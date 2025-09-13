"""Knowledge base models."""

from sqlalchemy import Column, String, Integer, ForeignKey, Text, Boolean, JSON, Float
from sqlalchemy.orm import relationship

from ..db.base import BaseModel


class KnowledgeBase(BaseModel):
    """Knowledge base model."""
    
    __tablename__ = "knowledge_bases"
    
    name = Column(String(100), unique=False, index=True, nullable=False)
    description = Column(Text, nullable=True)
    embedding_model = Column(String(100), nullable=False, default="sentence-transformers/all-MiniLM-L6-v2")
    chunk_size = Column(Integer, nullable=False, default=1000)
    chunk_overlap = Column(Integer, nullable=False, default=200)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Vector database settings
    vector_db_type = Column(String(50), nullable=False, default="chroma")
    collection_name = Column(String(100), nullable=True)  # For vector DB collection
    
    # Relationships removed to eliminate foreign key constraints
    
    def __repr__(self):
        return f"<KnowledgeBase(id={self.id}, name='{self.name}')>"
    
    @property
    def document_count(self):
        """Get the number of documents in this knowledge base."""
        return len(self.documents)
    
    @property
    def active_document_count(self):
        """Get the number of active documents in this knowledge base."""
        return len([doc for doc in self.documents if doc.is_processed])


class Document(BaseModel):
    """Document model."""
    
    __tablename__ = "documents"
    
    knowledge_base_id = Column(Integer, nullable=False)  # Removed ForeignKey("knowledge_bases.id")
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    file_type = Column(String(50), nullable=False)  # .pdf, .txt, .docx, etc.
    mime_type = Column(String(100), nullable=True)
    
    # Processing status
    is_processed = Column(Boolean, default=False, nullable=False)
    processing_error = Column(Text, nullable=True)
    
    # Content and metadata
    content = Column(Text, nullable=True)  # Extracted text content
    doc_metadata = Column(JSON, nullable=True)  # Additional metadata
    
    # Chunking information
    chunk_count = Column(Integer, default=0, nullable=False)
    
    # Embedding information
    embedding_model = Column(String(100), nullable=True)
    vector_ids = Column(JSON, nullable=True)  # Store vector database IDs for chunks
    
    # Relationships removed to eliminate foreign key constraints
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', kb_id={self.knowledge_base_id})>"
    
    @property
    def file_size_mb(self):
        """Get file size in MB."""
        return round(self.file_size / (1024 * 1024), 2)
    
    @property
    def is_text_file(self):
        """Check if document is a text file."""
        return self.file_type.lower() in ['.txt', '.md', '.csv']
    
    @property
    def is_pdf_file(self):
        """Check if document is a PDF file."""
        return self.file_type.lower() == '.pdf'
    
    @property
    def is_office_file(self):
        """Check if document is an Office file."""
        return self.file_type.lower() in ['.docx', '.xlsx', '.pptx']