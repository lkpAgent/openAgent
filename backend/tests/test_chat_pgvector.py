#!/usr/bin/env python3
"""测试修改后的聊天功能是否能正常使用PGVector进行知识库问答"""

import sys
import os
import asyncio
from sqlalchemy.orm import Session

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from open_agent.db.database import get_db
from open_agent.services.knowledge_chat import KnowledgeChatService
from open_agent.services.conversation import ConversationService
from open_agent.services.document_processor import get_document_processor
from open_agent.utils.logger import get_logger
from open_agent.core.config import settings
from langchain.schema import Document

logger = get_logger("test_chat_pgvector")

async def test_chat_with_pgvector():
    """测试聊天功能使用PGVector"""
    try:
        # 获取数据库会话
        db = next(get_db())
        
        # 初始化服务
        knowledge_chat_service = KnowledgeChatService(db)
        conversation_service = ConversationService(db)
        doc_processor = get_document_processor()
        
        logger.info("开始测试聊天功能使用PGVector...")
        
        # 测试知识库ID
        knowledge_base_id = 999
        
        # 1. 首先添加一些测试文档到知识库
        logger.info("添加测试文档到知识库...")
        test_documents = [
            Document(
                page_content="Python是一种高级编程语言，具有简洁的语法和强大的功能。它广泛应用于Web开发、数据科学、人工智能等领域。",
                metadata={
                    "source": "python_intro.txt",
                    "filename": "python_intro.txt"
                }
            ),
            Document(
                page_content="机器学习是人工智能的一个重要分支，通过算法让计算机从数据中学习模式。常见的机器学习算法包括线性回归、决策树、神经网络等。",
                metadata={
                    "source": "ml_intro.txt",
                    "filename": "ml_intro.txt"
                }
            ),
            Document(
                page_content="深度学习是机器学习的一个子领域，使用多层神经网络来学习数据的复杂模式。它在图像识别、自然语言处理等任务中表现出色。",
                metadata={
                    "source": "dl_intro.txt",
                    "filename": "dl_intro.txt"
                }
            )
        ]
        
        # 添加文档到向量存储
        doc_processor.add_documents_to_vector_store(knowledge_base_id, test_documents, document_id=888)
        logger.info("测试文档添加完成")
        
        # 2. 创建一个测试对话
        logger.info("创建测试对话...")
        # 这里我们模拟一个对话ID，实际应用中应该通过API创建
        conversation_id = 1  # 假设存在ID为1的对话
        
        # 3. 测试向量存储获取
        logger.info("测试向量存储获取...")
        vector_store = knowledge_chat_service._get_vector_store(knowledge_base_id)
        if vector_store:
            logger.info(f"✅ 成功获取向量存储: {type(vector_store).__name__}")
            
            # 测试相似性搜索
            logger.info("测试相似性搜索...")
            search_results = vector_store.similarity_search("什么是Python", k=2)
            logger.info(f"搜索到 {len(search_results)} 个相关文档")
            for i, doc in enumerate(search_results):
                logger.info(f"  文档 {i+1}: {doc.page_content[:50]}...")
        else:
            logger.error("❌ 无法获取向量存储")
            return False
        
        # 4. 测试知识库搜索功能
        logger.info("测试知识库搜索功能...")
        search_results = await knowledge_chat_service.search_knowledge_base(
            knowledge_base_id=knowledge_base_id,
            query="机器学习是什么",
            k=3
        )
        
        if search_results:
            logger.info(f"✅ 知识库搜索成功，找到 {len(search_results)} 个相关文档")
            for i, result in enumerate(search_results):
                logger.info(f"  结果 {i+1}: 相似度={result.get('similarity_score', 'N/A'):.4f}, 内容={result['content'][:50]}...")
        else:
            logger.warning("知识库搜索未找到相关文档")
        
        # 5. 测试流式聊天功能（模拟）
        logger.info("测试流式聊天功能...")
        test_message = "请介绍一下Python编程语言"
        
        try:
            # 由于我们没有真实的对话记录，这里只测试向量存储部分
            # 实际的聊天功能需要完整的对话上下文
            logger.info("模拟聊天查询...")
            
            # 获取相关文档
            retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 3})
            relevant_docs = retriever.get_relevant_documents(test_message)
            
            logger.info(f"✅ 检索到 {len(relevant_docs)} 个相关文档用于回答")
            for i, doc in enumerate(relevant_docs):
                logger.info(f"  相关文档 {i+1}: {doc.page_content[:50]}...")
                
        except Exception as e:
            logger.error(f"❌ 流式聊天测试失败: {e}")
            return False
        
        # 6. 清理测试数据
        logger.info("清理测试数据...")
        doc_processor.delete_document_from_vector_store(knowledge_base_id, 888)
        logger.info("测试数据清理完成")
        
        logger.info("🎉 聊天功能PGVector集成测试完成！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试过程中发生错误: {str(e)}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        return False
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    success = asyncio.run(test_chat_with_pgvector())
    if success:
        print("\n✅ 聊天功能PGVector集成测试通过！")
    else:
        print("\n❌ 聊天功能PGVector集成测试失败！")
        sys.exit(1)