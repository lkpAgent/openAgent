#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from chat_agent.db.database import get_db_session
from chat_agent.models.user import User
from chat_agent.services.auth import AuthService

def debug_password():
    """Debug password verification."""
    db = get_db_session()
    
    try:
        # Find the test user
        user = db.query(User).filter(User.email == "test@example.com").first()
        if not user:
            print("❌ Test user not found!")
            return False
        
        print(f"Found user: {user.username} ({user.email})")
        print(f"Stored hash: {user.hashed_password[:50]}...")
        
        # Test different passwords
        test_passwords = ["testpass123", "password", "test123", "admin"]
        
        for password in test_passwords:
            try:
                is_valid = AuthService.verify_password(password, user.hashed_password)
                print(f"Password '{password}': {'✅ VALID' if is_valid else '❌ INVALID'}")
                if is_valid:
                    print(f"✅ Correct password found: {password}")
                    break
            except Exception as e:
                print(f"Error verifying password '{password}': {e}")
        
        # Try to authenticate with the service
        print("\n=== Testing AuthService.authenticate_user ===")
        try:
            auth_user = AuthService.authenticate_user(db, "test@example.com", "testpass123")
            if auth_user:
                print(f"✅ Authentication successful: {auth_user.username}")
            else:
                print("❌ Authentication failed")
        except Exception as e:
            print(f"❌ Authentication error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    debug_password()