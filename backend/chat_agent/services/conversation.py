"""Conversation service."""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..models.conversation import Conversation
from ..models.message import Message, MessageRole
from ..utils.schemas import ConversationCreate, ConversationUpdate
from ..utils.exceptions import ConversationNotFoundError, DatabaseError
from ..utils.logger import get_logger

logger = get_logger("conversation_service")


class ConversationService:
    """Service for managing conversations and messages."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_conversation(
        self, 
        user_id: int, 
        conversation_data: ConversationCreate
    ) -> Conversation:
        """Create a new conversation."""
        logger.info(f"Creating new conversation for user {user_id}")
        
        try:
            conversation = Conversation(
                user_id=user_id,
                **conversation_data.dict()
            )
            self.db.add(conversation)
            self.db.commit()
            self.db.refresh(conversation)
            
            logger.info(f"Successfully created conversation {conversation.id}")
            return conversation
            
        except Exception as e:
            logger.error(f"Failed to create conversation: {str(e)}", exc_info=True)
            self.db.rollback()
            raise DatabaseError(f"Failed to create conversation: {str(e)}")
    
    def get_conversation(self, conversation_id: int) -> Optional[Conversation]:
        """Get a conversation by ID."""
        try:
            conversation = self.db.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()
            
            if not conversation:
                logger.warning(f"Conversation {conversation_id} not found")
            
            return conversation
            
        except Exception as e:
            logger.error(f"Failed to get conversation {conversation_id}: {str(e)}", exc_info=True)
            raise DatabaseError(f"Failed to get conversation: {str(e)}")
    
    def get_user_conversations(
        self, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 50
    ) -> List[Conversation]:
        """Get user's conversations."""
        return self.db.query(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.is_archived == False
        ).order_by(desc(Conversation.updated_at)).offset(skip).limit(limit).all()
    
    def update_conversation(
        self, 
        conversation_id: int, 
        conversation_update: ConversationUpdate
    ) -> Optional[Conversation]:
        """Update a conversation."""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return None
        
        update_data = conversation_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(conversation, field, value)
        
        self.db.commit()
        self.db.refresh(conversation)
        return conversation
    
    def delete_conversation(self, conversation_id: int) -> bool:
        """Delete a conversation."""
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return False
        
        self.db.delete(conversation)
        self.db.commit()
        return True
    
    def get_conversation_messages(
        self, 
        conversation_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Message]:
        """Get messages from a conversation."""
        return self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at).offset(skip).limit(limit).all()
    
    def add_message(
        self, 
        conversation_id: int, 
        content: str, 
        role: MessageRole,
        message_metadata: Optional[dict] = None,
        context_documents: Optional[list] = None,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None
    ) -> Message:
        """Add a message to a conversation."""
        message = Message(
            conversation_id=conversation_id,
            content=content,
            role=role,
            message_metadata=message_metadata,
            context_documents=context_documents,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message
    
    def get_conversation_history(
        self, 
        conversation_id: int, 
        limit: int = 20
    ) -> List[Message]:
        """Get recent conversation history for context."""
        return self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(desc(Message.created_at)).limit(limit).all()[::-1]  # Reverse to get chronological order
    
    def update_conversation_timestamp(self, conversation_id: int) -> None:
        """Update conversation's updated_at timestamp."""
        conversation = self.get_conversation(conversation_id)
        if conversation:
            # SQLAlchemy will automatically update the updated_at field
            self.db.commit()