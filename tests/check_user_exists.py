#!/usr/bin/env python3
"""Check if demo user exists in database."""

from backend.chat_agent.db.database import get_db
from backend.chat_agent.services.user import UserService
from backend.chat_agent.services.auth import AuthService

def check_user_exists():
    """Check if demo user exists."""
    db = next(get_db())
    try:
        # Create UserService instance
        user_service = UserService(db)
        
        # Check if user exists
        user = user_service.get_user_by_email("demo@example.com")
        if user:
            print(f"✅ User found: {user.username} ({user.email})")
            print(f"User ID: {user.id}")
            print(f"User active: {user.is_active}")
            print(f"Hashed password: {user.hashed_password[:50]}...")
            
            # Test password verification
            is_valid = AuthService.verify_password("123456", user.hashed_password)
            print(f"Password verification: {is_valid}")
            
            # Test authentication
            auth_user = AuthService.authenticate_user_by_email(db, "demo@example.com", "123456")
            if auth_user:
                print(f"✅ Authentication successful: {auth_user.username}")
            else:
                print("❌ Authentication failed")
        else:
            print("❌ User not found")
            
            # List all users
            print("\nAll users in database:")
            # Note: get_users method may not exist, let's query directly
            from backend.chat_agent.models.user import User
            users = db.query(User).all()
            for u in users:
                print(f"- {u.username} ({u.email}) - Active: {u.is_active}")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    check_user_exists()