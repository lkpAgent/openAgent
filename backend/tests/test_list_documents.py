#!/usr/bin/env python3
"""Test document listing API."""

import requests
import json

# API base URL
BASE_URL = "http://localhost:8000/api"

def test_list_documents():
    """Test document listing functionality."""
    
    # Step 1: Login
    print("Logging in...")
    login_data = {
        "email": "test@example.com",
        "password": "password123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    login_result = response.json()
    access_token = login_result["access_token"]
    print("✅ Login successful")
    
    # Step 2: Get knowledge bases
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{BASE_URL}/knowledge-bases", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Failed to get knowledge bases: {response.status_code}")
        return
    
    knowledge_bases = response.json()
    if not knowledge_bases:
        print("❌ No knowledge bases found")
        return
    
    kb_id = knowledge_bases[0]["id"]
    print(f"✅ Found knowledge base with ID: {kb_id}")
    
    # Step 3: List documents
    print(f"\nTesting document listing for knowledge base {kb_id}...")
    response = requests.get(f"{BASE_URL}/knowledge-bases/{kb_id}/documents", headers=headers)
    
    print(f"List Status: {response.status_code}")
    if response.status_code == 200:
        documents_data = response.json()
        print(f"Response: {json.dumps(documents_data, indent=2, ensure_ascii=False)}")
        print("✅ Document listing successful!")
    else:
        print(f"Response: {response.text}")
        print("❌ Document listing failed")

if __name__ == "__main__":
    test_list_documents()