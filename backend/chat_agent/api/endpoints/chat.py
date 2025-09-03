"""Chat endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ...db.database import get_db
from ...models.user import User
from ...services.auth import AuthService
from ...services.chat import ChatService
from ...services.conversation import ConversationService
from ...utils.schemas import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
    MessageCreate,
    MessageResponse,
    ChatRequest,
    ChatResponse
)

router = APIRouter()


# Conversation management
@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new conversation."""
    conversation_service = ConversationService(db)
    conversation = conversation_service.create_conversation(
        user_id=current_user.id,
        conversation_data=conversation_data
    )
    return ConversationResponse.from_orm(conversation)


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    skip: int = 0,
    limit: int = 50,
    search: str = None,
    include_archived: bool = False,
    order_by: str = "updated_at",
    order_desc: bool = True,
    db: Session = Depends(get_db)
):
    """List user's conversations with search and filtering."""
    conversation_service = ConversationService(db)
    conversations = conversation_service.get_user_conversations(
        skip=skip,
        limit=limit,
        search_query=search,
        include_archived=include_archived,
        order_by=order_by,
        order_desc=order_desc
    )
    return [ConversationResponse.from_orm(conv) for conv in conversations]


@router.get("/conversations/count")
async def get_conversations_count(
    search: str = None,
    include_archived: bool = False,
    db: Session = Depends(get_db)
):
    """Get total count of conversations."""
    conversation_service = ConversationService(db)
    count = conversation_service.get_user_conversations_count(
        search_query=search,
        include_archived=include_archived
    )
    return {"count": count}


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific conversation."""
    conversation_service = ConversationService(db)
    conversation = conversation_service.get_conversation(
        conversation_id=conversation_id
    )
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    return ConversationResponse.from_orm(conversation)


@router.put("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: int,
    conversation_update: ConversationUpdate,
    db: Session = Depends(get_db)
):
    """Update a conversation."""
    conversation_service = ConversationService(db)
    updated_conversation = conversation_service.update_conversation(
        conversation_id, conversation_update
    )
    return ConversationResponse.from_orm(updated_conversation)


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """Delete a conversation."""
    conversation_service = ConversationService(db)
    conversation_service.delete_conversation(conversation_id)
    return {"message": "Conversation deleted successfully"}


@router.put("/conversations/{conversation_id}/archive")
async def archive_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """Archive a conversation."""
    conversation_service = ConversationService(db)
    success = conversation_service.archive_conversation(conversation_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to archive conversation"
        )
    
    return {"message": "Conversation archived successfully"}


@router.put("/conversations/{conversation_id}/unarchive")
async def unarchive_conversation(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """Unarchive a conversation."""
    conversation_service = ConversationService(db)
    success = conversation_service.unarchive_conversation(conversation_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to unarchive conversation"
        )
    
    return {"message": "Conversation unarchived successfully"}


# Message management
@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get messages from a conversation."""
    conversation_service = ConversationService(db)
    messages = conversation_service.get_conversation_messages(
        conversation_id, skip=skip, limit=limit
    )
    return [MessageResponse.from_orm(msg) for msg in messages]


# Chat functionality
@router.post("/conversations/{conversation_id}/chat", response_model=ChatResponse)
async def chat(
    conversation_id: int,
    chat_request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Send a message and get AI response."""
    chat_service = ChatService(db)
    response = await chat_service.chat(
        conversation_id=conversation_id,
        message=chat_request.message,
        stream=False,
        temperature=chat_request.temperature,
        max_tokens=chat_request.max_tokens,
        use_agent=chat_request.use_agent,
        use_knowledge_base=chat_request.use_knowledge_base,
        knowledge_base_id=chat_request.knowledge_base_id
    )
    
    return response


@router.post("/conversations/{conversation_id}/chat/stream")
async def chat_stream(
    conversation_id: int,
    chat_request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Send a message and get streaming AI response."""
    chat_service = ChatService(db)
    
    async def generate_response():
        async for chunk in chat_service.chat_stream(
            conversation_id=conversation_id,
            message=chat_request.message,
            temperature=chat_request.temperature,
            max_tokens=chat_request.max_tokens,
            use_agent=chat_request.use_agent,
            use_knowledge_base=chat_request.use_knowledge_base,
            knowledge_base_id=chat_request.knowledge_base_id
        ):
            yield f"data: {chunk}\n\n"
    
    return StreamingResponse(
        generate_response(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
