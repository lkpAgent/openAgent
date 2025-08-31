#!/usr/bin/env python3
"""Create a new test user for testing."""

from backend.chat_agent.db.database import get_db
from backend.chat_agent.services.user import UserService
from backend.chat_agent.utils.schemas import UserCreate

def create_new_test_user():
    """Create a new test user."""
    db = next(get_db())
    try:
        user_service = UserService(db)
        
        # Create new test user data
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="password123",
            full_name="Test User"
        )
        
        # Check if user already exists
        existing_user = user_service.get_user_by_email(user_data.email)
        if existing_user:
            print(f"User {user_data.email} already exists, deleting first...")
            db.delete(existing_user)
            db.commit()
        
        existing_user = user_service.get_user_by_username(user_data.username)
        if existing_user:
            print(f"Username {user_data.username} already exists, deleting first...")
            db.delete(existing_user)
            db.commit()
        
        # Create new user
        user = user_service.create_user(user_data)
        print(f"Created new test user: {user.username} ({user.email})")
        
    except Exception as e:
        print(f"Error creating user: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    create_new_test_user()