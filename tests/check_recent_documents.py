#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from chat_agent.db.database import get_db
from chat_agent.models.knowledge_base import Document
from sqlalchemy import desc

def check_recent_documents():
    """检查最近上传的文档状态"""
    try:
        db = next(get_db())
        
        # 获取最近5个文档
        recent_docs = db.query(Document).order_by(desc(Document.id)).limit(5).all()
        
        print("最近上传的文档:")
        print("-" * 80)
        
        for doc in recent_docs:
            print(f"ID: {doc.id}")
            print(f"文件名: {doc.filename}")
            print(f"原始文件名: {doc.original_filename}")
            print(f"文件类型: {doc.file_type}")
            print(f"处理状态: {'已处理' if doc.is_processed else '未处理'}")
            print(f"分段数量: {doc.chunk_count}")
            print(f"创建时间: {doc.created_at}")
            if doc.processing_error:
                print(f"处理错误: {doc.processing_error}")
            print("-" * 80)
            
        db.close()
        
    except Exception as e:
        print(f"查询失败: {e}")

if __name__ == "__main__":
    check_recent_documents()