"""User service for managing user operations."""

from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc

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
            # Use options to avoid loading problematic relationships
            from sqlalchemy.orm import noload
            return self.db.query(User).options(
                noload(User.roles)
            ).filter(User.id == user_id).first()
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            raise DatabaseError(f"Failed to get user: {str(e)}")
    
    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID (alias for get_user_by_id)."""
        return self.get_user_by_id(user_id)
    
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
            
            # Set audit fields
            db_user.set_audit_fields()
            
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
            
            # Skip audit fields for now due to database schema mismatch
            # user.set_audit_fields(is_update=True)
            
            self.db.commit()
            self.db.refresh(user)
            
            logger.info(f"User updated successfully: {user.username}")
            return user
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating user {user_id}: {e}")
            raise DatabaseError(f"Failed to update user: {str(e)}")
    
    def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination."""
        try:
            return self.db.query(User).offset(skip).limit(limit).all()
        except Exception as e:
            logger.error(f"Error getting users: {e}")
            raise DatabaseError(f"Failed to get users: {str(e)}")
    
    def get_users_with_filters(
        self, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None,
        role_id: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> Tuple[List[User], int]:
        """Get users with filters and return total count."""
        try:
            query = self.db.query(User).order_by(desc('created_at'))
            
            # Apply filters
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        User.username.ilike(search_term),
                        User.email.ilike(search_term),
                        User.full_name.ilike(search_term)
                    )
                )
            
            if role_id is not None:
                from ..models.permission import UserRole
                query = query.join(UserRole).filter(UserRole.role_id == role_id)
            
            if is_active is not None:
                query = query.filter(User.is_active == is_active)
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            users = query.offset(skip).limit(limit).all()
            
            return users, total
            
        except Exception as e:
            logger.error(f"Error getting users with filters: {e}")
            raise DatabaseError(f"Failed to get users: {str(e)}")
    
    def delete_user(self, user_id: int) -> bool:
        """Delete a user."""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return False
            
            # Manually delete related records to avoid cascade issues
            from sqlalchemy import text
            
            # Delete user_roles records
            self.db.execute(text("DELETE FROM user_roles WHERE user_id = :user_id"), {"user_id": user_id})
            
            # Now delete the user
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
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """Change user password."""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                raise ValidationError("User not found")
            
            # Verify current password
            if not self.verify_password(current_password, user.hashed_password):
                raise ValidationError("Current password is incorrect")
            
            # Validate new password
            if len(new_password) < 6:
                raise ValidationError("New password must be at least 6 characters long")
            
            # Hash new password
            hashed_password = self.get_password_hash(new_password)
            
            # Update password
            user.hashed_password = hashed_password
            self.db.commit()
            
            logger.info(f"Password changed successfully for user: {user.username}")
            return True
            
        except ValidationError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error changing password for user {user_id}: {e}")
            raise DatabaseError(f"Failed to change password: {str(e)}")
    
    def reset_password(self, user_id: int, new_password: str) -> bool:
        """Reset user password (admin only, no current password required)."""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                raise ValidationError("User not found")
            
            # Validate new password
            if len(new_password) < 6:
                raise ValidationError("New password must be at least 6 characters long")
            
            # Hash new password
            hashed_password = self.get_password_hash(new_password)
            
            # Update password
            user.hashed_password = hashed_password
            self.db.commit()
            
            logger.info(f"Password reset successfully for user: {user.username}")
            return True
            
        except ValidationError:
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error resetting password for user {user_id}: {e}")
            raise DatabaseError(f"Failed to reset password: {str(e)}")