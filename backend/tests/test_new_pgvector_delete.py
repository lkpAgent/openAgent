#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新版本PGVector删除功能
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from langchain_postgres import PGVector
from langchain.schema import Document
from open_agent.core.config import settings
from open_agent.services.embedding_factory import EmbeddingFactory
from urllib.parse import quote

def test_pgvector_delete():
    """测试新版本PGVector的删除功能"""
    print("开始测试新版本PGVector删除功能...")
    
    # 初始化embedding
    embeddings = EmbeddingFactory.create_embeddings()
    
    # 构建连接字符串
    connection_string = (
        f"postgresql+psycopg://{settings.vector_db.pgvector_user}:"
        f"{quote(settings.vector_db.pgvector_password)}@"
        f"{settings.vector_db.pgvector_host}:"
        f"{settings.vector_db.pgvector_port}/"
        f"{settings.vector_db.pgvector_database}"
    )
    
    # 测试集合名称
    collection_name = "test_delete_collection"
    
    try:
        # 创建PGVector实例
        vector_store = PGVector(
            connection=connection_string,
            embeddings=embeddings,
            collection_name=collection_name,
            use_jsonb=True
        )
        
        print(f"成功连接到PGVector，集合名称: {collection_name}")
        
        # 创建测试文档
        test_documents = [
            Document(
                page_content="这是第一个测试文档的内容",
                metadata={
                    "document_id": "test_doc_1",
                    "knowledge_base_id": 999,
                    "chunk_id": "999_test_doc_1_0",
                    "chunk_index": 0
                }
            ),
            Document(
                page_content="这是第二个测试文档的内容",
                metadata={
                    "document_id": "test_doc_1",
                    "knowledge_base_id": 999,
                    "chunk_id": "999_test_doc_1_1",
                    "chunk_index": 1
                }
            ),
            Document(
                page_content="这是另一个文档的内容",
                metadata={
                    "document_id": "test_doc_2",
                    "knowledge_base_id": 999,
                    "chunk_id": "999_test_doc_2_0",
                    "chunk_index": 0
                }
            )
        ]
        
        # 添加测试文档
        print("添加测试文档...")
        vector_store.add_documents(test_documents)
        print(f"成功添加 {len(test_documents)} 个测试文档")
        
        # 验证文档已添加
        print("\n验证文档已添加...")
        search_results = vector_store.similarity_search(
            query="测试文档",
            k=10,
            filter={"knowledge_base_id": {"$eq": 999}}
        )
        print(f"搜索到 {len(search_results)} 个文档")
        for i, doc in enumerate(search_results):
            print(f"  文档 {i+1}: document_id={doc.metadata.get('document_id')}, 内容={doc.page_content[:30]}...")
        
        # 测试删除功能
        print("\n测试删除功能...")
        print("删除 document_id='test_doc_1' 的所有文档")
        
        # 使用新版本的过滤器语法删除
        filter_condition = {"document_id": {"$eq": "test_doc_1"}}
        vector_store.delete(filter=filter_condition)
        print("删除操作完成")
        
        # 验证删除结果
        print("\n验证删除结果...")
        remaining_results = vector_store.similarity_search(
            query="测试文档",
            k=10,
            filter={"knowledge_base_id": {"$eq": 999}}
        )
        print(f"删除后剩余 {len(remaining_results)} 个文档")
        for i, doc in enumerate(remaining_results):
            print(f"  剩余文档 {i+1}: document_id={doc.metadata.get('document_id')}, 内容={doc.page_content[:30]}...")
        
        # 检查是否只剩下test_doc_2
        remaining_doc_ids = [doc.metadata.get('document_id') for doc in remaining_results]
        if len(remaining_results) == 1 and 'test_doc_2' in remaining_doc_ids:
            print("\n✅ 删除功能测试成功！只剩下预期的文档")
        else:
            print(f"\n❌ 删除功能测试失败！预期只剩下test_doc_2，实际剩余: {remaining_doc_ids}")
        
        # 清理测试数据
        print("\n清理测试数据...")
        vector_store.delete(filter={"knowledge_base_id": {"$eq": 999}})
        print("测试数据清理完成")
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_pgvector_delete()
    if success:
        print("\n🎉 新版本PGVector删除功能测试通过！")
    else:
        print("\n💥 新版本PGVector删除功能测试失败！")
        sys.exit(1)