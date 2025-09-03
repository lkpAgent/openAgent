#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from chat_agent.db.database import get_db_session
from chat_agent.models.user import User
from chat_agent.services.auth import AuthService

def recreate_test_user():
    """Delete and recreate test user."""
    db = get_db_session()
    
    try:
        # Delete existing test user
        existing_user = db.query(User).filter(User.email == "test@example.com").first()
        if existing_user:
            print(f"Deleting existing user: {existing_user.username}")
            db.delete(existing_user)
            db.commit()
        
        # Create new user with fresh password hash
        print("Creating new test user...")
        
        # Test password hashing first
        test_password = "testpass123"
        print(f"Testing password: {test_password}")
        
        try:
            hashed = AuthService.get_password_hash(test_password)
            print(f"Generated hash: {hashed[:50]}...")
            
            # Verify the hash immediately
            is_valid = AuthService.verify_password(test_password, hashed)
            print(f"Hash verification: {'✅ SUCCESS' if is_valid else '❌ FAILED'}")
            
            if not is_valid:
                print("❌ Password hashing/verification is broken!")
                return False
                
        except Exception as e:
            print(f"❌ Error with password hashing: {e}")
            return False
        
        # Create user
        user = User(
            username="test",
            email="test@example.com",
            hashed_password=hashed,
            is_active=True
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print(f"✅ User created: {user.username} (ID: {user.id})")
        
        # Test authentication
        print("\n=== Testing authentication ===")
        auth_user = AuthService.authenticate_user_by_email(db, "test@example.com", test_password)
        if auth_user:
            print(f"✅ Authentication successful: {auth_user.username}")
            return True
        else:
            print("❌ Authentication failed")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    recreate_test_user()