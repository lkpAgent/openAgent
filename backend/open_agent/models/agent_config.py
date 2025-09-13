"""Agent configuration model."""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from ..db.base import BaseModel


class AgentConfig(BaseModel):
    """Agent configuration model."""
    
    __tablename__ = "agent_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Agent configuration
    enabled_tools = Column(JSON, nullable=False, default=list)
    max_iterations = Column(Integer, default=10)
    temperature = Column(String(10), default="0.1")
    system_message = Column(Text, nullable=True)
    verbose = Column(Boolean, default=True)
    
    # Model configuration
    model_name = Column(String(100), default="gpt-3.5-turbo")
    max_tokens = Column(Integer, default=2048)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)

    
    def __repr__(self):
        return f"<AgentConfig(id={self.id}, name='{self.name}', is_active={self.is_active})>"
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "enabled_tools": self.enabled_tools or [],
            "max_iterations": self.max_iterations,
            "temperature": self.temperature,
            "system_message": self.system_message,
            "verbose": self.verbose,
            "model_name": self.model_name,
            "max_tokens": self.max_tokens,
            "is_active": self.is_active,
            "is_default": self.is_default,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }