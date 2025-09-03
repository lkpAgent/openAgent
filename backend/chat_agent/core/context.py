"""Request context management."""

from contextvars import ContextVar
from typing import Optional
import threading
from ..models.user import User

# Context variable to store current user
current_user_context: ContextVar[Optional[User]] = ContextVar('current_user', default=None)

# Thread-local storage as backup
_thread_local = threading.local()


class UserContext:
    """User context manager for accessing current user globally."""
    
    @staticmethod
    def set_current_user(user: User) -> None:
        """Set current user in context."""
        import logging
        logging.info(f"Setting user in context: {user.username} (ID: {user.id})")
        
        # Set in ContextVar
        current_user_context.set(user)
        
        # Also set in thread-local as backup
        _thread_local.current_user = user
        
        # Verify it was set
        verify_user = current_user_context.get()
        logging.info(f"Verification - ContextVar user: {verify_user.username if verify_user else None}")
    
    @staticmethod
    def set_current_user_with_token(user: User):
        """Set current user in context and return token for cleanup."""
        import logging
        logging.info(f"Setting user in context with token: {user.username} (ID: {user.id})")
        
        # Set in ContextVar and get token
        token = current_user_context.set(user)
        
        # Also set in thread-local as backup
        _thread_local.current_user = user
        
        # Verify it was set
        verify_user = current_user_context.get()
        logging.info(f"Verification - ContextVar user: {verify_user.username if verify_user else None}")
        
        return token
    
    @staticmethod
    def reset_current_user_token(token):
        """Reset current user context using token."""
        import logging
        logging.info("Resetting user context using token")
        
        # Reset ContextVar using token
        current_user_context.reset(token)
        
        # Clear thread-local as well
        if hasattr(_thread_local, 'current_user'):
            delattr(_thread_local, 'current_user')
    
    @staticmethod
    def get_current_user() -> Optional[User]:
        """Get current user from context."""
        import logging
        
        # Try ContextVar first
        user = current_user_context.get()
        print('user==',user)
        if user:
            logging.debug(f"Got user from ContextVar: {user.username} (ID: {user.id})")
            return user
        
        # Fallback to thread-local
        user = getattr(_thread_local, 'current_user', None)
        if user:
            logging.debug(f"Got user from thread-local: {user.username} (ID: {user.id})")
            return user
        
        logging.warning("No user found in context (neither ContextVar nor thread-local)")
        return None
    
    @staticmethod
    def get_current_user_id() -> Optional[int]:
        """Get current user ID from context."""
        user = UserContext.get_current_user()
        return user.id if user else None
    
    @staticmethod
    def clear_current_user() -> None:
        """Clear current user from context."""
        import logging
        logging.info("Clearing user context")
        
        current_user_context.set(None)
        if hasattr(_thread_local, 'current_user'):
            delattr(_thread_local, 'current_user')
    
    @staticmethod
    def require_current_user() -> User:
        """Get current user from context, raise exception if not found."""
        user = current_user_context.get()
        if user is None:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No authenticated user in context"
            )
        return user
    
    @staticmethod
    def require_current_user_id() -> int:
        """Get current user ID from context, raise exception if not found."""
        user = UserContext.require_current_user()
        return user.id