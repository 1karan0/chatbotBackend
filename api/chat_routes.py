from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, attributes
from datetime import datetime
import uuid

from models.schemas import (
    QuestionRequest,
    QuestionResponse,
    SourceImage,
    ConversationResponse,
    ConversationMessage,
    ConversationListResponse,
    ConversationListItem,
)
from auth.dependencies import get_tenant_id, get_current_user
from services.retrieval_service_v2 import retrieval_service
from database.connection import get_db
from database.models import Conversations, Bots, KnowledgeSources

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/session", status_code=status.HTTP_200_OK)
async def create_chat_session(
    tenant_id: str = Query(..., description="Tenant ID for the chatbot"),
    db: Session = Depends(get_db)
):
    """
    Get a new session_id for a chat. Call this once when the user opens a new chat,
    then use the returned session_id for every POST /chat/ask and GET /chat/conversation.

    Flow:
    1. User opens new chat → GET /chat/session?tenant_id=... → store the session_id (e.g. in state).
    2. Every message → POST /chat/ask with body: { question, tenant_id, session_id: <stored> }.
    3. Load history → GET /chat/conversation?tenant_id=...&session_id=<stored>.
    """
    bot = db.query(Bots).filter(Bots.tenant_id == str(tenant_id)).first()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found for this tenant"
        )
    session_id = str(uuid.uuid4())
    return {"session_id": session_id, "tenant_id": tenant_id}


@router.post("/ask", response_model=QuestionResponse)
async def ask_question(
    request: QuestionRequest,
    db: Session = Depends(get_db)
):
    """
    Ask a question, get an answer, and log the conversation.
    """
    tenant_id = request.tenant_id
    # New conversation: always generate a new session_id. Otherwise reuse the one sent by the client.
    if getattr(request, "new_conversation", False):
        session_id = str(uuid.uuid4())
    else:
        session_id = (request.session_id and request.session_id.strip()) or str(uuid.uuid4())
    user_id = getattr(request, "user_id", None)
    question_text = request.question.strip()

    if not question_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty"
        )
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="tenant_id is required"
        )

    try:
        # 1 Detect if user is asking for images so the model can acknowledge them in the answer
        user_wants_images = retrieval_service.user_asks_for_image(question_text)

        # 2 Run retrieval and generate answer (pass image hint so model doesn't say "I don't have that information")
        result = retrieval_service.answer_question(question_text, tenant_id, user_asking_for_images=user_wants_images)

        # 3 Include images only when the user explicitly asks for them (e.g. "show image", "photo")
        images: list[SourceImage] = []
        if user_wants_images and result.get("sources"):
            raw_images: list[dict] = []
            source_rows = (
                db.query(KnowledgeSources)
                .filter(
                    KnowledgeSources.tenant_id == tenant_id,
                    KnowledgeSources.source_url.in_(result["sources"]),
                    KnowledgeSources.source_metadata.isnot(None),
                )
                .all()
            )
            seen_urls: set[str] = set()
            for row in source_rows:
                meta = row.source_metadata or {}
                for img in meta.get("images") or []:
                    if isinstance(img, dict) and img.get("url") and img["url"] not in seen_urls:
                        seen_urls.add(img["url"])
                        raw_images.append({
                            "url": img["url"],
                            "alt": img.get("alt") or "",
                            "title": img.get("title"),
                        })
            filtered = retrieval_service.filter_relevant_images(
                question_text, result["answer"], raw_images
            )
            images = [
                SourceImage(url=img["url"], alt=img.get("alt") or "", title=img.get("title"))
                for img in filtered
            ]
            # If we have images but the model still said it doesn't have the info, fix the answer
            if images and result.get("answer"):
                answer_lower = result["answer"].lower()
                if "don't have" in answer_lower or "do not have" in answer_lower or "don't have that information" in answer_lower:
                    result = {**result, "answer": "Here are the images from the relevant sources."}

        # 4 Find bot using tenant_id
        bot = db.query(Bots).filter(Bots.tenant_id == str(tenant_id)).first()
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found for this tenant"
            )

        # 5 Find or create conversation
        conversation = (
            db.query(Conversations)
            .filter(Conversations.sessionId == session_id, Conversations.botId == bot.id)
            .first()
        )

        if not conversation:
            conversation = Conversations(
                id=str(uuid.uuid4()),
                sessionId=session_id,
                userId=user_id,
                botId=bot.id,
                messages=[],
                createdAt=datetime.utcnow(),
                updatedAt=datetime.utcnow(),
            )
            db.add(conversation)
            bot.totalConversations += 1

        # 6 Append user + bot messages (assign new list so SQLAlchemy persists JSONB changes)
        msg_list = list(conversation.messages) if conversation.messages else []
        msg_list.append({
            "role": "user",
            "text": question_text,
            "timestamp": datetime.utcnow().isoformat(),
        })
        bot_msg: dict = {
            "role": "bot",
            "text": result["answer"],
            "timestamp": datetime.utcnow().isoformat(),
        }
        if images:
            bot_msg["images"] = [{"url": img.url, "alt": img.alt or "", "title": img.title} for img in images]
        msg_list.append(bot_msg)
        conversation.messages = msg_list
        conversation.updatedAt = datetime.utcnow()
        bot.totalMessages += 2
        attributes.flag_modified(conversation, "messages")

        # 7 Commit all changes
        db.add(conversation)
        db.add(bot)
        db.commit()

        # 8 Return response including images and session_id so frontend can load conversation
        return QuestionResponse(
            answer=result["answer"],
            sources=result["sources"],
            tenant_id=result["tenant_id"],
            session_id=session_id,
            suggestions=result["suggestions"],
            images=images,
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing question: {str(e)}"
        )


