from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import asyncio

from models.schemas import KnowledgeSourceCreate, KnowledgeSourceInfo, ProcessingStatus
from auth.dependencies import get_tenant_id, get_current_user
from database.connection import get_db
from database.models import User, KnowledgeSource
from services.web_scraper import web_scraper
from services.document_processor import document_processor
from services.retrieval_service_v2 import retrieval_service

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

@router.post("/sources/url", response_model=ProcessingStatus, status_code=status.HTTP_201_CREATED)
async def add_url_source(
    url: str = Form(...),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a URL as a knowledge source and process it."""
    if not web_scraper.validate_url(url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid URL format"
        )

    source = KnowledgeSource(
        tenant_id=tenant_id,
        source_type="url",
        source_url=url,
        status="processing"
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    try:
        result = await web_scraper.scrape_url(url)

        if not result['success']:
            source.status = "failed"
            source.error_message = result['error']
            db.commit()
            return ProcessingStatus(
                source_id=source.source_id,
                status="failed",
                message="Failed to scrape URL",
                error_message=result['error']
            )

        source.source_content = result['content']
        source.source_metadata = {'title': result.get('title', url)}

        await retrieval_service.add_documents_to_index(
            text=result['content'],
            source=url,
            tenant_id=tenant_id
        )

        source.status = "completed"
        db.commit()

        return ProcessingStatus(
            source_id=source.source_id,
            status="completed",
            message="URL processed successfully"
        )

    except Exception as e:
        source.status = "failed"
        source.error_message = str(e)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing URL: {str(e)}"
        )

@router.post("/sources/text", response_model=ProcessingStatus, status_code=status.HTTP_201_CREATED)
async def add_text_source(
    text: str = Form(...),
    title: Optional[str] = Form("Text Document"),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add text content as a knowledge source."""
    if not text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text content cannot be empty"
        )

    source = KnowledgeSource(
        tenant_id=tenant_id,
        source_type="text",
        source_content=text,
        status="processing",
        source_metadata={'title': title}
    )
    db.add(source)
    db.commit()
    db.refresh(source)

    try:
        await retrieval_service.add_documents_to_index(
            text=text,
            source=title,
            tenant_id=tenant_id
        )

        source.status = "completed"
        db.commit()

        return ProcessingStatus(
            source_id=source.source_id,
            status="completed",
            message="Text processed successfully"
        )

    except Exception as e:
        source.status = "failed"
        source.error_message = str(e)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing text: {str(e)}"
        )

@router.post("/sources/file", response_model=ProcessingStatus, status_code=status.HTTP_201_CREATED)
async def add_file_source(
    file: UploadFile = File(...),
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a file as a knowledge source."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File name is required"
        )

    allowed_extensions = ['.txt', '.md', '.csv', '.pdf', '.docx']
    if not any(file.filename.endswith(ext) for ext in allowed_extensions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not supported. Allowed: {', '.join(allowed_extensions)}"
        )

    try:
        file_content = await file.read()
        text_content = document_processor.extract_file_content(file_content, file.filename)

        if not text_content.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract text from file"
            )

        source = KnowledgeSource(
            tenant_id=tenant_id,
            source_type="file",
            file_name=file.filename,
            file_content=text_content,
            status="processing"
        )
        db.add(source)
        db.commit()
        db.refresh(source)

        await retrieval_service.add_documents_to_index(
            text=text_content,
            source=file.filename,
            tenant_id=tenant_id
        )

        source.status = "completed"
        db.commit()

        return ProcessingStatus(
            source_id=source.source_id,
            status="completed",
            message="File processed successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        if 'source' in locals():
            source.status = "failed"
            source.error_message = str(e)
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}"
        )

@router.get("/sources", response_model=List[KnowledgeSourceInfo])
async def list_knowledge_sources(
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all knowledge sources for the current tenant."""
    sources = db.query(KnowledgeSource).filter(
        KnowledgeSource.tenant_id == tenant_id
    ).order_by(KnowledgeSource.created_at.desc()).all()

    return sources

@router.delete("/sources/{source_id}", status_code=status.HTTP_200_OK)
async def delete_knowledge_source(
    source_id: str,
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a knowledge source."""
    source = db.query(KnowledgeSource).filter(
        KnowledgeSource.source_id == source_id,
        KnowledgeSource.tenant_id == tenant_id
    ).first()

    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge source not found"
        )

    db.delete(source)
    db.commit()

    return {"message": "Knowledge source deleted successfully"}

@router.post("/rebuild-index", status_code=status.HTTP_200_OK)
async def rebuild_tenant_index(
    tenant_id: str = Depends(get_tenant_id),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Rebuild the search index for the current tenant."""
    try:
        sources = db.query(KnowledgeSource).filter(
            KnowledgeSource.tenant_id == tenant_id,
            KnowledgeSource.status == "completed"
        ).all()

        if not sources:
            return {"message": "No completed sources to index"}

        retrieval_service.clear_tenant_documents(tenant_id)

        for source in sources:
            content = source.source_content or source.file_content
            if content:
                source_name = source.source_url or source.file_name or f"source_{source.source_id}"
                await retrieval_service.add_documents_to_index(
                    text=content,
                    source=source_name,
                    tenant_id=tenant_id
                )

        return {
            "message": f"Index rebuilt successfully for tenant {tenant_id}",
            "sources_processed": len(sources)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error rebuilding index: {str(e)}"
        )
