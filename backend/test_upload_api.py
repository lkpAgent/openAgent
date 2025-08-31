#!/usr/bin/env python3
"""Test file upload API."""

import requests
import json
import os
from io import BytesIO

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

if login_response.status_code == 200:
    token_data = login_response.json()
    access_token = token_data["access_token"]
    print(f"✅ Login successful")
    
    # Get knowledge bases
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    kb_response = requests.get(
        "http://localhost:8000/api/knowledge-bases/",
        headers=headers
    )
    
    if kb_response.status_code == 200:
        knowledge_bases = kb_response.json()
        if knowledge_bases:
            kb_id = knowledge_bases[0]["id"]
            print(f"✅ Found knowledge base with ID: {kb_id}")
            
            # Create a test file
            test_content = "This is a test document for upload testing.\n\nIt contains some sample text to verify the upload functionality."
            test_file = BytesIO(test_content.encode('utf-8'))
            
            # Test file upload
            files = {
                'file': ('test_document.txt', test_file, 'text/plain')
            }
            data = {
                'process_immediately': 'true'
            }
            
            print(f"\nTesting file upload to knowledge base {kb_id}...")
            upload_response = requests.post(
                f"http://localhost:8000/api/knowledge-bases/{kb_id}/documents",
                headers={"Authorization": f"Bearer {access_token}"},
                files=files,
                data=data
            )
            
            print(f"Upload Status: {upload_response.status_code}")
            print(f"Response: {upload_response.text}")
            
            if upload_response.status_code == 200:
                print("✅ File upload successful!")
            else:
                print("❌ File upload failed")
        else:
            print("❌ No knowledge bases found")
    else:
        print(f"❌ Failed to get knowledge bases: {kb_response.text}")
else:
    print(f"❌ Login failed: {login_response.text}")