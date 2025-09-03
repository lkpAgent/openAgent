#!/usr/bin/env python3
"""
测试DELETE文档请求
"""

import requests
import json

# 配置
BASE_URL = "http://localhost:8001/api"
USERNAME = "demo"
PASSWORD = "demo123"

def login():
    """登录获取token"""
    login_data = {
        "email": "demo@example.com",  # 使用email而不是username
        "password": "123456"  # 使用测试用户的密码
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token")
    else:
        print(f"登录失败: {response.status_code} - {response.text}")
        return None

def test_delete_document(token, kb_id, doc_id):
    """测试删除文档"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print(f"\n测试删除文档: kb_id={kb_id}, doc_id={doc_id}")
    print(f"请求URL: {BASE_URL}/knowledge-bases/{kb_id}/documents/{doc_id}")
    
    response = requests.delete(
        f"{BASE_URL}/knowledge-bases/{kb_id}/documents/{doc_id}",
        headers=headers
    )
    
    print(f"响应状态码: {response.status_code}")
    print(f"响应头: {dict(response.headers)}")
    print(f"响应内容: {response.text}")
    
    return response.status_code == 200

def list_knowledge_bases(token):
    """列出知识库"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(f"{BASE_URL}/knowledge-bases/", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"获取知识库列表失败: {response.status_code} - {response.text}")
        return []

def list_documents(token, kb_id):
    """列出文档"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(f"{BASE_URL}/knowledge-bases/{kb_id}/documents", headers=headers)
    if response.status_code == 200:
        data = response.json()
        # API返回的是分页数据，实际文档列表在'documents'字段中
        if isinstance(data, dict) and 'documents' in data:
            return data['documents']
        return data
    else:
        print(f"获取文档列表失败: {response.status_code} - {response.text}")
        return []

def main():
    print("=== 测试DELETE文档请求 ===")
    
    # 1. 登录
    print("\n1. 登录...")
    token = login()
    if not token:
        print("登录失败，退出测试")
        return
    
    print(f"登录成功，token: {token[:20]}...")
    
    # 2. 获取知识库列表
    print("\n2. 获取知识库列表...")
    knowledge_bases = list_knowledge_bases(token)
    if not knowledge_bases:
        print("没有找到知识库")
        return
    
    print(f"找到 {len(knowledge_bases)} 个知识库:")
    for kb in knowledge_bases:
        print(f"  - {kb.get('name', 'Unknown')} (ID: {kb.get('id')})")
    
    # 3. 选择第一个知识库，获取文档列表
    kb_id = knowledge_bases[0]['id']
    print(f"\n3. 获取知识库 {kb_id} 的文档列表...")
    documents = list_documents(token, kb_id)
    
    if not documents:
        print("知识库中没有文档")
        return
    
    if not documents:
        print("知识库中没有文档")
        return
    
    print(f"找到 {len(documents)} 个文档:")
    for doc in documents:
        print(f"  - {doc.get('original_filename', doc.get('filename', 'Unknown'))} (ID: {doc.get('id')})")
    
    # 4. 测试删除第一个文档
    doc_id = documents[0]['id']
    print(f"\n4. 测试删除文档 {doc_id}...")
    success = test_delete_document(token, kb_id, doc_id)
    
    if success:
        print("✅ 删除成功")
    else:
        print("❌ 删除失败")

if __name__ == "__main__":
    main()