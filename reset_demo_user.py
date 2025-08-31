#!/usr/bin/env python3
"""
重置数据库用户并创建demo用户
"""

import sys
import os
from pathlib import Path

# 添加backend目录到Python路径
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# 设置环境变量
os.environ.setdefault('PYTHONPATH', str(backend_path))

try:
    from chat_agent.db.models import User
    from chat_agent.core.security import get_password_hash
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from chat_agent.core.config import settings
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在backend目录下运行此脚本")
    sys.exit(1)

def reset_users():
    """清空所有用户并创建demo用户"""
    # 创建数据库连接
    engine = create_engine(settings.database.url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    try:
        # 删除所有用户
        print("正在删除所有用户...")
        deleted_count = db.query(User).delete()
        print(f"已删除 {deleted_count} 个用户")
        
        # 创建demo用户
        print("正在创建demo用户...")
        demo_user = User(
            username="demo",
            email="demo@example.com",
            hashed_password=get_password_hash("123456"),
            is_active=True
        )
        
        db.add(demo_user)
        db.commit()
        
        print("Demo用户创建成功!")
        print("用户名: demo")
        print("邮箱: demo@example.com")
        print("密码: 123456")
        
    except Exception as e:
        print(f"操作失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_users()