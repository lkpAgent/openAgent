#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langchain.schema import Document
from chat_agent.core.config import Settings
from chat_agent.services.document_processor import DocumentProcessor
from chat_agent.services.embedding_factory import EmbeddingFactory

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_document_processor_pgvector():
    """测试文档处理器的pgvector集成"""
    try:
        logger.info("开始测试文档处理器的pgvector集成...")
        
        # 获取配置
        config_path = "configs/settings.yaml"
        settings = Settings.load_from_yaml(config_path)
        logger.info(f"向量数据库类型: {settings.vector_db.type}")
        
        if settings.vector_db.type != "pgvector":
            logger.error("配置文件中向量数据库类型不是pgvector")
            return False
        
        # 初始化文档处理器
        doc_processor = DocumentProcessor()
        logger.info("文档处理器初始化成功")
        
        # 创建测试文档
        test_documents = [
            Document(
                page_content="这是第一个测试文档，包含关于人工智能的内容。",
                metadata={
                    "source": "test_doc_1.txt",
                    "document_id": "test_doc_1",
                    "chunk_id": "test_doc_1_chunk_0",
                    "knowledge_base_id": 1
                }
            ),
            Document(
                page_content="这是第二个测试文档，讨论机器学习算法。",
                metadata={
                    "source": "test_doc_2.txt",
                    "document_id": "test_doc_2",
                    "chunk_id": "test_doc_2_chunk_0",
                    "knowledge_base_id": 1
                }
            ),
            Document(
                page_content="这是第三个测试文档，介绍深度学习技术。",
                metadata={
                    "source": "test_doc_3.txt",
                    "document_id": "test_doc_3",
                    "chunk_id": "test_doc_3_chunk_0",
                    "knowledge_base_id": 1
                }
            )
        ]
        
        # 测试创建向量存储
        logger.info("测试创建向量存储...")
        knowledge_base_id = 1
        vector_store = doc_processor.create_vector_store(knowledge_base_id, test_documents)
        
        if vector_store:
            logger.info("✅ 向量存储创建成功")
        else:
            logger.error("❌ 向量存储创建失败")
            return False
        
        # 测试添加文档到向量存储
        logger.info("测试添加文档到向量存储...")
        additional_docs = [
            Document(
                page_content="这是额外添加的文档，关于自然语言处理。",
                metadata={
                    "source": "additional_doc.txt",
                    "document_id": "additional_doc",
                    "chunk_id": "additional_doc_chunk_0",
                    "knowledge_base_id": 1
                }
            )
        ]
        
        success = doc_processor.add_documents_to_vector_store(additional_docs, knowledge_base_id)
        if success:
            logger.info("✅ 文档添加成功")
        else:
            logger.error("❌ 文档添加失败")
            return False
        
        # 测试相似性搜索
        logger.info("测试相似性搜索...")
        query = "人工智能和机器学习"
        search_results = doc_processor.search_similar_documents(query, knowledge_base_id, k=3)
        
        if search_results:
            logger.info(f"✅ 相似性搜索成功，返回 {len(search_results)} 个结果")
            for i, doc in enumerate(search_results):
                logger.info(f"  结果 {i+1}: {doc.page_content[:50]}...")
                logger.info(f"  元数据: {doc.metadata}")
        else:
            logger.error("❌ 相似性搜索失败")
            return False
        
        # 测试获取文档分段
        logger.info("测试获取文档分段...")
        document_id = "test_doc_1"
        chunks = doc_processor.get_document_chunks(document_id, knowledge_base_id)
        
        if chunks:
            logger.info(f"✅ 获取文档分段成功，返回 {len(chunks)} 个分段")
            for i, chunk in enumerate(chunks):
                logger.info(f"  分段 {i+1}: {chunk.page_content[:50]}...")
        else:
            logger.info("⚠️ 未找到指定文档的分段（可能是正常情况）")
        
        # 测试删除文档
        logger.info("测试删除文档...")
        delete_success = doc_processor.delete_document_from_vector_store("additional_doc", knowledge_base_id)
        
        if delete_success:
            logger.info("✅ 文档删除成功")
        else:
            logger.info("⚠️ 文档删除操作完成（可能文档不存在）")
        
        logger.info("✅ 文档处理器pgvector集成测试完成！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 文档处理器pgvector集成测试失败: {e}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    logger.info("开始文档处理器pgvector集成测试...")
    
    success = test_document_processor_pgvector()
    if success:
        print("\n✅ 文档处理器pgvector集成测试通过！")
    else:
        print("\n❌ 文档处理器pgvector集成测试失败！")
        sys.exit(1)