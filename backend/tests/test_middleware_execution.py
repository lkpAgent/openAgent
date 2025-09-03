#!/usr/bin/env python3
"""
测试中间件是否被执行的脚本
"""

import requests
import json
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_middleware_execution():
    """测试中间件是否被执行"""
    base_url = "http://localhost:8001"
    
    print("=== 测试中间件执行 ===")
    
    # 1. 测试健康检查端点（应该跳过认证）
    print("\n1. 测试健康检查端点...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"健康检查状态码: {response.status_code}")
        print(f"响应: {response.json()}")
    except Exception as e:
        print(f"健康检查失败: {e}")
        return
    
    # 2. 测试需要认证的端点（没有token）
    print("\n2. 测试需要认证的端点（无token）...")
    try:
        response = requests.get(f"{base_url}/api/chat/sessions")
        print(f"无token请求状态码: {response.status_code}")
        if response.status_code != 200:
            print(f"响应: {response.text}")
    except Exception as e:
        print(f"无token请求失败: {e}")
    
    # 3. 登录获取token
    print("\n3. 登录获取token...")
    login_data = {
        "email": "test@example.com",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"登录状态码: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get("access_token")
            print(f"获取到token: {token[:20]}...")
            
            # 4. 使用token测试需要认证的端点
            print("\n4. 使用token测试需要认证的端点...")
            headers = {"Authorization": f"Bearer {token}"}
            
            try:
                response = requests.get(f"{base_url}/api/chat/sessions", headers=headers)
                print(f"带token请求状态码: {response.status_code}")
                if response.status_code == 200:
                    sessions = response.json()
                    print(f"获取到 {len(sessions)} 个会话")
                else:
                    print(f"响应: {response.text}")
            except Exception as e:
                print(f"带token请求失败: {e}")
        else:
            print(f"登录失败: {response.text}")
    except Exception as e:
        print(f"登录请求失败: {e}")
    
    print("\n=== 测试完成 ===")
    print("请检查服务器日志，看是否有中间件的日志输出")

if __name__ == "__main__":
    test_middleware_execution()