#!/usr/bin/env python3
"""测试HTTP认证"""

import requests
import sys
import os
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "backend"))

# 切换到backend目录，确保使用相同的数据库
os.chdir(str(Path(__file__).parent / "backend"))

from chat_agent.db.database import get_db_session
from chat_agent.services.auth import AuthService
from chat_agent.models.user import User

BASE_URL = "http://localhost:8000"

def test_http_auth():
    """测试HTTP认证"""
    print("开始测试HTTP认证...")
    
    # 1. 获取token
    db = get_db_session()
    try:
        user = db.query(User).filter(User.username == "demo").first()
        if not user:
            print("❌ 用户不存在")
            return
        
        token = AuthService.create_access_token(data={"sub": user.username})
        print(f"✅ Token: {token[:50]}...")
        
    finally:
        db.close()
    
    # 2. 测试不同的API端点
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 测试获取当前用户信息
    print("\n测试 /api/auth/me 端点...")
    response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        print(f"✅ 用户信息: {response.json()}")
    else:
        print(f"❌ 错误: {response.text}")
    
    # 测试获取知识库列表
    print("\n测试 /api/knowledge-bases/ 端点...")
    response = requests.get(f"{BASE_URL}/api/knowledge-bases/", headers=headers)
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        kb_list = response.json()
        print(f"✅ 知识库列表: {len(kb_list)} 个知识库")
        for kb in kb_list:
            print(f"  - {kb['name']} (ID: {kb['id']})")
    else:
        print(f"❌ 错误: {response.text}")

if __name__ == "__main__":
    test_http_auth()