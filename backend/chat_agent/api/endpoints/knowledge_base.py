"""Knowledge base API endpoints."""

import os
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...models.user import User
from ...models.knowledge_base import KnowledgeBase, Document
from ...services.knowledge_base import KnowledgeBaseService
from ...services.document import DocumentService
from ...services.auth import AuthService
from ...utils.schemas import (
    KnowledgeBaseCreate,
    KnowledgeBaseResponse,
    DocumentResponse,
    DocumentListResponse,
    DocumentUpload,
    DocumentProcessingStatus,
    DocumentChunksResponse,
    ErrorResponse
)
from ...utils.file_utils import FileUtils
from ...core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["knowledge-bases"])


@router.post("/", response_model=KnowledgeBaseResponse)
async def create_knowledge_base(
    kb_data: KnowledgeBaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Create a new knowledge base."""
    try:
        # Check if knowledge base with same name already exists for this user
        service = KnowledgeBaseService(db)
        existing_kb = service.get_knowledge_base_by_name(kb_data.name)
        if existing_kb:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Knowledge base with this name already exists"
            )
        
        # Create knowledge base
        kb = service.create_knowledge_base(kb_data)
        
        return KnowledgeBaseResponse(
            id=kb.id,
            created_at=kb.created_at,
            updated_at=kb.updated_at,
            name=kb.name,
            description=kb.description,
            embedding_model=kb.embedding_model,
            chunk_size=kb.chunk_size,
            chunk_overlap=kb.chunk_overlap,
            is_active=kb.is_active,
            vector_db_type=kb.vector_db_type,
            collection_name=kb.collection_name,
            document_count=0,
            active_document_count=0
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create knowledge base: {str(e)}"
        )


@router.get("/", response_model=List[KnowledgeBaseResponse])
async def list_knowledge_bases(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """List knowledge bases for current user."""
    try:
        service = KnowledgeBaseService(db)
        knowledge_bases = service.get_knowledge_bases(skip=skip, limit=limit)
        
        result = []
        for kb in knowledge_bases:
            # Count documents
            total_docs = db.query(Document).filter(
                Document.knowledge_base_id == kb.id
            ).count()
            
            active_docs = db.query(Document).filter(
                Document.knowledge_base_id == kb.id,
                Document.is_processed == True
            ).count()
            
            result.append(KnowledgeBaseResponse(
                id=kb.id,
                created_at=kb.created_at,
                updated_at=kb.updated_at,
                name=kb.name,
                description=kb.description,
                embedding_model=kb.embedding_model,
                chunk_size=kb.chunk_size,
                chunk_overlap=kb.chunk_overlap,
                is_active=kb.is_active,
                vector_db_type=kb.vector_db_type,
                collection_name=kb.collection_name,
                document_count=total_docs,
                active_document_count=active_docs
            ))
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list knowledge bases: {str(e)}"
        )


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(
    kb_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get knowledge base by ID."""
    try:
        service = KnowledgeBaseService(db)
        kb = service.get_knowledge_base(kb_id)
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge base not found"
            )
        
        # Count documents
        total_docs = db.query(Document).filter(
            Document.knowledge_base_id == kb.id
        ).count()
        
        active_docs = db.query(Document).filter(
            Document.knowledge_base_id == kb.id,
            Document.is_processed == True
        ).count()
        
        return KnowledgeBaseResponse(
            id=kb.id,
            created_at=kb.created_at,
            updated_at=kb.updated_at,
            name=kb.name,
            description=kb.description,
            embedding_model=kb.embedding_model,
            chunk_size=kb.chunk_size,
            chunk_overlap=kb.chunk_overlap,
            is_active=kb.is_active,
            vector_db_type=kb.vector_db_type,
            collection_name=kb.collection_name,
            document_count=total_docs,
            active_document_count=active_docs
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get knowledge base: {str(e)}"
        )


