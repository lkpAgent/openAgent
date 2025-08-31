#!/usr/bin/env python3
"""Test knowledge base API with authentication."""

import requests
import json

# Login to get token
login_data = {
    "email": "test@example.com",
    "password": "password123"
}

print("Logging in...")
login_response = requests.post(
    "http://localhost:8000/api/auth/login",
    json=login_data,
    headers={"Content-Type": "application/json"}
)

print(f"Login Status: {login_response.status_code}")
if login_response.status_code == 200:
    token_data = login_response.json()
    access_token = token_data["access_token"]
    print(f"Access token obtained: {access_token[:20]}...")
    
    # Test knowledge base API
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    print("\nTesting knowledge base API...")
    kb_response = requests.get(
        "http://localhost:8000/api/knowledge-bases/",
        headers=headers
    )
    
    print(f"Knowledge Base API Status: {kb_response.status_code}")
    print(f"Response: {kb_response.text}")
    
    if kb_response.status_code == 200:
        print("✅ Knowledge base API is working!")
    else:
        print("❌ Knowledge base API failed")
else:
    print(f"❌ Login failed: {login_response.text}")