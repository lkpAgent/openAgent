#!/usr/bin/env python3
"""Test new user authentication."""

from backend.chat_agent.db.database import get_db
from backend.chat_agent.services.auth import AuthService

def test_new_user_auth():
    """Test new user authentication."""
    db = next(get_db())
    try:
        print("Testing authentication for new user: test@example.com")
        
        # Test authenticate_user_by_email
        user = AuthService.authenticate_user_by_email(db, 'test@example.com', 'password123')
        if user:
            print(f"✅ Authentication successful: {user.username} ({user.email})")
            print(f"User ID: {user.id}")
            print(f"User active: {user.is_active}")
            print(f"Hashed password: {user.hashed_password[:50]}...")
        else:
            print("❌ Authentication failed")
            
        # Also test direct password verification
        from backend.chat_agent.models.user import User
        user_obj = db.query(User).filter(User.email == 'test@example.com').first()
        if user_obj:
            print(f"\nUser found in database: {user_obj.username}")
            print(f"Stored hash: {user_obj.hashed_password[:50]}...")
            
            # Test password verification
            is_valid = AuthService.verify_password('password123', user_obj.hashed_password)
            print(f"Password verification result: {is_valid}")
        else:
            print("❌ User not found in database")
            
    except Exception as e:
        print(f"❌ Error during authentication: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    test_new_user_auth()