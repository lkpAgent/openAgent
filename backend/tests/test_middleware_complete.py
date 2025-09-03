#!/usr/bin/env python3
"""
完整的中间件测试脚本
测试UserContextMiddleware的所有功能
"""

import requests
import json
import sys

# 服务器配置
BASE_URL = "http://localhost:8001"

def test_unauthenticated_endpoints():
    """测试不需要认证的端点"""
    print("\n=== 测试不需要认证的端点 ===")
    
    endpoints = [
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/auth/login",
        "/api/auth/register"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            print(f"✓ {endpoint}: {response.status_code}")
        except Exception as e:
            print(f"✗ {endpoint}: 错误 - {e}")

def test_authenticated_endpoints_without_token():
    """测试需要认证的端点（无token）"""
    print("\n=== 测试需要认证的端点（无token）===")
    
    endpoints = [
        "/api/chat/conversations",
        "/api/users/me",
        "/api/chat/conversations/1/messages"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            if response.status_code == 403:
                print(f"✓ {endpoint}: 正确返回403 (未认证)")
            else:
                print(f"✗ {endpoint}: 期望403，实际{response.status_code}")
        except Exception as e:
            print(f"✗ {endpoint}: 错误 - {e}")

def get_auth_token():
    """获取认证token"""
    try:
        login_data = {
            "email": "test@example.com",
            "password": "testpass123"
        }
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=login_data,
            timeout=5
        )
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get("access_token")
        else:
            print(f"登录失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"登录错误: {e}")
        return None

def test_authenticated_endpoints_with_token(token):
    """测试需要认证的端点（有token）"""
    print("\n=== 测试需要认证的端点（有token）===")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    endpoints = [
        "/api/chat/conversations",
        "/api/users/me"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=5)
            if response.status_code == 200:
                print(f"✓ {endpoint}: 认证成功 (200)")
            else:
                print(f"✗ {endpoint}: 期望200，实际{response.status_code} - {response.text}")
        except Exception as e:
            print(f"✗ {endpoint}: 错误 - {e}")

def main():
    print("开始测试UserContextMiddleware...")
    
    # 测试不需要认证的端点
    test_unauthenticated_endpoints()
    
    # 测试需要认证的端点（无token）
    test_authenticated_endpoints_without_token()
    
    # 获取token并测试认证端点
    print("\n=== 获取认证token ===")
    token = get_auth_token()
    if token:
        print(f"✓ 成功获取token: {token[:20]}...")
        test_authenticated_endpoints_with_token(token)
    else:
        print("✗ 无法获取token，跳过认证测试")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    main()