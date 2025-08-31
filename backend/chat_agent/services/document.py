"""Document service."""

import os
import logging
import hashlib
import mimetypes
from pathlib import Path
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import UploadFile

from ..models.knowledge_base import Document, KnowledgeBase
from ..core.config import get_settings
from ..utils.file_utils import FileUtils
from .storage import storage_service
from .document_processor import document_processor
from ..utils.schemas import DocumentChunk

logger = logging.getLogger(__name__)
settings = get_settings()


class DocumentService:
    """Document service for managing documents in knowledge bases."""
    
    def __init__(self, db: Session):
        self.db = db
        self.file_utils = FileUtils()
    
    async def upload_document(self, kb_id: int, file: UploadFile) -> Document:
        """Upload a document to knowledge base."""
        try:
            # Validate knowledge base exists
            kb = self.db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
            if not kb:
                raise ValueError(f"Knowledge base {kb_id} not found")
            
            # Validate file
            if not file.filename:
                raise ValueError("No filename provided")
            
            # Validate file extension
            file_extension = Path(file.filename).suffix.lower()
            if file_extension not in settings.file.allowed_extensions:
                raise ValueError(f"File type {file_extension} not allowed")
            
            # Upload file using storage service
            storage_info = await storage_service.upload_file(file, kb_id)
            
            # Create document record
            document = Document(
                knowledge_base_id=kb_id,
                filename=os.path.basename(storage_info["file_path"]),
                original_filename=file.filename,
                file_path=storage_info.get("full_path", storage_info["file_path"]),  # Use absolute path if available
                file_size=storage_info["size"],
                file_type=file_extension,
                mime_type=storage_info["mime_type"],
                is_processed=False
            )
            
            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)
            
            logger.info(f"Uploaded document: {file.filename} to KB {kb_id} (Doc ID: {document.id})")
            return document
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to upload document: {e}")
            raise
    
    def get_document(self, doc_id: int, kb_id: int = None) -> Optional[Document]:
        """Get document by ID, optionally filtered by knowledge base."""
        query = self.db.query(Document).filter(Document.id == doc_id)
        if kb_id is not None:
            query = query.filter(Document.knowledge_base_id == kb_id)
        return query.first()
    
    def get_documents(self, kb_id: int, skip: int = 0, limit: int = 50) -> List[Document]:
        """Get documents in knowledge base."""
        return (
            self.db.query(Document)
            .filter(Document.knowledge_base_id == kb_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def list_documents(self, kb_id: int, skip: int = 0, limit: int = 50) -> tuple[List[Document], int]:
        """List documents in knowledge base with total count."""
        # Get total count
        total = self.db.query(Document).filter(Document.knowledge_base_id == kb_id).count()
        
        # Get documents with pagination
        documents = (
            self.db.query(Document)
            .filter(Document.knowledge_base_id == kb_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        return documents, total
    
    async def delete_document(self, doc_id: int, kb_id: int = None) -> bool:
        """Delete document."""
        try:
            document = self.get_document(doc_id, kb_id)
            if not document:
                return False
            
            # Delete file from storage
            try:
                await storage_service.delete_file(document.file_path)
                logger.info(f"Deleted file: {document.file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete file {document.file_path}: {e}")
            
            # TODO: Remove from vector database
            # This should be implemented when vector database service is ready
            
            # Delete database record
            self.db.delete(document)
            self.db.commit()
            
            logger.info(f"Deleted document: {document.filename} (ID: {doc_id})")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete document {doc_id}: {e}")
            raise
    
    async def process_document(self, doc_id: int, kb_id: int = None) -> Dict[str, Any]:
        """Process document (extract text and create embeddings)."""
        try:
            document = self.get_document(doc_id, kb_id)
            if not document:
                raise ValueError(f"Document {doc_id} not found")
            
            if document.is_processed:
                logger.info(f"Document {doc_id} already processed")
                return {
                    "document_id": doc_id,
                    "status": "already_processed",
                    "message": "文档已处理"
                }
            
            # 更新文档状态为处理中
            document.processing_error = None
            self.db.commit()
            
            # 调用文档处理器进行处理
            result = document_processor.process_document(
                document_id=doc_id,
                file_path=document.file_path,
                knowledge_base_id=document.knowledge_base_id
            )
            
            # 如果处理成功，更新文档状态
            if result["status"] == "success":
                document.is_processed = True
                document.chunk_count = result.get("chunks_count", 0)
                self.db.commit()
                self.db.refresh(document)
                logger.info(f"Processed document: {document.filename} (ID: {doc_id})")
            
            return result
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to process document {doc_id}: {e}")
            
            # Update document with error
            try:
                document = self.get_document(doc_id)
                if document:
                    document.processing_error = str(e)
                    self.db.commit()
            except Exception as db_error:
                logger.error(f"Failed to update document error status: {db_error}")
            
            return {
                "document_id": doc_id,
                "status": "failed",
                "error": str(e),
                "message": "文档处理失败"
            }
    
    async def _extract_text(self, document: Document) -> str:
        """Extract text content from document."""
        try:
            if document.is_text_file:
                # Read text files directly
                with open(document.file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            elif document.is_pdf_file:
                # TODO: Implement PDF text extraction using PyPDF2 or similar
                # For now, return placeholder
                return f"PDF content from {document.original_filename}"
            
            elif document.is_office_file:
                # TODO: Implement Office file text extraction using python-docx, openpyxl, etc.
                # For now, return placeholder
                return f"Office document content from {document.original_filename}"
            
            else:
                raise ValueError(f"Unsupported file type: {document.file_type}")
                
        except Exception as e:
            logger.error(f"Failed to extract text from {document.file_path}: {e}")
            raise
    
    def update_document_status(self, doc_id: int, is_processed: bool, error: Optional[str] = None) -> bool:
        """Update document processing status."""
        try:
            document = self.get_document(doc_id)
            if not document:
                return False
            
            document.is_processed = is_processed
            document.processing_error = error
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update document status {doc_id}: {e}")
            raise
    
    def search_documents(self, kb_id: int, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search documents in knowledge base using vector similarity."""
        try:
            # 使用文档处理器进行相似性搜索
            results = document_processor.search_similar_documents(kb_id, query, limit)
            return results
        except Exception as e:
            logger.error(f"Failed to search documents in KB {kb_id}: {e}")
            return []
    
    def get_document_stats(self, kb_id: int) -> Dict[str, Any]:
        """Get document statistics for knowledge base."""
        documents = self.get_documents(kb_id, limit=1000)  # Get all documents
        
        total_count = len(documents)
        processed_count = len([doc for doc in documents if doc.is_processed])
        total_size = sum(doc.file_size for doc in documents)
        
        file_types = {}
        for doc in documents:
            file_type = doc.file_type
            file_types[file_type] = file_types.get(file_type, 0) + 1
        
        return {
            "total_documents": total_count,
            "processed_documents": processed_count,
            "pending_documents": total_count - processed_count,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_types": file_types
        }
    
    def get_document_chunks(self, doc_id: int) -> List[DocumentChunk]:
        """Get document chunks for a specific document."""
        try:
            # Get document to find knowledge base ID
            document = self.db.query(Document).filter(Document.id == doc_id).first()
            if not document:
                logger.error(f"Document {doc_id} not found")
                return []
            
            # Get chunks from document processor
            chunks_data = document_processor.get_document_chunks(document.knowledge_base_id, doc_id)
            
            # Convert to DocumentChunk objects
            chunks = []
            for chunk_data in chunks_data:
                chunk = DocumentChunk(
                    id=chunk_data["id"],
                    content=chunk_data["content"],
                    metadata=chunk_data["metadata"],
                    page_number=chunk_data.get("page_number"),
                    chunk_index=chunk_data["chunk_index"],
                    start_char=chunk_data.get("start_char"),
                    end_char=chunk_data.get("end_char")
                )
                chunks.append(chunk)
            
            logger.info(f"Retrieved {len(chunks)} chunks for document {doc_id}")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to get chunks for document {doc_id}: {e}")
            return []