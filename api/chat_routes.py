from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from models.schemas import QuestionRequest, QuestionResponse
from auth.dependencies import get_tenant_id, get_current_user
from services.retrieval_service import retrieval_service
from database.connection import get_db
from database.models import User

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/ask", response_model=QuestionResponse)
async def ask_question(
    request: QuestionRequest,
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ask a question and get an answer based on tenant-specific knowledge."""
    if not request.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty"
        )
    
    try:
        # Get answer using retrieval service
        result = retrieval_service.answer_question(request.question, tenant_id)
        print(f"Question: {request.question} | Answer: {result['answer']} | Sources: {result['sources']}")
        
        return QuestionResponse(
            answer=result["answer"],
            sources=result["sources"],
            tenant_id=result["tenant_id"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing question: {str(e)}"
        ) 

@router.post("/rebuild-index", status_code=status.HTTP_200_OK)
async def rebuild_search_index(
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Rebuild the search index."""
    try:
        success = retrieval_service.initialize_database(force_rebuild=True)
        
        if success:
            return {"message": "Search index rebuilt successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to rebuild search index"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error rebuilding index: {str(e)}"
        )