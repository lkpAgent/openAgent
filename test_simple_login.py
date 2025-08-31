#!/usr/bin/env python3
"""Simple login test."""

import requests
import json

def test_simple_login():
    """Test simple login."""
    url = "http://localhost:8000/api/auth/login"
    
    # Test with the new user we created
    data = {
        "email": "test@example.com",
        "password": "password123"
    }
    
    print(f"Testing login with: {data['email']}")
    print(f"URL: {url}")
    
    try:
        response = requests.post(
            url, 
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success! Token: {result.get('access_token', '')[:50]}...")
            return True
        else:
            print(f"❌ Failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Raw response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == '__main__':
    test_simple_login()