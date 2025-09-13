#!/usr/bin/env python3
"""
重置数据库用户并创建demo用户
"""

from open_agent.models.user import User
from open_agent.services.auth import AuthService
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from open_agent.core.config import settings

def reset_users():
    """清空所有用户并创建demo用户"""
    # 创建数据库连接
    engine = create_engine(settings.database.url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    try:
        # 删除所有用户
        print("正在删除所有用户...")
        # deleted_count = db.query(User).delete()
        # print(f"已删除 {deleted_count} 个用户")
        
        # 创建demo用户
        print("正在创建demo用户...")
        demo_user = User(
            username="demo1",
            email="demo1@example.com",
            hashed_password=AuthService.get_password_hash("123456"),
            is_active=True
        )
        
        db.add(demo_user)
        db.commit()
        
        print("Demo用户创建成功!")
        print("用户名: demo1")
        print("邮箱: demo1@example.com")
        print("密码: 123456")
        
    except Exception as e:
        print(f"操作失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_users()