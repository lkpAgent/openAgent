#!/usr/bin/env python3
"""Simple test for UserContext."""

import requests
import json

def test_create_conversation():
    """Test creating a conversation with UserContext."""
    print("=== Testing Create Conversation with UserContext ===")
    
    base_url = "http://localhost:8001/api"
    
    # Login to get token
    login_data = {
        "email": "test@example.com",
        "password": "123456"
    }
    
    try:
        # Step 1: Login
        response = requests.post(f"{base_url}/auth/login", json=login_data)
        if response.status_code != 200:
            print(f"Login failed: {response.status_code} - {response.text}")
            return
            
        token_data = response.json()
        token = token_data.get("access_token")
        print(f"✓ Login successful, token: {token[:20]}...")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Step 2: Create conversation
        conversation_data = {
            "title": "Test Conversation",
            "model_name": "deepseek-chat",
            "temperature": "0.7",
            "max_tokens": 2048
        }
        
        print("\nCreating conversation...")
        response = requests.post(f"{base_url}/chat/conversations", json=conversation_data, headers=headers)
        print(f"Create conversation status: {response.status_code}")
        
        if response.status_code == 200:
            conversation = response.json()
            print(f"✓ Conversation created successfully: ID {conversation.get('id')}")
            print(f"  Title: {conversation.get('title')}")
            print(f"  User ID: {conversation.get('user_id')}")
        else:
            print(f"✗ Create conversation failed: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Cannot connect to server. Make sure the server is running on localhost:8001")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_create_conversation()