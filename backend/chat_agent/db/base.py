"""Database base model."""

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from typing import Optional


Base = declarative_base()


class BaseModel(Base):
    """Base model with common fields."""
    
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)

    def __init__(self, **kwargs):
        """Initialize ExcelFile and automatically set audit fields."""
        super().__init__(**kwargs)
        # Automatically set audit fields when creating new instance
        self.set_audit_fields()
    def set_audit_fields(self, user_id: Optional[int] = None, is_update: bool = False):
        """Set audit fields for create/update operations.

        Args:
            user_id: ID of the user performing the operation (optional, will use context if not provided)
            is_update: True for update operations, False for create operations
        """
        # Get user_id from context if not provided
        if user_id is None:
            from ..core.context import UserContext
            try:
                user_id = UserContext.get_current_user_id()
            except Exception:
                # If no user in context, skip setting audit fields
                return

        # Skip if still no user_id
        if user_id is None:
            return

        if not is_update:
            # For create operations, set both create_by and update_by
            self.created_by = user_id
            self.updated_by = user_id
        else:
            # For update operations, only set update_by
            self.updated_by = user_id
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }