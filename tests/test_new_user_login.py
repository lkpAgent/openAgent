#!/usr/bin/env python3
"""Test new user login."""

import requests
import json

def test_new_user_login():
    """Test login with new user."""
    url = "http://localhost:8000/api/auth/login"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "email": "test@example.com",
        "password": "password123"
    }
    
    try:
        print(f"Testing login for new user: {data['email']}")
        print(f"Sending POST request to: {url}")
        
        response = requests.post(url, headers=headers, json=data)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Text: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Login successful!")
            print(f"Access Token: {result.get('access_token', 'N/A')[:50]}...")
            print(f"Token Type: {result.get('token_type', 'N/A')}")
            print(f"Expires In: {result.get('expires_in', 'N/A')} seconds")
            return result.get('access_token')
        else:
            print(f"❌ Login failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                print(f"Raw error response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

if __name__ == '__main__':
    token = test_new_user_login()
    if token:
        print("\n🎉 New user login test passed!")
    else:
        print("\n💥 New user login test failed!")