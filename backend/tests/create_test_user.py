#!/usr/bin/env python3
"""Create a test user for login testing."""

import sys
import os


def find_project_root():
    """智能查找项目根目录"""
    current_dir = os.path.abspath(os.getcwd())
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 可能的项目根目录位置
    possible_roots = [
        current_dir,  # 当前工作目录
        script_dir,  # 脚本所在目录
        os.path.dirname(script_dir),  # 脚本父目录
        os.path.dirname(os.path.dirname(script_dir))  # 脚本祖父目录
    ]

    for root in possible_roots:
        backend_dir = os.path.join(root, 'backend')
        if os.path.exists(backend_dir) and os.path.exists(os.path.join(backend_dir, 'open_agent')):
            return root, backend_dir

    raise FileNotFoundError("无法找到项目根目录和backend目录")


# 查找项目根目录和backend目录
project_root, backend_dir = find_project_root()

# 添加backend目录到Python路径
sys.path.insert(0, backend_dir)

# 保存原始工作目录
original_cwd = os.getcwd()

# 设置工作目录为backend，以便找到.env文件
os.chdir(backend_dir)

from open_agent.db.database import get_db, init_db
from open_agent.services.user import UserService
from open_agent.utils.schemas import UserCreate
import asyncio


async def create_database_tables():
    """Create all database tables using SQLAlchemy models."""
    try:
        await init_db()
        print('Database tables created successfully using SQLAlchemy models')
        return True
    except Exception as e:
        print(f'Error creating database tables: {e}')
        return False


async def create_test_user():
    """Create a test user."""
    # First, create all database tables using SQLAlchemy models
    if not await create_database_tables():
        print('Failed to create database tables')
        return None

    db = next(get_db())

    try:
        user_service = UserService(db)

        # Create test user
        user_data = UserCreate(
            username='test1',
            email='test1@example.com',
            password='123456',
            full_name='Test User 1'
        )

        # Check if user already exists
        existing_user = user_service.get_user_by_email(user_data.email)
        if existing_user:
            print(f'User already exists: {existing_user.username} ({existing_user.email})')
            return existing_user

        # Create new user
        user = user_service.create_user(user_data)
        print(f'Created user: {user.username} ({user.email})')
        return user
    except Exception as e:
        print(f'Error creating user: {e}')
        return None
    finally:
        db.close()


if __name__ == "__main__":
    try:
        asyncio.run(create_test_user())
    finally:
        # 恢复原始工作目录
        os.chdir(original_cwd)