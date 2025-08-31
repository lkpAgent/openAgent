"""User service for managing user operations."""

from typing import Optional
from sqlalchemy.orm import Session

from ..models.user import User
from ..utils.schemas import UserCreate, UserUpdate
from ..utils.exceptions import DatabaseError, ValidationError
from ..utils.logger import get_logger
from .auth import AuthService

logger = get_logger(__name__)


class UserService:
    """Service for user management operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password."""
        return AuthService.get_password_hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return AuthService.verify_password(plain_password, hashed_password)
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        try:
            return self.db.query(User).filter(User.id == user_id).first()
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            raise DatabaseError(f"Failed to get user: {str(e)}")
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        try:
            return self.db.query(User).filter(User.email == email).first()
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            raise DatabaseError(f"Failed to get user: {str(e)}")
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        try:
            return self.db.query(User).filter(User.username == username).first()
        except Exception as e:
            logger.error(f"Error getting user by username {username}: {e}")
            raise DatabaseError(f"Failed to get user: {str(e)}")
    
    def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        try:
            # Validate input
            if len(user_data.password) < 6:
                raise ValidationError("Password must be at least 6 characters long")
            
            # Hash password
            hashed_password = self.get_password_hash(user_data.password)
            
            # Create user
            db_user = User(
                username=user_data.username,
                email=user_data.email,
                hashed_password=hashed_password,
                full_name=user_data.full_name,
                is_active=True
            )
            
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
            
            logger.info(f"User created successfully: {user_data.username}")
            return db_user
            
        except ValidationError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating user {user_data.username}: {e}")
            raise DatabaseError(f"Failed to create user: {str(e)}")
    
    def update_user(self, user_id: int, user_update: UserUpdate) -> Optional[User]:
        """Update user information."""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return None
            
            # Update fields
            update_data = user_update.dict(exclude_unset=True)
            
            if "password" in update_data:
                update_data["hashed_password"] = self.get_password_hash(update_data.pop("password"))
            
            for field, value in update_data.items():
                setattr(user, field, value)
            
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"User updated successfully: {user.username}")
            return user
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating user {user_id}: {e}")
            raise DatabaseError(f"Failed to update user: {str(e)}")
    
    def delete_user(self, user_id: int) -> bool:
        """Delete a user."""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            self.db.delete(user)
            self.db.commit()
            
            logger.info(f"User deleted successfully: {user.username}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting user {user_id}: {e}")
            raise DatabaseError(f"Failed to delete user: {str(e)}")
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password."""
        try:
            user = self.get_user_by_username(username)
            if not user:
                return None
            
            if not self.verify_password(password, user.hashed_password):
                return None
            
            if not user.is_active:
                return None
            
            return user
            
        except Exception as e:
            logger.error(f"Error authenticating user {username}: {e}")
            return None