@router.put("/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(
    kb_id: int,
    kb_data: KnowledgeBaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Update knowledge base."""
    try:
        service = KnowledgeBaseService(db)
        kb = service.update_knowledge_base(kb_id, kb_data, current_user.id)
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge base not found"
            )
        
        # Count documents
        total_docs = db.query(Document).filter(
            Document.knowledge_base_id == kb.id
        ).count()
        
        active_docs = db.query(Document).filter(
            Document.knowledge_base_id == kb.id,
            Document.is_processed == True
        ).count()
        
        return KnowledgeBaseResponse(
            id=kb.id,
            created_at=kb.created_at,
            updated_at=kb.updated_at,
            name=kb.name,
            description=kb.description,
            embedding_model=kb.embedding_model,
            chunk_size=kb.chunk_size,
            chunk_overlap=kb.chunk_overlap,
            is_active=kb.is_active,
            vector_db_type=kb.vector_db_type,
            collection_name=kb.collection_name,
            document_count=total_docs,
            active_document_count=active_docs
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update knowledge base: {str(e)}"
        )


@router.delete("/{kb_id}")
async def delete_knowledge_base(
    kb_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Delete knowledge base."""
    try:
        service = KnowledgeBaseService(db)
        success = service.delete_knowledge_base(kb_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge base not found"
            )
        
        return {"message": "Knowledge base deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete knowledge base: {str(e)}"
        )


# Document management endpoints
@router.post("/{kb_id}/documents", response_model=DocumentResponse)
async def upload_document(
    kb_id: int,
    file: UploadFile = File(...),
    process_immediately: bool = Form(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Upload document to knowledge base."""
    try:
        # Verify knowledge base exists and user has access
        kb_service = KnowledgeBaseService(db)
        kb = kb_service.get_knowledge_base(kb_id)
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge base not found"
            )
        
        # Validate file
        if not FileUtils.validate_file_extension(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not supported. Allowed types: {', '.join(FileUtils.ALLOWED_EXTENSIONS)}"
            )
        
        # Check file size (50MB limit)
        max_size = 50 * 1024 * 1024  # 50MB
        if file.size and file.size > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size: {FileUtils.format_file_size(max_size)}"
            )
        
        # Upload document
        doc_service = DocumentService(db)
        document = await doc_service.upload_document(
            kb_id, file
        )
        
        # Process document immediately if requested
        if process_immediately:
            try:
                await doc_service.process_document(document.id, kb_id)
                # Refresh document to get updated status
                db.refresh(document)
            except Exception as e:
                # Log error but don't fail the upload
                logger.error(f"Failed to process document immediately: {e}")
        
        return DocumentResponse(
            id=document.id,
            created_at=document.created_at,
            updated_at=document.updated_at,
            knowledge_base_id=document.knowledge_base_id,
            filename=document.filename,
            original_filename=document.original_filename,
            file_path=document.file_path,
            file_type=document.file_type,
            file_size=document.file_size,
            mime_type=document.mime_type,
            is_processed=document.is_processed,
            processing_error=document.processing_error,
            chunk_count=document.chunk_count or 0,
            embedding_model=document.embedding_model,
            file_size_mb=round(document.file_size / (1024 * 1024), 2)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )


@router.get("/{kb_id}/documents", response_model=DocumentListResponse)
async def list_documents(
    kb_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """List documents in knowledge base."""
    try:
        # Verify knowledge base exists and user has access
        kb_service = KnowledgeBaseService(db)
        kb = kb_service.get_knowledge_base(kb_id)
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge base not found"
            )
        
        doc_service = DocumentService(db)
        documents, total = doc_service.list_documents(kb_id, skip, limit)
        
        doc_responses = []
        for doc in documents:
            doc_responses.append(DocumentResponse(
                id=doc.id,
                created_at=doc.created_at,
                updated_at=doc.updated_at,
                knowledge_base_id=doc.knowledge_base_id,
                filename=doc.filename,
                original_filename=doc.original_filename,
                file_path=doc.file_path,
                file_type=doc.file_type,
                file_size=doc.file_size,
                mime_type=doc.mime_type,
                is_processed=doc.is_processed,
                processing_error=doc.processing_error,
                chunk_count=doc.chunk_count or 0,
                embedding_model=doc.embedding_model,
                file_size_mb=round(doc.file_size / (1024 * 1024), 2)
            ))
        
        return DocumentListResponse(
            documents=doc_responses,
            total=total,
            page=skip // limit + 1,
            page_size=limit
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.get("/{kb_id}/documents/{doc_id}", response_model=DocumentResponse)
async def get_document(
    kb_id: int,
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get document by ID."""
    try:
        # Verify knowledge base exists and user has access
        kb_service = KnowledgeBaseService(db)
        kb = kb_service.get_knowledge_base(kb_id)
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge base not found"
            )
        
        doc_service = DocumentService(db)
        document = doc_service.get_document(doc_id, kb_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        return DocumentResponse(
            id=document.id,
            created_at=document.created_at,
            updated_at=document.updated_at,
            knowledge_base_id=document.knowledge_base_id,
            filename=document.filename,
            original_filename=document.original_filename,
            file_path=document.file_path,
            file_type=document.file_type,
            file_size=document.file_size,
            mime_type=document.mime_type,
            is_processed=document.is_processed,
            processing_error=document.processing_error,
            chunk_count=document.chunk_count or 0,
            embedding_model=document.embedding_model,
            file_size_mb=round(document.file_size / (1024 * 1024), 2)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document: {str(e)}"
        )


@router.delete("/{kb_id}/documents/{doc_id}")
async def delete_document(
    kb_id: int,
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Delete document from knowledge base."""
    try:
        # Verify knowledge base exists and user has access
        kb_service = KnowledgeBaseService(db)
        kb = kb_service.get_knowledge_base(kb_id)
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge base not found"
            )
        
        doc_service = DocumentService(db)
        success = doc_service.delete_document(doc_id, kb_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        return {"message": "Document deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.post("/{kb_id}/documents/{doc_id}/process", response_model=DocumentProcessingStatus)
async def process_document(
    kb_id: int,
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Process document for vector search."""
    try:
        # Verify knowledge base exists and user has access
        kb_service = KnowledgeBaseService(db)
        kb = kb_service.get_knowledge_base(kb_id)
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge base not found"
            )
        
        # Check if document exists
        doc_service = DocumentService(db)
        document = doc_service.get_document(doc_id, kb_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Process the document
        result = await doc_service.process_document(doc_id, kb_id)
        
        return DocumentProcessingStatus(
            document_id=doc_id,
            status=result["status"],
            progress=result.get("progress", 0.0),
            error_message=result.get("error_message"),
            chunks_created=result.get("chunks_created", 0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}"
        )


@router.get("/{kb_id}/documents/{doc_id}/status", response_model=DocumentProcessingStatus)
async def get_document_processing_status(
    kb_id: int,
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Get document processing status."""
    try:
        # Verify knowledge base exists and user has access
        kb_service = KnowledgeBaseService(db)
        kb = kb_service.get_knowledge_base(kb_id)
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge base not found"
            )
        
        doc_service = DocumentService(db)
        document = doc_service.get_document(doc_id, kb_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Determine status
        if document.processing_error:
            status_str = "failed"
            progress = 0.0
        elif document.is_processed:
            status_str = "completed"
            progress = 100.0
        else:
            status_str = "pending"
            progress = 0.0
        
        return DocumentProcessingStatus(
            document_id=document.id,
            status=status_str,
            progress=progress,
            error_message=document.processing_error,
            chunks_created=document.chunk_count or 0
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document status: {str(e)}"
        )


@router.get("/{kb_id}/search")
async def search_knowledge_base(
    kb_id: int,
    query: str,
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """Search documents in a knowledge base."""
    try:
        # Verify knowledge base exists and user has access
        kb_service = KnowledgeBaseService(db)
        kb = kb_service.get_knowledge_base(kb_id)
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge base not found"
            )
        
        # Perform search
        doc_service = DocumentService(db)
        results = doc_service.search_documents(kb_id, query, limit)
        
        return {
            "knowledge_base_id": kb_id,
            "query": query,
            "results": results,
            "total_results": len(results)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search knowledge base: {str(e)}"
        )


@router.get("/{kb_id}/documents/{doc_id}/chunks", response_model=DocumentChunksResponse)
async def get_document_chunks(
    kb_id: int,
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(AuthService.get_current_user)
):
    """
    Get document chunks (segments) for a specific document.
    
    Args:
        kb_id: Knowledge base ID
        doc_id: Document ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        DocumentChunksResponse: Document chunks with metadata
    """
    try:
        # Verify knowledge base exists and user has access
        kb_service = KnowledgeBaseService(db)
        knowledge_base = kb_service.get_knowledge_base(kb_id)
        if not knowledge_base:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge base not found"
            )
        
        # Verify document exists in the knowledge base
        doc_service = DocumentService(db)
        document = doc_service.get_document(doc_id, kb_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Get document chunks
        chunks = doc_service.get_document_chunks(doc_id)
        
        return DocumentChunksResponse(
            document_id=doc_id,
            document_name=document.filename,
            total_chunks=len(chunks),
            chunks=chunks
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document chunks: {str(e)}"
        )