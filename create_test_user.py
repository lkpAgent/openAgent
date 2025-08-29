#!/usr/bin/env python3
"""Create a test user for login testing."""

from backend.chat_agent.db.database import get_db
from backend.chat_agent.services.user import UserService
from backend.chat_agent.utils.schemas import UserCreate

def create_test_user():
    """Create a test user."""
    db = next(get_db())
    user_service = UserService(db)
    
    # Create test user
    user_data = UserCreate(
        username='demo',
        email='demo@example.com',
        password='123456',
        full_name='Demo User'
    )
    
    try:
        # Check if user already exists
        existing_user = user_service.get_user_by_email(user_data.email)
        if existing_user:
            print(f'User already exists: {existing_user.username} ({existing_user.email})')
            return existing_user
        
        # Create new user
        user = user_service.create_user(user_data)
        print(f'Created user: {user.username} ({user.email})')
        return user
    except Exception as e:
        print(f'Error creating user: {e}')
        return None
    finally:
        db.close()

if __name__ == '__main__':
    create_test_user()