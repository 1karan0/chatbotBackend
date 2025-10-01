from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from models.schemas import QuestionRequest, QuestionResponse
from auth.dependencies import get_tenant_id, get_current_user
from services.retrieval_service_v2 import retrieval_service
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

@router.get("/embed-code", status_code=status.HTTP_200_OK)
async def get_embed_code(
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Get embed code for integrating the chatbot into a website."""
    embed_code = f"""<!-- AI Chatbot Widget -->
<script>
  (function() {{
    var chatbotConfig = {{
      tenantId: '{tenant_id}',
      apiEndpoint: 'YOUR_API_ENDPOINT_HERE',
      primaryColor: '#2563eb',
      position: 'bottom-right'
    }};

    // Load chatbot widget
    var script = document.createElement('script');
    script.src = 'YOUR_WIDGET_URL_HERE/chatbot-widget.js';
    script.async = true;
    document.body.appendChild(script);
  }})();
</script>
<!-- End AI Chatbot Widget -->"""

    return {
        "tenant_id": tenant_id,
        "embed_code": embed_code,
        "instructions": "Copy and paste this code before the closing </body> tag of your website"
    }

@router.get("/status", status_code=status.HTTP_200_OK)
async def get_chat_status(
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user)
):
    """Get chatbot status for the current tenant."""
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