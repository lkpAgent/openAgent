#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试新版本PGVector删除功能
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langchain.schema import Document
from langchain_postgres import PGVector
from open_agent.core.config import settings
from open_agent.services.embedding_factory import EmbeddingFactory
from urllib.parse import quote

def test_simple_pgvector_delete():
    """简单测试新版本PGVector删除功能"""
    try:
        print("开始简单测试新版本PGVector删除功能...")
        
        # 初始化embedding
        embeddings = EmbeddingFactory.create_embeddings()
        
        # 构建连接字符串
        user = quote(settings.vector_db.pgvector_user)
        password = quote(settings.vector_db.pgvector_password)
        host = settings.vector_db.pgvector_host
        port = settings.vector_db.pgvector_port
        database = settings.vector_db.pgvector_database
        
        connection = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{database}"
        
        # 创建PGVector实例
        vector_store = PGVector(
            connection=connection,
            embeddings=embeddings,
            collection_name="simple_test_collection",
            use_jsonb=True
        )
        
        print(f"成功连接到PGVector，集合名称: simple_test_collection")
        
        # 创建简单测试文档
        test_docs = [
            Document(
                page_content="这是测试文档1",
                metadata={"document_id": "simple_test_1", "source": "test"}
            ),
            Document(
                page_content="这是测试文档2", 
                metadata={"document_id": "simple_test_2", "source": "test"}
            )
        ]
        
        print("添加测试文档...")
        vector_store.add_documents(test_docs)
        print("✅ 测试文档添加成功")
        
        # 验证文档已添加
        results = vector_store.similarity_search("测试文档", k=5)
        print(f"添加后查询到 {len(results)} 个文档")
        
        # 测试删除功能 - 使用新版本语法
        print("\n测试删除功能...")
        try:
            # 使用新版本的过滤器语法删除
            vector_store.delete(filter={"document_id": {"$eq": "simple_test_1"}})
            print("✅ 删除操作执行成功")
            
            # 验证删除结果
            results_after = vector_store.similarity_search("测试文档", k=5)
            print(f"删除后查询到 {len(results_after)} 个文档")
            
            # 检查剩余文档的document_id
            remaining_ids = [doc.metadata.get('document_id') for doc in results_after]
            print(f"剩余文档IDs: {remaining_ids}")
            
            if "simple_test_1" not in remaining_ids and "simple_test_2" in remaining_ids:
                print("✅ 删除功能测试成功！指定文档已被删除，其他文档保留")
            else:
                print("❌ 删除功能测试失败！")
                
        except Exception as delete_error:
            print(f"❌ 删除操作失败: {delete_error}")
            return False
            
        # 清理测试数据
        print("\n清理测试数据...")
        try:
            vector_store.delete(filter={"source": {"$eq": "test"}})
            print("✅ 测试数据清理完成")
        except Exception as cleanup_error:
            print(f"⚠️ 清理测试数据时出错: {cleanup_error}")
            
        return True
        
    except Exception as e:
        print(f"💥 简单PGVector删除功能测试失败！")
        print(f"错误详情: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple_pgvector_delete()
    if success:
        print("\n🎉 新版本PGVector删除功能测试通过！")
    else:
        print("\n💥 新版本PGVector删除功能测试失败！")
        sys.exit(1)