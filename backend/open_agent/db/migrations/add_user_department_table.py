"""Add user_department association table migration."""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import asyncpg
from open_agent.core.config import get_settings

async def create_user_department_table():
    """Create user_departments association table."""
    settings = get_settings()
    database_url = settings.database.url
    
    print(f"Database URL: {database_url}")
    
    try:
        # 解析PostgreSQL连接URL
        # postgresql://user:password@host:port/database
        url_parts = database_url.replace('postgresql://', '').split('/')
        db_name = url_parts[1] if len(url_parts) > 1 else 'postgres'
        user_host = url_parts[0].split('@')
        user_pass = user_host[0].split(':')
        host_port = user_host[1].split(':')
        
        user = user_pass[0]
        password = user_pass[1] if len(user_pass) > 1 else ''
        host = host_port[0]
        port = int(host_port[1]) if len(host_port) > 1 else 5432
        
        # 连接PostgreSQL数据库
        conn = await asyncpg.connect(
            user=user,
            password=password,
            database=db_name,
            host=host,
            port=port
        )
        
        # 创建user_departments表
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS user_departments (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            department_id INTEGER NOT NULL,
            is_primary BOOLEAN NOT NULL DEFAULT true,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (department_id) REFERENCES departments (id) ON DELETE CASCADE
        );
        """
        
        await conn.execute(create_table_sql)
        
        # 创建索引
        create_indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_user_departments_user_id ON user_departments (user_id);",
            "CREATE INDEX IF NOT EXISTS idx_user_departments_department_id ON user_departments (department_id);",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_user_departments_unique ON user_departments (user_id, department_id);"
        ]
        
        for index_sql in create_indexes_sql:
            await conn.execute(index_sql)
        
        print("User departments table created successfully")
        
    except Exception as e:
        print(f"Error creating user departments table: {e}")
        raise
    finally:
        if 'conn' in locals():
            await conn.close()


if __name__ == "__main__":
    asyncio.run(create_user_department_table())