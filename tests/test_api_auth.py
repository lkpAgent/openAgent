#!/usr/bin/env python3
"""Test API authentication flow."""

from backend.chat_agent.db.database import get_db
from backend.chat_agent.services.auth import AuthService
from backend.chat_agent.utils.schemas import LoginRequest
from pydantic import ValidationError

def test_api_auth():
    """Test API authentication flow."""
    # Test data parsing
    try:
        login_data = LoginRequest(email="demo@example.com", password="123456")
        print(f"Login data parsed: {login_data.email}")
    except ValidationError as e:
        print(f"Validation error: {e}")
        return
    
    # Test database connection
    db = next(get_db())
    try:
        print("Database connection established")
        
        # Test authentication
        print(f"Authenticating user: {login_data.email}")
        user = AuthService.authenticate_user_by_email(db, login_data.email, login_data.password)
        
        if user:
            print(f"Authentication successful: {user.username} ({user.email})")
            print(f"User ID: {user.id}")
            print(f"User active: {user.is_active}")
        else:
            print("Authentication failed - user not found or password incorrect")
            
    except Exception as e:
        print(f"Error during authentication: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
        print("Database connection closed")

if __name__ == '__main__':
    test_api_auth()