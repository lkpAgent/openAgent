#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from open_agent.db.database import get_db_session
from open_agent.models.user import User
from open_agent.services.auth import AuthService

def reset_test_user_password():
    """Reset test user password."""
    db = get_db_session()
    
    try:
        # Find the test user
        user = db.query(User).filter(User.email == "test@example.com").first()
        if not user:
            print("❌ Test user not found!")
            return False
        
        print(f"Found user: {user.username} ({user.email})")
        
        # Reset password
        new_password = "testpass123"
        user.hashed_password = AuthService.get_password_hash(new_password)
        
        db.commit()
        
        print(f"✅ Password reset successfully for user {user.username}")
        print(f"New password: {new_password}")
        
        # Test the password
        if AuthService.verify_password(new_password, user.hashed_password):
            print("✅ Password verification successful")
        else:
            print("❌ Password verification failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Error resetting password: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    reset_test_user_password()