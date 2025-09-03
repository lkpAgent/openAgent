#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from chat_agent.db.database import get_db_session
from chat_agent.models.user import User
from chat_agent.services.auth import AuthService

def create_test_user():
    """Create a test user for testing purposes."""
    db = get_db_session()
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == "test@example.com").first()
        if existing_user:
            print("Test user already exists!")
            print(f"User ID: {existing_user.id}")
            print(f"Username: {existing_user.username}")
            print(f"Email: {existing_user.email}")
            print(f"Is Active: {existing_user.is_active}")
            return existing_user
        
        # Create new user
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=AuthService.get_password_hash("testpass123"),
            is_active=True
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print("✅ Test user created successfully!")
        print(f"User ID: {user.id}")
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
        print(f"Is Active: {user.is_active}")
        
        return user
        
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        db.rollback()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()