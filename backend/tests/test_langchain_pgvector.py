import sys
import os
from pathlib import Path
import logging
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langchain.schema import Document
from langchain_community.vectorstores.pgvector import PGVector
from chat_agent.core.config import Settings
from chat_agent.services.embedding_factory import EmbeddingFactory

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_langchain_pgvector():
    """测试LangChain PGVector集成"""
    try:
        logger.info("开始测试LangChain PGVector集成...")
        
        # 加载配置
        config_path = Path(__file__).parent / "configs" / "settings.yaml"
        settings = Settings.load_from_yaml(str(config_path))
        
        logger.info(f"配置信息:")
        logger.info(f"  主机: {settings.vector_db.pgvector_host}")
        logger.info(f"  端口: {settings.vector_db.pgvector_port}")
        logger.info(f"  数据库: {settings.vector_db.pgvector_database}")
        
        # 初始化嵌入模型
        embedding_factory = EmbeddingFactory()
        embeddings = embedding_factory.create_embeddings()
        logger.info("✅ 嵌入模型初始化成功")
        
        # 构建连接字符串
        connection_string = f"postgresql://{settings.vector_db.pgvector_user}:{settings.vector_db.pgvector_password}@{settings.vector_db.pgvector_host}:{settings.vector_db.pgvector_port}/{settings.vector_db.pgvector_database}"
        
        # 创建测试文档
        test_documents = [
            Document(
                page_content="这是一个关于人工智能的测试文档。",
                metadata={"source": "test1.txt", "type": "test"}
            ),
            Document(
                page_content="机器学习是人工智能的一个重要分支。",
                metadata={"source": "test2.txt", "type": "test"}
            )
        ]
        
        logger.info(f"创建了 {len(test_documents)} 个测试文档")
        
        # 使用唯一的集合名称
        collection_name = "test_langchain_collection"
        
        logger.info(f"尝试创建PGVector存储，集合名称: {collection_name}")
        
        try:
            # 创建PGVector存储
            vector_store = PGVector.from_documents(
                documents=test_documents,
                embedding=embeddings,
                connection_string=connection_string,
                collection_name=collection_name,
                pre_delete_collection=True  # 清理之前的数据
            )
            
            logger.info("✅ PGVector存储创建成功")
            
            # 测试相似性搜索
            logger.info("测试相似性搜索...")
            search_results = vector_store.similarity_search(
                query="人工智能",
                k=2
            )
            
            logger.info(f"搜索结果数量: {len(search_results)}")
            for i, doc in enumerate(search_results):
                logger.info(f"结果 {i+1}: {doc.page_content}")
                logger.info(f"  元数据: {doc.metadata}")
            
            # 测试带分数的相似性搜索
            logger.info("测试带分数的相似性搜索...")
            search_results_with_scores = vector_store.similarity_search_with_score(
                query="机器学习",
                k=2
            )
            
            logger.info(f"带分数搜索结果数量: {len(search_results_with_scores)}")
            for i, (doc, score) in enumerate(search_results_with_scores):
                logger.info(f"结果 {i+1} (分数: {score:.4f}): {doc.page_content}")
            
            logger.info("✅ 相似性搜索测试成功")
            
            # 清理测试数据
            logger.info("清理测试数据...")
            try:
                vector_store.delete_collection()
                logger.info("✅ 测试数据清理完成")
            except Exception as e:
                logger.warning(f"清理测试数据时出现警告: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ PGVector操作失败: {e}")
            logger.error(f"错误类型: {type(e).__name__}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    logger.info("开始LangChain PGVector集成测试...")
    
    success = test_langchain_pgvector()
    if success:
        print("\n✅ LangChain PGVector集成测试通过！")
        print("向量创建和搜索功能正常")
    else:
        print("\n❌ LangChain PGVector集成测试失败！")
        print("请检查LangChain配置和数据库权限")
        sys.exit(1)