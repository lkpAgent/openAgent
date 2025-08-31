#!/usr/bin/env python3
"""Test FastAPI request processing."""

import asyncio
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from chat_agent.main import app

def test_fastapi_request():
    """Test FastAPI request processing."""
    print("=== Testing FastAPI Request Processing ===")
    
    # Create test client
    client = TestClient(app)
    
    # Test data
    login_data = {
        "email": "test@example.com",
        "password": "password123"
    }
    
    print(f"\nTesting login with: {login_data['email']}")
    
    # Make request
    response = client.post("/api/auth/login", json=login_data)
    
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Success! Token: {result.get('access_token', '')[:50]}...")
        return True
    else:
        print(f"❌ Failed with status {response.status_code}")
        try:
            error_data = response.json()
            print(f"Error details: {error_data}")
        except:
            print(f"Raw response: {response.text}")
        return False

if __name__ == '__main__':
    test_fastapi_request()