#!/usr/bin/env python3
"""Test API endpoint directly."""

import asyncio
from backend.chat_agent.db.database import get_db
from backend.chat_agent.services.auth import AuthService
from backend.chat_agent.utils.schemas import LoginRequest
from backend.chat_agent.api.endpoints.auth import login

async def test_api_direct():
    """Test API endpoint directly."""
    print("=== Testing API endpoint directly ===")
    
    # Create login request
    login_data = LoginRequest(email="demo@example.com", password="123456")
    print(f"Login data: {login_data.email}")
    
    # Get database session
    db = next(get_db())
    
    try:
        # Call API endpoint directly
        result = await login(login_data, db)
        print(f"✅ API call successful!")
        print(f"Access token: {result['access_token'][:50]}...")
        print(f"Token type: {result['token_type']}")
        print(f"Expires in: {result['expires_in']} seconds")
        return True
        
    except Exception as e:
        print(f"❌ API call failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()

if __name__ == '__main__':
    success = asyncio.run(test_api_direct())
    if success:
        print("\n🎉 Direct API test passed!")
    else:
        print("\n💥 Direct API test failed!")