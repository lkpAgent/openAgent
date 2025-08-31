#!/usr/bin/env python3
"""Test login API directly."""

import requests
import json

def test_login_api():
    """Test login API."""
    url = "http://localhost:8000/api/auth/login"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "email": "demo@example.com",
        "password": "123456"
    }
    
    try:
        print(f"Sending POST request to: {url}")
        print(f"Headers: {headers}")
        print(f"Data: {data}")
        
        response = requests.post(url, headers=headers, json=data)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Login successful! Token: {result.get('access_token', 'N/A')[:50]}...")
            return result.get('access_token')
        else:
            print(f"Login failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                print(f"Raw error response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None

if __name__ == '__main__':
    test_login_api()