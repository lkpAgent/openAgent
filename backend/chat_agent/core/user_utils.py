"""User utility functions for easy access to current user context."""

from typing import Optional
from ..models.user import User
from .context import UserContext


def get_current_user() -> Optional[User]:
    """Get current authenticated user from context.
    
    Returns:
        Current user if authenticated, None otherwise
    """
    return UserContext.get_current_user()


def get_current_user_id() -> Optional[int]:
    """Get current authenticated user ID from context.
    
    Returns:
        Current user ID if authenticated, None otherwise
    """
    return UserContext.get_current_user_id()


def require_current_user() -> User:
    """Get current authenticated user from context, raise exception if not found.
    
    Returns:
        Current user
        
    Raises:
        HTTPException: If no authenticated user in context
    """
    return UserContext.require_current_user()


def require_current_user_id() -> int:
    """Get current authenticated user ID from context, raise exception if not found.
    
    Returns:
        Current user ID
        
    Raises:
        HTTPException: If no authenticated user in context
    """
    return UserContext.require_current_user_id()


def is_user_authenticated() -> bool:
    """Check if there is an authenticated user in the current context.
    
    Returns:
        True if user is authenticated, False otherwise
    """
    return UserContext.get_current_user() is not None


def get_current_username() -> Optional[str]:
    """Get current authenticated user's username from context.
    
    Returns:
        Current user's username if authenticated, None otherwise
    """
    user = UserContext.get_current_user()
    return user.username if user else None


def get_current_user_email() -> Optional[str]:
    """Get current authenticated user's email from context.
    
    Returns:
        Current user's email if authenticated, None otherwise
    """
    user = UserContext.get_current_user()
    return user.email if user else None