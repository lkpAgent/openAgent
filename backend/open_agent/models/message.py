"""Message model."""

from sqlalchemy import Column, String, Integer, ForeignKey, Text, Enum, JSON
from sqlalchemy.orm import relationship
import enum

from ..db.base import BaseModel


class MessageRole(str, enum.Enum):
    """Message role enumeration."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageType(str, enum.Enum):
    """Message type enumeration."""
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    AUDIO = "audio"


class Message(BaseModel):
    """Message model."""
    
    __tablename__ = "messages"
    
    conversation_id = Column(Integer, nullable=False)  # Removed ForeignKey("conversations.id")
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(Enum(MessageType), default=MessageType.TEXT, nullable=False)
    message_metadata = Column(JSON, nullable=True)  # Store additional data like file info, tokens used, etc.
    
    # For knowledge base context
    context_documents = Column(JSON, nullable=True)  # Store retrieved document references
    
    # Token usage tracking
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    
    # Relationships removed to eliminate foreign key constraints
    
    def __repr__(self):
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<Message(id={self.id}, role='{self.role}', content='{content_preview}')>"
    
    def to_dict(self, include_metadata=True):
        """Convert to dictionary."""
        data = super().to_dict()
        if not include_metadata:
            data.pop('message_metadata', None)
            data.pop('context_documents', None)
            data.pop('prompt_tokens', None)
            data.pop('completion_tokens', None)
            data.pop('total_tokens', None)
        return data
    
    @property
    def is_from_user(self):
        """Check if message is from user."""
        return self.role == MessageRole.USER
    
    @property
    def is_from_assistant(self):
        """Check if message is from assistant."""
        return self.role == MessageRole.ASSISTANT