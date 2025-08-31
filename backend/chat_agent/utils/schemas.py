"""Pydantic schemas for API requests and responses."""

from typing import Optional, List, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class MessageRole(str, Enum):
    """Message role enumeration."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageType(str, Enum):
    """Message type enumeration."""
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    AUDIO = "audio"


# Base schemas
class BaseResponse(BaseModel):
    """Base response schema."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# User schemas
class UserBase(BaseModel):
    """User base schema."""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., max_length=100)
    full_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    """User creation schema."""
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    """User update schema."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[str] = Field(None, max_length=100)
    full_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    password: Optional[str] = Field(None, min_length=6)
    is_active: Optional[bool] = None


class UserResponse(BaseResponse, UserBase):
    """User response schema."""
    is_active: bool
    is_superuser: bool


# Authentication schemas
class LoginRequest(BaseModel):
    """Login request schema."""
    email: str = Field(..., max_length=100)
    password: str = Field(..., min_length=6)


class Token(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str
    expires_in: int


# Conversation schemas
class ConversationBase(BaseModel):
    """Conversation base schema."""
    title: str = Field(..., min_length=1, max_length=200)
    system_prompt: Optional[str] = None
    model_name: str = Field(default="gpt-3.5-turbo", max_length=100)
    temperature: str = Field(default="0.7", max_length=10)
    max_tokens: int = Field(default=2048, ge=1, le=8192)
    knowledge_base_id: Optional[int] = None


class ConversationCreate(ConversationBase):
    """Conversation creation schema."""
    pass


class ConversationUpdate(BaseModel):
    """Conversation update schema."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    system_prompt: Optional[str] = None
    model_name: Optional[str] = Field(None, max_length=100)
    temperature: Optional[str] = Field(None, max_length=10)
    max_tokens: Optional[int] = Field(None, ge=1, le=8192)
    is_archived: Optional[bool] = None


class ConversationResponse(BaseResponse, ConversationBase):
    """Conversation response schema."""
    user_id: int
    is_archived: bool
    message_count: int = 0
    last_message_at: Optional[datetime] = None


# Message schemas
class MessageBase(BaseModel):
    """Message base schema."""
    content: str = Field(..., min_length=1)
    role: MessageRole
    message_type: MessageType = MessageType.TEXT
    metadata: Optional[Dict[str, Any]] = Field(None, alias="message_metadata")


class MessageCreate(MessageBase):
    """Message creation schema."""
    conversation_id: int


class MessageResponse(BaseResponse, MessageBase):
    """Message response schema."""
    conversation_id: int
    context_documents: Optional[List[Dict[str, Any]]] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    
    class Config:
        from_attributes = True
        populate_by_name = True


# Chat schemas
class ChatRequest(BaseModel):
    """Chat request schema."""
    message: str = Field(..., min_length=1, max_length=10000)
    stream: bool = Field(default=False)
    use_knowledge_base: bool = Field(default=False)
    knowledge_base_id: Optional[int] = Field(None, description="Knowledge base ID for RAG mode")
    use_agent: bool = Field(default=True, description="Enable agent mode with tool calling capabilities")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=8192)


class ChatResponse(BaseModel):
    """Chat response schema."""
    user_message: MessageResponse
    assistant_message: MessageResponse
    total_tokens: Optional[int] = None
    model_used: str


class StreamChunk(BaseModel):
    """Stream chunk schema."""
    content: str
    role: MessageRole = MessageRole.ASSISTANT
    finish_reason: Optional[str] = None
    tokens_used: Optional[int] = None


# Knowledge Base schemas
class KnowledgeBaseBase(BaseModel):
    """Knowledge base base schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    chunk_size: int = Field(default=1000, ge=100, le=5000)
    chunk_overlap: int = Field(default=200, ge=0, le=1000)


class KnowledgeBaseCreate(KnowledgeBaseBase):
    """Knowledge base creation schema."""
    pass


class KnowledgeBaseUpdate(BaseModel):
    """Knowledge base update schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    embedding_model: Optional[str] = None
    chunk_size: Optional[int] = Field(None, ge=100, le=5000)
    chunk_overlap: Optional[int] = Field(None, ge=0, le=1000)
    is_active: Optional[bool] = None


class KnowledgeBaseResponse(BaseResponse, KnowledgeBaseBase):
    """Knowledge base response schema."""
    is_active: bool
    vector_db_type: str
    collection_name: Optional[str]
    document_count: int = 0
    active_document_count: int = 0


# Document schemas
class DocumentBase(BaseModel):
    """Document base schema."""
    filename: str
    original_filename: str
    file_type: str
    file_size: int


class DocumentUpload(BaseModel):
    """Document upload schema."""
    knowledge_base_id: int
    process_immediately: bool = Field(default=True)


class DocumentResponse(BaseResponse, DocumentBase):
    """Document response schema."""
    knowledge_base_id: int
    file_path: str
    mime_type: Optional[str]
    is_processed: bool
    processing_error: Optional[str]
    chunk_count: int = 0
    embedding_model: Optional[str]
    file_size_mb: float


class DocumentListResponse(BaseModel):
    """Document list response schema."""
    documents: List[DocumentResponse]
    total: int
    page: int
    page_size: int


class DocumentProcessingStatus(BaseModel):
    """Document processing status schema."""
    document_id: int
    status: str  # 'pending', 'processing', 'completed', 'failed'
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    error_message: Optional[str] = None
    chunks_created: int = 0
    estimated_time_remaining: Optional[int] = None  # seconds


# Error schemas
# Document chunk schemas
class DocumentChunk(BaseModel):
    """Document chunk schema."""
    id: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    page_number: Optional[int] = None
    chunk_index: int
    start_char: Optional[int] = None
    end_char: Optional[int] = None


class DocumentChunksResponse(BaseModel):
    """Document chunks response schema."""
    document_id: int
    document_name: str
    total_chunks: int
    chunks: List[DocumentChunk]


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None