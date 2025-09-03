#!/usr/bin/env python3
"""
测试聊天API
"""

import requests
import json

def test_chat_api():
    # 1. 登录获取token
    login_url = "http://localhost:8000/api/auth/login"
    login_data = {
        "email": "demo@example.com",
        "password": "123456"
    }
    
    print("正在登录...")
    login_response = requests.post(login_url, json=login_data)
    
    if login_response.status_code != 200:
        print(f"登录失败: {login_response.status_code}")
        print(login_response.text)
        return
    
    token = login_response.json()["access_token"]
    print(f"登录成功，获取到token: {token[:20]}...")
    
    # 2. 测试聊天API
    conversation_id = 1
    chat_url = f"http://localhost:8000/api/chat/conversations/{conversation_id}/chat/stream"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    chat_data = {
        "message": "测试知识库对话"
    }
    
    print("正在发送聊天请求...")
    try:
        chat_response = requests.post(chat_url, json=chat_data, headers=headers)
        print(f"响应状态码: {chat_response.status_code}")
        print(f"响应内容: {chat_response.text}")
    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    test_chat_api()