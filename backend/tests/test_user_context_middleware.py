#!/usr/bin/env python3
"""Test UserContext middleware functionality."""

import requests
import json
from pathlib import Path
import sys

# Add backend directory to Python path
backend_dir = Path(__file__).parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from open_agent.core.context import UserContext
from open_agent.services.auth import AuthService
from open_agent.db.database import get_db_session
from open_agent.models.user import User

def test_user_context_direct():
    """Test UserContext directly."""
    print("=== Testing UserContext directly ===")
    
    # Test without user
    user_id = UserContext.get_current_user_id()
    print(f"Current user ID (should be None): {user_id}")
    
    # Create a mock user and set it
    db = get_db_session()
    try:
        user = db.query(User).filter(User.username == "demo").first()
        if user:
            UserContext.set_current_user(user)
            user_id = UserContext.get_current_user_id()
            print(f"Current user ID after setting: {user_id}")
            
            # Clear context
            UserContext.clear_current_user()
            user_id = UserContext.get_current_user_id()
            print(f"Current user ID after clearing: {user_id}")
        else:
            print("Demo user not found in database")
    finally:
        db.close()

def test_api_with_token():
    """Test API endpoints with token."""
    print("\n=== Testing API with token ===")
    
    base_url = "http://localhost:8001/api"
    
    # First, login to get token
    login_data = {
        "email": "test@example.com",
        "password": "123456"
    }
    
    try:
        # Login
        response = requests.post(f"{base_url}/auth/login", json=login_data)
        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get("access_token")
            print(f"Login successful, token: {token[:20]}...")
            
            # Test protected endpoint
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test conversations endpoint
            response = requests.get(f"{base_url}/chat/conversations", headers=headers)
            print(f"Conversations endpoint status: {response.status_code}")
            if response.status_code == 200:
                conversations = response.json()
                print(f"Found {len(conversations)} conversations")
            else:
                print(f"Error: {response.text}")
                
            # Test conversations count endpoint
            response = requests.get(f"{base_url}/chat/conversations/count", headers=headers)
            print(f"Conversations count endpoint status: {response.status_code}")
            if response.status_code == 200:
                count_data = response.json()
                print(f"Conversations count: {count_data}")
            else:
                print(f"Error: {response.text}")
                
        else:
            print(f"Login failed: {response.status_code} - {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Cannot connect to server. Make sure the server is running on localhost:8001")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_user_context_direct()
    test_api_with_token()