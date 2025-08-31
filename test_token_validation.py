#!/usr/bin/env python3
"""测试token验证功能"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "backend"))

from chat_agent.db.database import get_db_session
from chat_agent.services.auth import AuthService
from chat_agent.models.user import User
import jwt
from chat_agent.core.config import settings

def test_token_validation():
    """测试token验证流程"""
    print("开始测试token验证...")
    
    # 1. 获取用户
    db = get_db_session()
    try:
        user = db.query(User).filter(User.email == "demo@example.com").first()
        if not user:
            print("❌ 用户不存在")
            return
        
        print(f"✅ 找到用户: {user.username} ({user.email})")
        
        # 2. 创建token
        token = AuthService.create_access_token(data={"sub": user.email})
        print(f"✅ Token创建成功: {token[:50]}...")
        
        # 3. 验证token
        payload = AuthService.verify_token(token)
        if payload:
            print(f"✅ Token验证成功: {payload}")
            
            # 4. 通过email查找用户
            email = payload.get("sub")
            found_user = db.query(User).filter(User.email == email).first()
            if found_user:
                print(f"✅ 通过email找到用户: {found_user.username} ({found_user.email})")
            else:
                print(f"❌ 通过email未找到用户: {email}")
        else:
            print("❌ Token验证失败")
            
        # 5. 手动解析token
        try:
            decoded = jwt.decode(token, settings.security.secret_key, algorithms=[settings.security.algorithm])
            print(f"✅ 手动解析token成功: {decoded}")
        except Exception as e:
            print(f"❌ 手动解析token失败: {e}")
            
    finally:
        db.close()

if __name__ == "__main__":
    test_token_validation()