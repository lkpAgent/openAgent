#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chat_agent.core.config import get_settings
import psycopg2
from urllib.parse import urlparse

def test_db_connection():
    """测试数据库连接"""
    try:
        # 获取配置
        config = get_settings()
        db_url = config.database.url
        
        print(f"原始数据库URL: {db_url}")
        
        # 解析URL
        parsed = urlparse(db_url)
        print(f"解析后的URL组件:")
        print(f"  scheme: {parsed.scheme}")
        print(f"  username: {parsed.username}")
        print(f"  password: {parsed.password}")
        print(f"  hostname: {parsed.hostname}")
        print(f"  port: {parsed.port}")
        print(f"  database: {parsed.path[1:]}")
        
        # 尝试直接连接
        print("\n尝试直接连接数据库...")
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path[1:]
        )
        
        print("数据库连接成功！")
        
        # 测试基本查询
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"PostgreSQL版本: {version[0]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"连接失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_db_connection()