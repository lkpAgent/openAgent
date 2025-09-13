#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langchain.schema import Document
from open_agent.core.config import Settings
from open_agent.services.document_processor import DocumentProcessor

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_document_upload_simulation():
    """模拟文档上传过程，测试向量创建功能"""
    try:
        logger.info("开始模拟文档上传测试...")
        
        # 加载配置
        config_path = "configs/settings.yaml"
        settings = Settings.load_from_yaml(config_path)
        logger.info(f"向量数据库类型: {settings.vector_db.type}")
        
        if settings.vector_db.type != "pgvector":
            logger.error("配置文件中向量数据库类型不是pgvector")
            return False
        
        # 初始化文档处理器
        doc_processor = DocumentProcessor()
        logger.info("文档处理器初始化成功")
        
        # 模拟文档内容（类似实际上传的文档）
        test_documents = [
            Document(
                page_content="人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。",
                metadata={
                    "source": "ai_introduction.txt",
                    "title": "人工智能简介",
                    "page": 1
                }
            ),
            Document(
                page_content="机器学习是人工智能的一个重要分支，它是一种通过算法使计算机系统能够自动学习和改进的技术。机器学习算法通过分析大量数据来识别模式，并使用这些模式来对新数据进行预测或决策。",
                metadata={
                    "source": "machine_learning.txt", 
                    "title": "机器学习概述",
                    "page": 1
                }
            ),
            Document(
                page_content="深度学习是机器学习的一个子集，它模仿人脑神经网络的结构和功能。深度学习使用多层神经网络来学习数据的复杂模式，在图像识别、语音识别、自然语言处理等领域取得了突破性进展。",
                metadata={
                    "source": "deep_learning.txt",
                    "title": "深度学习技术", 
                    "page": 1
                }
            )
        ]
        
        # 测试知识库ID和文档ID
        knowledge_base_id = 999  # 测试知识库
        document_id = 1001  # 测试文档
        
        logger.info(f"开始为知识库 {knowledge_base_id} 创建向量存储...")
        
        # 创建向量存储（模拟文档上传时的向量创建过程）
        vector_store_result = doc_processor.create_vector_store(
            knowledge_base_id=knowledge_base_id,
            documents=test_documents,
            document_id=document_id
        )
        
        if vector_store_result:
            logger.info(f"✅ 向量存储创建成功: {vector_store_result}")
        else:
            logger.error("❌ 向量存储创建失败")
            return False
        
        # 测试相似性搜索
        logger.info("测试相似性搜索功能...")
        search_query = "什么是人工智能？"
        search_results = doc_processor.search_similar_documents(
            knowledge_base_id=knowledge_base_id,
            query=search_query,
            k=3
        )
        
        if search_results:
            logger.info(f"✅ 相似性搜索成功，找到 {len(search_results)} 个结果")
            for i, result in enumerate(search_results):
                logger.info(f"  结果 {i+1}: 相似度={result.get('similarity_score', 'N/A'):.4f}")
                logger.info(f"    内容预览: {result['content'][:50]}...")
        else:
            logger.warning("⚠️ 相似性搜索未返回结果")
        
        # 测试添加更多文档
        logger.info("测试添加额外文档...")
        additional_docs = [
            Document(
                page_content="自然语言处理（Natural Language Processing，NLP）是人工智能和语言学领域的分支学科。它研究能实现人与计算机之间用自然语言进行有效通信的各种理论和方法。",
                metadata={
                    "source": "nlp_overview.txt",
                    "title": "自然语言处理",
                    "page": 1
                }
            )
        ]
        
        doc_processor.add_documents_to_vector_store(
            knowledge_base_id=knowledge_base_id,
            documents=additional_docs,
            document_id=document_id + 1
        )
        logger.info("✅ 额外文档添加成功")
        
        # 再次测试搜索
        logger.info("测试添加文档后的搜索功能...")
        search_results_2 = doc_processor.search_similar_documents(
            knowledge_base_id=knowledge_base_id,
            query="自然语言处理是什么？",
            k=2
        )
        
        if search_results_2:
            logger.info(f"✅ 第二次搜索成功，找到 {len(search_results_2)} 个结果")
            for i, result in enumerate(search_results_2):
                logger.info(f"  结果 {i+1}: 相似度={result.get('similarity_score', 'N/A'):.4f}")
                logger.info(f"    内容预览: {result['content'][:50]}...")
        
        # 清理测试数据
        logger.info("清理测试数据...")
        try:
            doc_processor.delete_document_from_vector_store(
                knowledge_base_id=knowledge_base_id,
                document_id=document_id
            )
            doc_processor.delete_document_from_vector_store(
                knowledge_base_id=knowledge_base_id,
                document_id=document_id + 1
            )
            logger.info("✅ 测试数据清理完成")
        except Exception as e:
            logger.warning(f"⚠️ 清理测试数据时出现警告: {e}")
        
        logger.info("✅ 文档上传模拟测试完成！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 文档上传模拟测试失败: {e}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    logger.info("开始文档上传模拟测试...")
    
    success = test_document_upload_simulation()
    if success:
        print("\n✅ 文档上传模拟测试通过！向量创建功能正常工作。")
    else:
        print("\n❌ 文档上传模拟测试失败！")
        sys.exit(1)