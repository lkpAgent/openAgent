#!/usr/bin/env python3
"""Debug login flow step by step."""

from backend.chat_agent.db.database import get_db
from backend.chat_agent.services.auth import AuthService
from backend.chat_agent.utils.schemas import LoginRequest
from backend.chat_agent.api.endpoints.auth import login
from sqlalchemy.orm import Session
import asyncio

async def debug_login_flow():
    """Debug the complete login flow."""
    print("=== Debugging Login Flow ===")
    
    # Step 1: Test data validation
    print("\n1. Testing data validation...")
    try:
        login_data = LoginRequest(email="test@example.com", password="password123")
        print(f"✅ LoginRequest created: {login_data.email}")
    except Exception as e:
        print(f"❌ LoginRequest validation failed: {e}")
        return
    
    # Step 2: Test database connection
    print("\n2. Testing database connection...")
    try:
        db = next(get_db())
        print("✅ Database connection established")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    # Step 3: Test user lookup
    print("\n3. Testing user lookup...")
    try:
        from backend.chat_agent.models.user import User
        user_obj = db.query(User).filter(User.email == login_data.email).first()
        if user_obj:
            print(f"✅ User found: {user_obj.username} (ID: {user_obj.id})")
            print(f"   Email: {user_obj.email}")
            print(f"   Active: {user_obj.is_active}")
            print(f"   Hash: {user_obj.hashed_password[:30]}...")
        else:
            print(f"❌ User not found: {login_data.email}")
            db.close()
            return
    except Exception as e:
        print(f"❌ User lookup failed: {e}")
        db.close()
        return
    
    # Step 4: Test password verification
    print("\n4. Testing password verification...")
    try:
        is_valid = AuthService.verify_password(login_data.password, user_obj.hashed_password)
        print(f"Password verification result: {is_valid}")
        if is_valid:
            print("✅ Password verification successful")
        else:
            print("❌ Password verification failed")
            db.close()
            return
    except Exception as e:
        print(f"❌ Password verification error: {e}")
        db.close()
        return
    
    # Step 5: Test authenticate_user_by_email
    print("\n5. Testing authenticate_user_by_email...")
    try:
        auth_user = AuthService.authenticate_user_by_email(db, login_data.email, login_data.password)
        if auth_user:
            print(f"✅ Authentication successful: {auth_user.username}")
        else:
            print("❌ Authentication failed")
            db.close()
            return
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        db.close()
        return
    
    # Step 6: Test API endpoint directly
    print("\n6. Testing API endpoint directly...")
    try:
        # Create a new database session for the API call
        db_for_api = next(get_db())
        result = await login(login_data, db_for_api)
        print(f"✅ API endpoint successful: {result}")
        db_for_api.close()
    except Exception as e:
        print(f"❌ API endpoint failed: {e}")
        import traceback
        traceback.print_exc()
    
    db.close()
    print("\n=== Debug Complete ===")

if __name__ == '__main__':
    asyncio.run(debug_login_flow())