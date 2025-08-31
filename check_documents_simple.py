#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import create_engine, text
from chat_agent.core.config import settings

def check_documents_simple():
    """直接查询数据库检查文档"""
    try:
        # 创建数据库连接
        engine = create_engine(settings.database.url)
        
        with engine.connect() as conn:
            # 查询最近的文档
            result = conn.execute(text("""
                SELECT id, filename, original_filename, file_type, 
                       is_processed, chunk_count, created_at
                FROM documents 
                ORDER BY id DESC 
                LIMIT 5
            """))
            
            print("最近上传的文档:")
            print("-" * 80)
            
            for row in result:
                print(f"ID: {row.id}")
                print(f"文件名: {row.filename}")
                print(f"原始文件名: {row.original_filename}")
                print(f"文件类型: {row.file_type}")
                print(f"处理状态: {'已处理' if row.is_processed else '未处理'}")
                print(f"分段数量: {row.chunk_count}")
                print(f"创建时间: {row.created_at}")
                print("-" * 80)
                
    except Exception as e:
        print(f"查询失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_documents_simple()