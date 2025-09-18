#!/usr/bin/env python3
"""Add missing columns to users table."""

import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置工作目录为backend，以便找到.env文件
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from open_agent.db.database import get_db, init_db
from sqlalchemy import text
import asyncio


async def add_missing_columns():
    """Add missing columns to users table."""
    try:
        # 初始化数据库
        await init_db()
        
        # 获取数据库会话
        db = next(get_db())
        
        # 添加缺失的列
        try:
            db.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS department_id INTEGER'))
            print("Added department_id column")
        except Exception as e:
            print(f"department_id column might already exist: {e}")
        
        try:
            db.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(255)'))
            print("Added avatar_url column")
        except Exception as e:
            print(f"avatar_url column might already exist: {e}")
        
        try:
            db.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS bio TEXT'))
            print("Added bio column")
        except Exception as e:
            print(f"bio column might already exist: {e}")
        
        db.commit()
        print("Successfully added missing columns to users table")
        
    except Exception as e:
        print(f"Error adding columns: {e}")
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.rollback()
    finally:
        if 'db' in locals():
            db.close()


if __name__ == "__main__":
    asyncio.run(add_missing_columns())