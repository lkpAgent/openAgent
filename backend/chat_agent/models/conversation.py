"""Conversation model."""

from sqlalchemy import Column, String, Integer, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship

from ..db.base import BaseModel


class Conversation(BaseModel):
    """Conversation model."""
    
    __tablename__ = "conversations"
    
    title = Column(String(200), nullable=False)
    user_id = Column(Integer, nullable=False)  # Removed ForeignKey("users.id")
    knowledge_base_id = Column(Integer, nullable=True)  # Removed ForeignKey("knowledge_bases.id")
    system_prompt = Column(Text, nullable=True)
    model_name = Column(String(100), nullable=False, default="gpt-3.5-turbo")
    temperature = Column(String(10), nullable=False, default="0.7")
    max_tokens = Column(Integer, nullable=False, default=2048)
    is_archived = Column(Boolean, default=False, nullable=False)
    
    # Relationships removed to eliminate foreign key constraints
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, title='{self.title}', user_id={self.user_id})>"
    
    @property
    def message_count(self):
        """Get the number of messages in this conversation."""
        return len(self.messages)
    
    @property
    def last_message_at(self):
        """Get the timestamp of the last message."""
        if self.messages:
            return self.messages[-1].created_at
        return self.created_at