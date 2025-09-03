#!/usr/bin/env python3
"""Debug middleware and user context."""

import requests
import json

def test_middleware_debug():
    """Test middleware with debug endpoint."""
    print("=== Testing Middleware Debug ===")
    
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
        
        # Step 2: Test /auth/me endpoint (should work with context)
        response = requests.get(f"{base_url}/auth/me", headers=headers)
        if response.status_code == 200:
            user_info = response.json()
            print(f"✓ /auth/me successful: {user_info.get('username')} (ID: {user_info.get('id')})")
        else:
            print(f"✗ /auth/me failed: {response.status_code} - {response.text}")
            
        # Step 3: Test conversations list (should work with context)
        response = requests.get(f"{base_url}/chat/conversations", headers=headers)
        if response.status_code == 200:
            conversations = response.json()
            print(f"✓ Conversations list successful: {len(conversations)} conversations")
        else:
            print(f"✗ Conversations list failed: {response.status_code} - {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Cannot connect to server. Make sure the server is running on localhost:8001")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_middleware_debug()