@router.get("/conversations", response_model=ConversationListResponse, status_code=status.HTTP_200_OK)
async def list_conversations(
    tenant_id: str = Query(..., description="Tenant ID for the chatbot"),
    db: Session = Depends(get_db)
):
    """
    List all conversations for the tenant. Use this to show the total conversations in the frontend
    (e.g. sidebar). Each item includes session_id; use GET /chat/conversation?session_id=... to load
    that conversation's messages.
    """
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="tenant_id is required"
        )
    bot = db.query(Bots).filter(Bots.tenant_id == str(tenant_id)).first()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found for this tenant"
        )
    rows = (
        db.query(Conversations)
        .filter(Conversations.botId == bot.id)
        .order_by(Conversations.updatedAt.desc())
        .all()
    )
    items = []
    for conv in rows:
        messages = conv.messages if isinstance(conv.messages, list) else []
        preview = None
        if messages:
            last = messages[-1]
            if isinstance(last, dict) and last.get("text"):
                text = str(last["text"]).strip()
                preview = text[:80] + "..." if len(text) > 80 else text
                if "images" in last:
                    preview += " (images)"
        items.append(ConversationListItem(
            conversation_id=conv.id,
            session_id=conv.sessionId,
            tenant_id=tenant_id,
            messages=messages,
            preview=preview,
            created_at=conv.createdAt,
            updated_at=conv.updatedAt,
        ))
    return ConversationListResponse(conversations=items, total=len(items))


@router.get("/conversation", response_model=ConversationResponse, status_code=status.HTTP_200_OK)
async def get_conversation(
    tenant_id: str = Query(..., description="Tenant ID for the chatbot"),
    session_id: str = Query(..., description="Session ID of the chat (e.g. from your frontend)"),
    db: Session = Depends(get_db)
):
    """
    Get the conversation history (user + bot messages) for a given tenant and session.
    Use this to display the chat history in your frontend. If no conversation exists yet, returns empty messages.
    """
    if not tenant_id or not session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="tenant_id and session_id are required"
        )
    bot = db.query(Bots).filter(Bots.tenant_id == str(tenant_id)).first()
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found for this tenant"
        )
    conversation = (
        db.query(Conversations)
        .filter(Conversations.sessionId == session_id, Conversations.botId == bot.id)
        .first()
    )
    if not conversation:
        return ConversationResponse(
            conversation_id=None,
            session_id=session_id,
            tenant_id=tenant_id,
            messages=[],
            created_at=None,
            updated_at=None,
        )
    # Normalize messages: ensure each has role, text, timestamp; include images when present
    messages = []
    for m in conversation.messages or []:
        if isinstance(m, dict) and m.get("text") is not None:
            raw_images = m.get("images") or []
            msg_images = [
                SourceImage(url=img["url"], alt=img.get("alt") or "", title=img.get("title"))
                for img in raw_images
                if isinstance(img, dict) and img.get("url")
            ]
            messages.append(ConversationMessage(
                role=m.get("role", "user"),
                text=m.get("text", ""),
                timestamp=m.get("timestamp"),
                images=msg_images,
            ))
    return ConversationResponse(
        conversation_id=conversation.id,
        session_id=conversation.sessionId,
        tenant_id=tenant_id,
        messages=messages,
        created_at=conversation.createdAt,
        updated_at=conversation.updatedAt,
    )


@router.get("/status", status_code=status.HTTP_200_OK)
async def get_chat_status(
    tenant_id: str = Query(..., description="Tenant ID for the chatbot"),
    db: Session = Depends(get_db)
):
    """Get chatbot status for the given tenant_id."""
    try:
        doc_count = retrieval_service.get_tenant_document_count(tenant_id)
        return {
            "tenant_id": tenant_id,
            "document_count": doc_count,
            "status": "ready" if doc_count > 0 else "no_knowledge",
            "message": f"Chatbot has {doc_count} document chunks indexed"
            if doc_count > 0
            else "No knowledge sources added yet",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting status: {str(e)}",
        )