#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
from chat_agent.core.context import UserContext
from chat_agent.db.database import get_db_session
from chat_agent.models.user import User
from chat_agent.services.auth import AuthService

def test_user_context():
    """测试用户上下文功能"""
    base_url = "http://localhost:8001"
    
    print("=== 测试用户上下文功能 ===")
    
    # 1. 测试登录
    print("\n1. 测试用户登录...")
    login_data = {
        "email": "test@example.com",
        "password": "123456"
    }
    
    try:
        response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        print(f"登录响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            login_result = response.json()
            token = login_result.get("access_token")
            print(f"登录成功，获得token: {token[:50]}...")
            
            # 2. 测试带token的API调用
            print("\n2. 测试带token的API调用...")
            headers = {"Authorization": f"Bearer {token}"}
            
            # 测试获取用户信息
            user_response = requests.get(f"{base_url}/api/auth/me", headers=headers)
            print(f"获取用户信息响应状态码: {user_response.status_code}")
            
            if user_response.status_code == 200:
                user_info = user_response.json()
                print(f"用户信息: {json.dumps(user_info, indent=2, ensure_ascii=False)}")
            else:
                print(f"获取用户信息失败: {user_response.text}")
            
            # 3. 测试token验证
            print("\n3. 测试token验证...")
            payload = AuthService.verify_token(token)
            if payload:
                print(f"Token验证成功，payload: {payload}")
                username = payload.get("sub")
                print(f"从token中提取的用户名: {username}")
                
                # 4. 测试数据库用户查询
                print("\n4. 测试数据库用户查询...")
                db = get_db_session()
                try:
                    user = db.query(User).filter(User.username == username).first()
                    if user:
                        print(f"找到用户: {user.username}, ID: {user.id}, 活跃状态: {user.is_active}")
                        
                        # 5. 测试UserContext设置和获取
                        print("\n5. 测试UserContext设置和获取...")
                        UserContext.set_current_user(user)
                        current_user = UserContext.get_current_user()
                        
                        if current_user:
                            print(f"UserContext.get_current_user()成功: {current_user.username}")
                            print(f"用户ID: {UserContext.get_current_user_id()}")
                        else:
                            print("❌ UserContext.get_current_user()返回None")
                        
                        UserContext.clear_current_user()
                        print("UserContext已清除")
                    else:
                        print(f"❌ 数据库中未找到用户: {username}")
                finally:
                    db.close()
            else:
                print("❌ Token验证失败")
        else:
            print(f"登录失败: {response.text}")
            
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_user_context()