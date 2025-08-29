"""Custom exceptions and error handlers for the chat agent application."""

from typing import Any, Dict, Optional
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from .logger import get_logger

logger = get_logger("exceptions")


class ChatAgentException(Exception):
    """Base exception for chat agent application."""
    
    def __init__(
        self,
        message: str,
        status_code: int = HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(ChatAgentException):
    """Validation error exception."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, HTTP_422_UNPROCESSABLE_ENTITY, details)


class AuthenticationError(ChatAgentException):
    """Authentication error exception."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, HTTP_401_UNAUTHORIZED)


class AuthorizationError(ChatAgentException):
    """Authorization error exception."""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, HTTP_403_FORBIDDEN)


class NotFoundError(ChatAgentException):
    """Resource not found exception."""
    
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, HTTP_404_NOT_FOUND)


class ConversationNotFoundError(NotFoundError):
    """Conversation not found exception."""
    
    def __init__(self, conversation_id: str):
        super().__init__(f"Conversation with ID {conversation_id} not found")


class UserNotFoundError(NotFoundError):
    """User not found exception."""
    
    def __init__(self, user_id: str):
        super().__init__(f"User with ID {user_id} not found")


class ChatServiceError(ChatAgentException):
    """Chat service error exception."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, HTTP_500_INTERNAL_SERVER_ERROR, details)


class OpenAIError(ChatServiceError):
    """OpenAI API error exception."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(f"OpenAI API error: {message}", details)


class RateLimitError(ChatAgentException):
    """Rate limit exceeded error."""
    pass


class DatabaseError(ChatAgentException):
    """Database operation error exception."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(f"Database error: {message}", details)


# Error handlers
async def chat_agent_exception_handler(request: Request, exc: ChatAgentException) -> JSONResponse:
    """Handle ChatAgentException and its subclasses."""
    logger.error(
        f"ChatAgentException: {exc.message}",
        extra={
            "status_code": exc.status_code,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "type": exc.__class__.__name__,
                "details": exc.details
            }
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTPException."""
    logger.warning(
        f"HTTPException: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.detail,
                "type": "HTTPException"
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    logger.error(
        f"Unhandled exception: {str(exc)}",
        extra={
            "exception_type": exc.__class__.__name__,
            "path": request.url.path,
            "method": request.method
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "message": "Internal server error",
                "type": "InternalServerError"
            }
        }
    )