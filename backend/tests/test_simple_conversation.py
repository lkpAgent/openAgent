#!/usr/bin/env python3

import requests
import json

# Test configuration
BASE_URL = "http://localhost:8001/api"
test_user = {
    "username": "test",
    "email": "test@example.com",
    "password": "testpass123"
}

def test_create_conversation():
    print("=== Testing Create Conversation ===\n")
    
    # Step 1: Login
    print("1. Logging in...")
    login_data = {
        "email": test_user["email"],
        "password": test_user["password"]
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"Login status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Login failed: {response.text}")
        return False
    
    token_data = response.json()
    token = token_data["access_token"]
    print(f"Token received: {token[:50]}...\n")
    
    # Step 2: Create conversation
    print("2. Creating conversation...")
    headers = {"Authorization": f"Bearer {token}"}
    conversation_data = {
        "title": "Test Conversation",
        "description": "A test conversation"
    }
    
    response = requests.post(
        f"{BASE_URL}/chat/conversations", 
        json=conversation_data,
        headers=headers
    )
    
    print(f"Create conversation status: {response.status_code}")
    
    if response.status_code == 200:
        conversation = response.json()
        print(f"✅ Success! Created conversation: {conversation['id']}")
        print(f"Title: {conversation['title']}")
        print(f"User ID: {conversation['user_id']}")
        return True
    else:
        print(f"❌ Failed to create conversation: {response.text}")
        return False

if __name__ == "__main__":
    success = test_create_conversation()
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n💥 Tests failed!")