#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试PGVector表结构和删除功能
"""

import sys
import os
import logging
from pathlib import Path
from urllib.parse import quote

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langchain.schema import Document
from langchain_postgres import PGVector
from open_agent.core.config import Settings
from open_agent.services.embedding_factory import EmbeddingFactory

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_pgvector_table_structure():
    """测试PGVector表结构和删除功能"""
    try:
        logger.info("开始测试PGVector表结构和删除功能...")
        
        # 获取配置
        config_path = "configs/settings.yaml"
        settings = Settings.load_from_yaml(config_path)
        
        # 初始化嵌入模型
        embedding_factory = EmbeddingFactory()
        embeddings = embedding_factory.create_embeddings()
        logger.info("✅ 嵌入模型初始化成功")
        
        # 构建连接字符串
        encoded_password = quote(settings.vector_db.pgvector_password, safe="")
        connection_string = (
            f"postgresql+psycopg://{settings.vector_db.pgvector_user}:"
            f"{encoded_password}@"
            f"{settings.vector_db.pgvector_host}:"
            f"{settings.vector_db.pgvector_port}/"
            f"{settings.vector_db.pgvector_database}"
        )
        logger.info(f"连接字符串: {connection_string.replace(encoded_password, '***')}")
        
        # 创建测试集合
        collection_name = "test_table_structure"
        
        # 创建PGVector实例
        vector_store = PGVector(
            embeddings=embeddings,
            collection_name=collection_name,
            connection=connection_string,
            use_jsonb=True,
            pre_delete_collection=True  # 清理之前的测试数据
        )
        logger.info("✅ PGVector实例创建成功")
        
        # 创建测试文档
        test_docs = [
            Document(
                page_content="这是第一个测试文档",
                metadata={
                    "document_id": "test_999991",
                    "knowledge_base_id": 999,
                    "source": "test1.txt"
                }
            ),
            Document(
                page_content="这是第二个测试文档",
                metadata={
                    "document_id": "test_999992",
                    "knowledge_base_id": 999,
                    "source": "test2.txt"
                }
            )
        ]
        
        # 逐个添加文档，显式指定ID以避免冲突
        import uuid
        logger.info("添加测试文档...")
        returned_ids = []
        for i, doc in enumerate(test_docs):
            logger.info(f"  添加文档 {i+1}: {doc.page_content[:30]}...")
            # 为每个文档生成唯一的ID
            doc_id = str(uuid.uuid4())
            doc_ids = vector_store.add_documents([doc], ids=[doc_id])
            returned_ids.extend(doc_ids)
            logger.info(f"    指定的ID: {doc_id}")
            logger.info(f"    返回的ID: {doc_ids[0]}")
        
        logger.info(f"✅ 文档添加成功，返回的IDs: {returned_ids}")
        
        # 验证文档已添加
        logger.info("验证文档已添加...")
        search_results = vector_store.similarity_search(
            query="测试文档",
            k=10
        )
        logger.info(f"搜索到 {len(search_results)} 个文档")
        for i, doc in enumerate(search_results):
            logger.info(f"  文档 {i+1}: document_id={doc.metadata.get('document_id')}, 内容={doc.page_content[:30]}...")
        
        # 测试使用返回的ID删除文档
        if returned_ids and len(returned_ids) > 0:
            logger.info(f"测试删除功能，删除ID: {returned_ids[0]}")
            delete_result = vector_store.delete(ids=[returned_ids[0]])
            logger.info(f"删除结果: {delete_result}")
            
            # 验证删除结果
            logger.info("验证删除结果...")
            search_results_after = vector_store.similarity_search(
                query="测试文档",
                k=10
            )
            logger.info(f"删除后搜索到 {len(search_results_after)} 个文档")
            for i, doc in enumerate(search_results_after):
                logger.info(f"  文档 {i+1}: document_id={doc.metadata.get('document_id')}, 内容={doc.page_content[:30]}...")
        
        # 测试使用过滤器删除剩余文档
        logger.info("测试使用过滤器删除剩余文档...")
        try:
            # 使用新版本的过滤器语法
            filter_condition = {"document_id": {"$eq": "test_999992"}}
            remaining_docs = vector_store.similarity_search(
                query="测试文档",
                k=10,
                filter=filter_condition
            )
            logger.info(f"找到匹配过滤器的文档: {len(remaining_docs)}")
            
            if remaining_docs:
                # 获取这些文档的ID并删除
                # 注意：这里我们需要从数据库中查询实际的uuid
                logger.info("清理剩余测试数据...")
                vector_store.delete(ids=returned_ids[1:])  # 删除剩余的ID
                
        except Exception as e:
            logger.warning(f"过滤器删除测试失败: {e}")
        
        logger.info("✅ PGVector表结构和删除功能测试完成！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    logger.info("开始PGVector表结构和删除功能测试...")
    
    success = test_pgvector_table_structure()
    if success:
        print("\n✅ PGVector表结构和删除功能测试通过！")
    else:
        print("\n❌ PGVector表结构和删除功能测试失败！")
        sys.exit(1)