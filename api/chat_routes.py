from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from models.schemas import QuestionRequest, QuestionResponse
from auth.dependencies import get_tenant_id, get_current_user
from services.retrieval_service_v2 import retrieval_service
from database.connection import get_db
from database.models import Conversations, Bots

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/ask", response_model=QuestionResponse)
async def ask_question(
    request: QuestionRequest,
    db: Session = Depends(get_db)
):
    """
    Ask a question, get an answer, and log the conversation.
    """
    tenant_id = request.tenant_id
    session_id = getattr(request, "session_id", None) or f"sess_{uuid.uuid4()}"
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
        # 1 Run your retrieval logic
        result = retrieval_service.answer_question(question_text, tenant_id)

        # 2 Find bot using tenant_id
        bot = db.query(Bots).filter(Bots.tenant_id == str(tenant_id)).first()
        if not bot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found for this tenant"
            )

        # 3 Find or create conversation
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

        # 4 Append user + bot messages to the JSON array
        conversation.messages.append({
            "role": "user",
            "text": question_text,
            "timestamp": datetime.utcnow().isoformat(),
        })
        conversation.messages.append({
            "role": "bot",
            "text": result["answer"],
            "timestamp": datetime.utcnow().isoformat(),
        })
        conversation.updatedAt = datetime.utcnow()
        bot.totalMessages += 2

        # 5 Commit all changes
        db.add(conversation)
        db.add(bot)
        db.commit()

        # 6 Return standard response (unchanged)
        return QuestionResponse(
            answer=result["answer"],
            sources=result["sources"],
            tenant_id=result["tenant_id"],
            suggestions=result["suggestions"]
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing question: {str(e)}"
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