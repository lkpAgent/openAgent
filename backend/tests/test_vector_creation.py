import sys
import os
from pathlib import Path
import logging
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langchain.schema import Document
from chat_agent.core.config import Settings
from chat_agent.services.document_processor import DocumentProcessor
from chat_agent.services.embedding_factory import EmbeddingFactory

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_vector_creation():
    """测试向量创建功能"""
    try:
        logger.info("开始测试向量创建功能...")
        
        # 加载配置
        config_path = Path(__file__).parent / "configs" / "settings.yaml"
        settings = Settings.load_from_yaml(str(config_path))
        
        logger.info(f"向量数据库类型: {settings.vector_db.type}")
        logger.info(f"PostgreSQL主机: {settings.vector_db.pgvector_host}")
        logger.info(f"PostgreSQL端口: {settings.vector_db.pgvector_port}")
        logger.info(f"PostgreSQL数据库: {settings.vector_db.pgvector_database}")
        
        # 初始化文档处理器
        doc_processor = DocumentProcessor()
        logger.info("文档处理器初始化成功")
        
        # 创建测试文档
        test_documents = [
            Document(
                page_content="这是第一个测试文档，用于验证向量存储功能。",
                metadata={
                    "source": "test_doc_1.txt",
                    "title": "测试文档1"
                }
            ),
            Document(
                page_content="这是第二个测试文档，包含不同的内容来测试相似性搜索。",
                metadata={
                    "source": "test_doc_2.txt",
                    "title": "测试文档2"
                }
            ),
            Document(
                page_content="人工智能是计算机科学的一个分支，致力于创建能够执行通常需要人类智能的任务的系统。",
                metadata={
                    "source": "test_doc_3.txt",
                    "title": "AI文档"
                }
            )
        ]
        
        logger.info(f"创建了 {len(test_documents)} 个测试文档")
        
        # 测试向量存储创建
        logger.info("测试创建向量存储...")
        knowledge_base_id = 999  # 使用测试ID
        
        try:
            vector_store = doc_processor.create_vector_store(knowledge_base_id, test_documents)
            logger.info("✅ 向量存储创建成功")
            
            # 测试相似性搜索
            logger.info("测试相似性搜索...")
            search_results = doc_processor.search_similar_documents(
                knowledge_base_id=knowledge_base_id,
                query="人工智能",
                k=2
            )
            
            logger.info(f"搜索结果数量: {len(search_results)}")
            for i, result in enumerate(search_results):
                logger.info(f"结果 {i+1}: {result.get('content', '')[:50]}...")
            
            logger.info("✅ 相似性搜索测试成功")
            
            # 清理测试数据
            logger.info("清理测试数据...")
            try:
                doc_processor.delete_document_from_vector_store(knowledge_base_id, None)
                logger.info("✅ 测试数据清理完成")
            except Exception as e:
                logger.warning(f"清理测试数据时出现警告: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 向量存储操作失败: {e}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        logger.error(f"详细错误信息: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("开始PostgreSQL pgvector向量创建测试...")
    
    success = test_vector_creation()
    if success:
        print("\n✅ PostgreSQL pgvector向量创建测试通过！")
    else:
        print("\n❌ PostgreSQL pgvector向量创建测试失败！")
        sys.exit(1)