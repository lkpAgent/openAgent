"""Custom exceptions for the application."""

from typing import Any, Dict, Optional


class BaseCustomException(Exception):
    """Base custom exception class."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(BaseCustomException):
    """Exception raised when a resource is not found."""
    pass


class ValidationError(BaseCustomException):
    """Exception raised when validation fails."""
    pass


class AuthenticationError(BaseCustomException):
    """Exception raised when authentication fails."""
    pass


class AuthorizationError(BaseCustomException):
    """Exception raised when authorization fails."""
    pass


class DatabaseError(BaseCustomException):
    """Exception raised when database operations fail."""
    pass


class ConfigurationError(BaseCustomException):
    """Exception raised when configuration is invalid."""
    pass


class ExternalServiceError(BaseCustomException):
    """Exception raised when external service calls fail."""
    pass


class BusinessLogicError(BaseCustomException):
    """Exception raised when business logic validation fails."""
    pass