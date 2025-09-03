#!/usr/bin/env python3

import requests
import json

# Configuration
BASE_URL = "http://localhost:8001/api"
test_user = {
    "username": "test",
    "email": "test@example.com",
    "password": "testpass123"
}

def test_user_context():
    """Test UserContext functionality during conversation creation."""
    print("=== Testing UserContext in Conversation Creation ===")
    
    # Step 1: Login
    print("\n1. Logging in...")
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={
            "email": test_user["email"],
            "password": test_user["password"]
        }
    )
    
    print(f"Login status: {login_response.status_code}")
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.text}")
        return False
    
    token_data = login_response.json()
    token = token_data["access_token"]
    print(f"Token received: {token[:50]}...")
    
    # Step 2: Create conversation and check UserContext
    print("\n2. Creating conversation with UserContext test...")
    headers = {"Authorization": f"Bearer {token}"}
    
    conversation_data = {
        "title": "UserContext Test Conversation",
        "description": "Testing UserContext functionality"
    }
    
    create_response = requests.post(
        f"{BASE_URL}/chat/conversations",
        json=conversation_data,
        headers=headers
    )
    
    print(f"Create conversation status: {create_response.status_code}")
    if create_response.status_code != 200:
        print(f"Create conversation failed: {create_response.text}")
        return False
    
    conversation = create_response.json()
    print(f"✅ Success! Created conversation: {conversation['id']}")
    print(f"Title: {conversation['title']}")
    print(f"User ID: {conversation['user_id']}")
    
    # Step 3: Verify the conversation was created with correct user
    if conversation['user_id'] == 5:  # Expected user ID from our test
        print("✅ UserContext worked correctly - conversation has correct user_id")
        return True
    else:
        print(f"❌ UserContext failed - expected user_id 5, got {conversation['user_id']}")
        return False

if __name__ == "__main__":
    success = test_user_context()
    if success:
        print("\n🎉 UserContext test passed!")
        print("✅ UserContext.get_current_user() is working correctly in the conversation service")
    else:
        print("\n💥 UserContext test failed!")
        print("❌ UserContext.get_current_user() is still returning None")