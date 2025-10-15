from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi import Query

from models.schemas import QuestionRequest, QuestionResponse
from auth.dependencies import get_tenant_id, get_current_user
from services.retrieval_service_v2 import retrieval_service
from database.connection import get_db
from database.models import User

router = APIRouter(prefix="/chat", tags=["chat"])

# ...existing code...

@router.post("/ask", response_model=QuestionResponse)
async def ask_question(
    request: QuestionRequest,
    db: Session = Depends(get_db)
):
    """Ask a question and get an answer based on tenant-specific knowledge."""
    tenant_id = request.tenant_id  # Add tenant_id to your QuestionRequest schema

    if not request.question.strip():
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
        result = retrieval_service.answer_question(request.question, tenant_id)
        return QuestionResponse(
            answer=result["answer"],
            sources=result["sources"],
            tenant_id=result["tenant_id"],
            suggestions=result["suggestions"]
        )
    except Exception as e:
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
            "message": f"Chatbot has {doc_count} document chunks indexed" if doc_count > 0 else "No knowledge sources added yet"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting status: {str(e)}"
        )