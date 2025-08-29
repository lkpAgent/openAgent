"""Knowledge base endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...services.auth import AuthService
from ...services.knowledge_base import KnowledgeBaseService
from ...services.document import DocumentService
from ...utils.schemas import (
    KnowledgeBaseCreate,
    KnowledgeBaseResponse,
    KnowledgeBaseUpdate,
    DocumentResponse,
    DocumentUpload,
    SearchRequest,
    SearchResponse
)

router = APIRouter()


# Knowledge base management
@router.post("/", response_model=KnowledgeBaseResponse)
async def create_knowledge_base(
    kb_data: KnowledgeBaseCreate,
    current_user = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new knowledge base."""
    kb_service = KnowledgeBaseService(db)
    
    # Check if knowledge base with same name exists
    existing_kb = kb_service.get_knowledge_base_by_name(kb_data.name)
    if existing_kb:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Knowledge base with this name already exists"
        )
    
    kb = kb_service.create_knowledge_base(kb_data)
    return KnowledgeBaseResponse.from_orm(kb)


@router.get("/", response_model=List[KnowledgeBaseResponse])
async def list_knowledge_bases(
    skip: int = 0,
    limit: int = 50,
    current_user = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """List all knowledge bases."""
    kb_service = KnowledgeBaseService(db)
    knowledge_bases = kb_service.get_knowledge_bases(skip=skip, limit=limit)
    return [KnowledgeBaseResponse.from_orm(kb) for kb in knowledge_bases]


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_knowledge_base(
    kb_id: int,
    current_user = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific knowledge base."""
    kb_service = KnowledgeBaseService(db)
    kb = kb_service.get_knowledge_base(kb_id)
    
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found"
        )
    
    return KnowledgeBaseResponse.from_orm(kb)


@router.put("/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_knowledge_base(
    kb_id: int,
    kb_update: KnowledgeBaseUpdate,
    current_user = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Update a knowledge base."""
    kb_service = KnowledgeBaseService(db)
    kb = kb_service.get_knowledge_base(kb_id)
    
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found"
        )
    
    updated_kb = kb_service.update_knowledge_base(kb_id, kb_update)
    return KnowledgeBaseResponse.from_orm(updated_kb)


@router.delete("/{kb_id}")
async def delete_knowledge_base(
    kb_id: int,
    current_user = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a knowledge base."""
    kb_service = KnowledgeBaseService(db)
    kb = kb_service.get_knowledge_base(kb_id)
    
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found"
        )
    
    kb_service.delete_knowledge_base(kb_id)
    return {"message": "Knowledge base deleted successfully"}


# Document management
@router.post("/{kb_id}/documents", response_model=DocumentResponse)
async def upload_document(
    kb_id: int,
    file: UploadFile = File(...),
    current_user = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a document to knowledge base."""
    kb_service = KnowledgeBaseService(db)
    kb = kb_service.get_knowledge_base(kb_id)
    
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found"
        )
    
    document_service = DocumentService(db)
    document = await document_service.upload_document(kb_id, file)
    
    return DocumentResponse.from_orm(document)


@router.get("/{kb_id}/documents", response_model=List[DocumentResponse])
async def list_documents(
    kb_id: int,
    skip: int = 0,
    limit: int = 50,
    current_user = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """List documents in knowledge base."""
    kb_service = KnowledgeBaseService(db)
    kb = kb_service.get_knowledge_base(kb_id)
    
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found"
        )
    
    document_service = DocumentService(db)
    documents = document_service.get_documents(kb_id, skip=skip, limit=limit)
    
    return [DocumentResponse.from_orm(doc) for doc in documents]


@router.delete("/{kb_id}/documents/{doc_id}")
async def delete_document(
    kb_id: int,
    doc_id: int,
    current_user = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a document from knowledge base."""
    document_service = DocumentService(db)
    document = document_service.get_document(doc_id)
    
    if not document or document.knowledge_base_id != kb_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    document_service.delete_document(doc_id)
    return {"message": "Document deleted successfully"}


@router.post("/{kb_id}/documents/{doc_id}/process")
async def process_document(
    kb_id: int,
    doc_id: int,
    current_user = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Process a document (extract text and create embeddings)."""
    document_service = DocumentService(db)
    document = document_service.get_document(doc_id)
    
    if not document or document.knowledge_base_id != kb_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    await document_service.process_document(doc_id)
    return {"message": "Document processing started"}


# Search functionality
@router.post("/{kb_id}/search", response_model=SearchResponse)
async def search_knowledge_base(
    kb_id: int,
    search_request: SearchRequest,
    current_user = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Search in knowledge base."""
    kb_service = KnowledgeBaseService(db)
    kb = kb_service.get_knowledge_base(kb_id)
    
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found"
        )
    
    results = await kb_service.search(
        kb_id=kb_id,
        query=search_request.query,
        top_k=search_request.top_k,
        similarity_threshold=search_request.similarity_threshold
    )
    
    return SearchResponse(results=results)