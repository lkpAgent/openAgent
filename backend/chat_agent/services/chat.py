"""Chat service for AI model integration using LangChain."""

import json
import asyncio
import os
from typing import AsyncGenerator, Optional, List, Dict, Any
from sqlalchemy.orm import Session

from ..core.config import settings
from ..models.message import MessageRole
from ..utils.schemas import ChatResponse, StreamChunk, MessageResponse
from ..utils.exceptions import ChatServiceError, OpenAIError
from ..utils.logger import get_logger
from .conversation import ConversationService
from .langchain_chat import LangChainChatService
from .knowledge_chat import KnowledgeChatService
from .agent.agent_service import get_agent_service

logger = get_logger("chat_service")


class ChatService:
    """Service for handling AI chat functionality using LangChain."""
    
    def __init__(self, db: Session):
        self.db = db
        self.conversation_service = ConversationService(db)
        
        # Initialize LangChain chat service
        self.langchain_service = LangChainChatService(db)
        
        # Initialize Knowledge chat service
        self.knowledge_service = KnowledgeChatService(db)
        
        # Initialize Agent service with database session
        self.agent_service = get_agent_service(db)
        
        logger.info("ChatService initialized with LangChain backend and Agent support")
    

    
    async def chat(
        self, 
        conversation_id: int, 
        message: str,
        stream: bool = False,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        use_agent: bool = False,
        use_knowledge_base: bool = False,
        knowledge_base_id: Optional[int] = None
    ) -> ChatResponse:
        """Send a message and get AI response using LangChain, Agent, or Knowledge Base."""
        if use_knowledge_base and knowledge_base_id:
            logger.info(f"Processing chat request for conversation {conversation_id} via Knowledge Base {knowledge_base_id}")
            
            # Use knowledge base chat service
            return await self.knowledge_service.chat_with_knowledge_base(
                conversation_id=conversation_id,
                message=message,
                knowledge_base_id=knowledge_base_id,
                stream=stream,
                temperature=temperature,
                max_tokens=max_tokens
            )
        elif use_agent:
            logger.info(f"Processing chat request for conversation {conversation_id} via Agent")
            
            # Get conversation history for agent
            conversation = self.conversation_service.get_conversation(conversation_id)
            if not conversation:
                raise ChatServiceError(f"Conversation {conversation_id} not found")
            
            messages = self.conversation_service.get_conversation_messages(conversation_id)
            chat_history = [{
                "role": "user" if msg.role == MessageRole.USER else "assistant",
                "content": msg.content
            } for msg in messages]
            
            # Use agent service
            agent_result = await self.agent_service.chat(message, chat_history)
            
            if agent_result["success"]:
                # Save user message
                user_message = self.conversation_service.add_message(
                    conversation_id=conversation_id,
                    content=message,
                    role=MessageRole.USER
                )
                
                # Save assistant response
                assistant_message = self.conversation_service.add_message(
                    conversation_id=conversation_id,
                    content=agent_result["response"],
                    role=MessageRole.ASSISTANT,
                    message_metadata={"tool_calls": agent_result["tool_calls"]}
                )
                
                return ChatResponse(
                    message=MessageResponse(
                        id=assistant_message.id,
                        content=agent_result["response"],
                        role=MessageRole.ASSISTANT,
                        conversation_id=conversation_id,
                        created_at=assistant_message.created_at,
                        metadata=assistant_message.metadata
                    )
                )
            else:
                raise ChatServiceError(f"Agent error: {agent_result.get('error', 'Unknown error')}")
        else:
            logger.info(f"Processing chat request for conversation {conversation_id} via LangChain")
            
            # Delegate to LangChain service
            return await self.langchain_service.chat(
                conversation_id=conversation_id,
                message=message,
                stream=stream,
                temperature=temperature,
                max_tokens=max_tokens
            )
    
    async def chat_stream(
        self, 
        conversation_id: int,
        message: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        use_agent: bool = False,
        use_knowledge_base: bool = False,
        knowledge_base_id: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """Send a message and get streaming AI response using LangChain, Agent, or Knowledge Base."""
        if use_knowledge_base and knowledge_base_id:
            logger.info(f"Processing streaming chat request for conversation {conversation_id} via Knowledge Base {knowledge_base_id}")
            
            # Use knowledge base chat service streaming
            async for content in self.knowledge_service.chat_stream_with_knowledge_base(
                conversation_id=conversation_id,
                message=message,
                knowledge_base_id=knowledge_base_id,
                temperature=temperature,
                max_tokens=max_tokens
            ):
                # Create stream chunk for compatibility with existing API
                stream_chunk = StreamChunk(
                    content=content,
                    role=MessageRole.ASSISTANT
                )
                yield json.dumps(stream_chunk.dict(), ensure_ascii=False)
        elif use_agent:
            logger.info(f"Processing streaming chat request for conversation {conversation_id} via Agent")
            
            # Get conversation history for agent
            conversation = self.conversation_service.get_conversation(conversation_id)
            if not conversation:
                raise ChatServiceError(f"Conversation {conversation_id} not found")
            
            messages = self.conversation_service.get_conversation_messages(conversation_id)
            chat_history = [{
                "role": "user" if msg.role == MessageRole.USER else "assistant",
                "content": msg.content
            } for msg in messages]
            
            # Save user message first
            user_message = self.conversation_service.add_message(
                conversation_id=conversation_id,
                content=message,
                role=MessageRole.USER
            )
            
            # Use agent service streaming
            full_response = ""
            tool_calls = []
            
            async for chunk in self.agent_service.chat_stream(message, chat_history):
                if chunk["type"] == "response":
                    full_response = chunk["content"]
                    tool_calls = chunk.get("tool_calls", [])
                    
                    # Return the chunk as-is to maintain type information
                    yield json.dumps(chunk, ensure_ascii=False)
                    
                elif chunk["type"] == "error":
                    # Return the chunk as-is to maintain type information
                    yield json.dumps(chunk, ensure_ascii=False)
                    return
                else:
                    # For other types (status, tool_start, etc.), pass through
                    yield json.dumps(chunk, ensure_ascii=False)
            
            # Save assistant response
            if full_response:
                self.conversation_service.add_message(
                    conversation_id=conversation_id,
                    content=full_response,
                    role=MessageRole.ASSISTANT,
                    message_metadata={"tool_calls": tool_calls}
                )
        else:
            logger.info(f"Processing streaming chat request for conversation {conversation_id} via LangChain")
            
            # Delegate to LangChain service and wrap response in JSON format
            async for content in self.langchain_service.chat_stream(
                conversation_id=conversation_id,
                message=message,
                temperature=temperature,
                max_tokens=max_tokens
            ):
                # Create stream chunk for compatibility with existing API
                stream_chunk = StreamChunk(
                    content=content,
                    role=MessageRole.ASSISTANT
                )
                yield json.dumps(stream_chunk.dict(), ensure_ascii=False)
    
    async def get_available_models(self) -> List[str]:
        """Get list of available models from LangChain."""
        logger.info("Getting available models via LangChain")
        
        # Delegate to LangChain service
        return await self.langchain_service.get_available_models()
    
    def update_model_config(
        self, 
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ):
        """Update LLM configuration via LangChain."""
        logger.info(f"Updating model config via LangChain: model={model}, temperature={temperature}, max_tokens={max_tokens}")
        
        # Delegate to LangChain service
        self.langchain_service.update_model_config(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )