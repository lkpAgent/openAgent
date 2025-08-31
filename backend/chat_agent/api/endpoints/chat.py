"""Chat endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ...db.database import get_db
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
    current_user = Depends(AuthService.get_current_user),
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
    current_user = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """List user's conversations."""
    conversation_service = ConversationService(db)
    conversations = conversation_service.get_user_conversations(
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    return [ConversationResponse.from_orm(conv) for conv in conversations]


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: int,
    current_user = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific conversation."""
    conversation_service = ConversationService(db)
    conversation = conversation_service.get_conversation(conversation_id)
    
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return ConversationResponse.from_orm(conversation)


@router.put("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: int,
    conversation_update: ConversationUpdate,
    current_user = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Update a conversation."""
    conversation_service = ConversationService(db)
    conversation = conversation_service.get_conversation(conversation_id)
    
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    updated_conversation = conversation_service.update_conversation(
        conversation_id, conversation_update
    )
    return ConversationResponse.from_orm(updated_conversation)


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    current_user = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a conversation."""
    conversation_service = ConversationService(db)
    conversation = conversation_service.get_conversation(conversation_id)
    
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    conversation_service.delete_conversation(conversation_id)
    return {"message": "Conversation deleted successfully"}


# Message management
@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Get messages from a conversation."""
    conversation_service = ConversationService(db)
    conversation = conversation_service.get_conversation(conversation_id)
    
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    messages = conversation_service.get_conversation_messages(
        conversation_id, skip=skip, limit=limit
    )
    return [MessageResponse.from_orm(msg) for msg in messages]


# Chat functionality
@router.post("/conversations/{conversation_id}/chat", response_model=ChatResponse)
async def chat(
    conversation_id: int,
    chat_request: ChatRequest,
    current_user = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message and get AI response."""
    conversation_service = ConversationService(db)
    conversation = conversation_service.get_conversation(conversation_id)
    
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
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
    current_user = Depends(AuthService.get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message and get streaming AI response."""
    conversation_service = ConversationService(db)
    conversation = conversation_service.get_conversation(conversation_id)
    
    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
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
