"""LangChain-based chat service."""

import json
import asyncio
import os
import time
from typing import AsyncGenerator, Optional, List, Dict, Any
from sqlalchemy.orm import Session

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

from ..core.config import settings
from ..models.message import MessageRole
from ..utils.schemas import ChatResponse, StreamChunk, MessageResponse
from ..utils.exceptions import ChatServiceError, OpenAIError, AuthenticationError, RateLimitError
from ..utils.logger import get_logger
from .conversation import ConversationService

logger = get_logger("langchain_chat_service")


class StreamingCallbackHandler(BaseCallbackHandler):
    """Custom callback handler for streaming responses."""
    
    def __init__(self):
        self.tokens = []
        
    def on_llm_new_token(self, token: str, **kwargs) -> None:
        """Handle new token from LLM."""
        self.tokens.append(token)
        
    def get_response(self) -> str:
        """Get the complete response."""
        return "".join(self.tokens)
        
    def clear(self):
        """Clear the tokens."""
        self.tokens = []


class LangChainChatService:
    """LangChain-based chat service for AI model integration."""
    
    def __init__(self, db: Session):
        self.db = db
        self.conversation_service = ConversationService(db)
        
        from ..core.llm import create_llm
        
        # 添加调试日志
        logger.info(f"LLM Provider: {settings.llm.provider}")

        # Initialize LangChain ChatOpenAI
        self.llm = create_llm(streaming=False)
        
        # Streaming LLM for stream responses
        self.streaming_llm = create_llm(streaming=True)
        
        self.streaming_handler = StreamingCallbackHandler()
        
        logger.info(f"LangChain ChatService initialized with model: {self.llm.model_name}")
    
    def _prepare_langchain_messages(self, conversation, history: List) -> List:
        """Prepare messages for LangChain format."""
        messages = []
        
        # Add system message if conversation has system prompt
        if hasattr(conversation, 'system_prompt') and conversation.system_prompt:
            messages.append(SystemMessage(content=conversation.system_prompt))
        else:
            # Default system message
            messages.append(SystemMessage(
                content="You are a helpful AI assistant. Please provide accurate and helpful responses."
            ))
        
        # Add conversation history
        for msg in history[:-1]:  # Exclude the last message (current user message)
            if msg.role == MessageRole.USER:
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == MessageRole.ASSISTANT:
                messages.append(AIMessage(content=msg.content))
        
        # Add current user message
        if history:
            last_msg = history[-1]
            if last_msg.role == MessageRole.USER:
                messages.append(HumanMessage(content=last_msg.content))
        
        return messages
    
    async def chat(
        self, 
        conversation_id: int, 
        message: str, 
        stream: bool = False,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> ChatResponse:
        """Send a message and get AI response using LangChain."""
        logger.info(f"Processing LangChain chat request for conversation {conversation_id}")
        
        try:
            # Get conversation details
            conversation = self.conversation_service.get_conversation(conversation_id)
            if not conversation:
                raise ChatServiceError("Conversation not found")
            
            # Add user message to database
            user_message = self.conversation_service.add_message(
                conversation_id=conversation_id,
                content=message,
                role=MessageRole.USER
            )
            
            # Get conversation history for context
            history = self.conversation_service.get_conversation_history(
                conversation_id, limit=20
            )
            
            # Prepare messages for LangChain
            langchain_messages = self._prepare_langchain_messages(conversation, history)
            
            # Update LLM parameters if provided
            llm_to_use = self.llm
            if temperature is not None or max_tokens is not None:
                llm_config = settings.llm.get_current_config()
                llm_to_use = ChatOpenAI(
                    model=llm_config["model"],
                    openai_api_key=llm_config["api_key"],
                    openai_api_base=llm_config["base_url"],
                    temperature=temperature if temperature is not None else float(conversation.temperature),
                    max_tokens=max_tokens if max_tokens is not None else conversation.max_tokens,
                    streaming=False
                )
            
            # Call LangChain LLM
            response = await llm_to_use.ainvoke(langchain_messages)
            
            # Extract response content
            assistant_content = response.content
            
            # Add assistant message to database
            assistant_message = self.conversation_service.add_message(
                conversation_id=conversation_id,
                content=assistant_content,
                role=MessageRole.ASSISTANT,
                message_metadata={
                    "model": llm_to_use.model_name,
                    "langchain_version": "0.1.0",
                    "provider": "langchain_openai"
                }
            )
            
            # Update conversation timestamp
            self.conversation_service.update_conversation_timestamp(conversation_id)
            
            logger.info(f"Successfully processed LangChain chat request for conversation {conversation_id}")
            
            return ChatResponse(
                user_message=MessageResponse.from_orm(user_message),
                assistant_message=MessageResponse.from_orm(assistant_message),
                total_tokens=None,  # LangChain doesn't provide token count by default
                model_used=llm_to_use.model_name
            )
            
        except Exception as e:
            logger.error(f"Failed to process LangChain chat request for conversation {conversation_id}: {str(e)}", exc_info=True)
            
            # Classify error types for better handling
            error_type = type(e).__name__
            error_message = self._format_error_message(e)
            
            # Add error message to database
            assistant_message = self.conversation_service.add_message(
                conversation_id=conversation_id,
                content=error_message,
                role=MessageRole.ASSISTANT,
                message_metadata={
                    "error": True, 
                    "error_type": error_type,
                    "original_error": str(e),
                    "langchain_error": True
                }
            )
            
            # Re-raise specific exceptions for proper error handling
            if "rate limit" in str(e).lower():
                raise RateLimitError(str(e))
            elif "api key" in str(e).lower() or "authentication" in str(e).lower():
                raise AuthenticationError(str(e))
            elif "openai" in str(e).lower():
                raise OpenAIError(str(e))
            
            return ChatResponse(
                user_message=MessageResponse.from_orm(user_message),
                assistant_message=MessageResponse.from_orm(assistant_message),
                total_tokens=0,
                model_used=self.llm.model_name
            )
    
    async def chat_stream(
        self, 
        conversation_id: int, 
        message: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """Send a message and get streaming AI response using LangChain."""
        logger.info(f"Processing LangChain streaming chat request for conversation {conversation_id}")
        _start_time = time.perf_counter()
        try:
            # Get conversation details
            conversation = self.conversation_service.get_conversation(conversation_id)
            if not conversation:
                raise ChatServiceError("Conversation not found")
            
            # Add user message to database
            user_message = self.conversation_service.add_message(
                conversation_id=conversation_id,
                content=message,
                role=MessageRole.USER
            )
            print(f'spend {time.perf_counter() - _start_time} seconds')
            # Get conversation history for context
            history = self.conversation_service.get_conversation_history(
                conversation_id, limit=20
            )
            
            # Prepare messages for LangChain
            langchain_messages = self._prepare_langchain_messages(conversation, history)
            # Update streaming LLM parameters if provided
            streaming_llm_to_use = self.streaming_llm

            # Clear previous streaming handler state
            self.streaming_handler.clear()
            print(f'spend {time.perf_counter() - _start_time} seconds')
            # Stream response
            full_response = ""
            async for chunk in streaming_llm_to_use.astream(langchain_messages):
                if hasattr(chunk, 'content') and chunk.content:
                    full_response += chunk.content
                    yield chunk.content
            
            # Add complete assistant message to database
            self.conversation_service.add_message(
                conversation_id=conversation_id,
                content=full_response,
                role=MessageRole.ASSISTANT,
                message_metadata={
                    "model": streaming_llm_to_use.model_name,
                    "langchain_version": "0.1.0",
                    "provider": "langchain_openai",
                    "streaming": True
                }
            )
            
            # Update conversation timestamp
            self.conversation_service.update_conversation_timestamp(conversation_id)
            
            logger.info(f"Successfully processed LangChain streaming chat request for conversation {conversation_id}")
            
        except Exception as e:
            logger.error(f"Failed to process LangChain streaming chat request for conversation {conversation_id}: {str(e)}", exc_info=True)
            
            # Format error message for user
            error_message = self._format_error_message(e)
            yield error_message
            
            # Add error message to database
            self.conversation_service.add_message(
                conversation_id=conversation_id,
                content=error_message,
                role=MessageRole.ASSISTANT,
                message_metadata={
                    "error": True, 
                    "error_type": type(e).__name__,
                    "original_error": str(e),
                    "langchain_error": True,
                    "streaming": True
                }
            )
    
    async def get_available_models(self) -> List[str]:
        """Get list of available models from LangChain."""
        try:
            # LangChain doesn't have a direct method to list models
            # Return commonly available OpenAI models
            return [
                "gpt-3.5-turbo",
                "gpt-3.5-turbo-16k",
                "gpt-4",
                "gpt-4-turbo-preview",
                "gpt-4o",
                "gpt-4o-mini"
            ]
        except Exception as e:
            logger.error(f"Failed to get available models: {str(e)}")
            return ["gpt-3.5-turbo"]
    
    def update_model_config(
        self, 
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ):
        """Update LLM configuration."""
        from ..core.llm import create_llm
        
        # 重新创建LLM实例
        self.llm = create_llm(
            model=model,
            temperature=temperature,
            streaming=False
        )
        
        self.streaming_llm = create_llm(
            model=model,
            temperature=temperature,
            streaming=True
        )
        
        logger.info(f"Updated LLM configuration: model={model}, temperature={temperature}, max_tokens={max_tokens}")
    
    def _format_error_message(self, error: Exception) -> str:
        """Format error message for user display."""
        error_type = type(error).__name__
        error_str = str(error)
        
        # Provide user-friendly error messages
        if "rate limit" in error_str.lower():
            return "服务器繁忙，请稍后再试。"
        elif "api key" in error_str.lower() or "authentication" in error_str.lower():
            return "API认证失败，请检查配置。"
        elif "timeout" in error_str.lower():
            return "请求超时，请重试。"
        elif "connection" in error_str.lower():
            return "网络连接错误，请检查网络连接。"
        elif "model" in error_str.lower() and "not found" in error_str.lower():
            return "指定的模型不可用，请选择其他模型。"
        else:
            return f"处理请求时发生错误：{error_str}"
    
    async def _retry_with_backoff(self, func, max_retries: int = 3, base_delay: float = 1.0):
        """Retry function with exponential backoff."""
        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                
                # Check if error is retryable
                if not self._is_retryable_error(e):
                    raise e
                
                delay = base_delay * (2 ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {str(e)}")
                await asyncio.sleep(delay)
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """Check if an error is retryable."""
        error_str = str(error).lower()
        retryable_errors = [
            "timeout",
            "connection",
            "server error",
            "internal error",
            "rate limit"
        ]
        return any(err in error_str for err in retryable_errors)