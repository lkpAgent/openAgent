#!/usr/bin/env python3
"""
简单的PGVector测试脚本
用于隔离和诊断PGVector插入问题
"""

import logging
import sys
import os
import uuid
from langchain.schema import Document

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chat_agent.core.config import get_settings
from chat_agent.services.embedding_factory import EmbeddingFactory
from langchain_postgres import PGVector

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("开始简单PGVector测试...")
        
        # 获取配置
        config = get_settings()
        
        # 创建embedding实例
        logger.info("初始化embedding...")
        embedding_config = config.embedding.get_current_config()
        embeddings = EmbeddingFactory.create_embeddings(
            provider=config.embedding.provider,
            model=embedding_config["model"]
        )
        
        # 构建数据库连接字符串
        connection_string = (
            f"postgresql://{config.vector_db.pgvector_user}:{config.vector_db.pgvector_password}@"
            f"{config.vector_db.pgvector_host}:{config.vector_db.pgvector_port}/{config.vector_db.pgvector_database}"
        )
        
        logger.info(f"连接到数据库: {config.vector_db.pgvector_host}:{config.vector_db.pgvector_port}/{config.vector_db.pgvector_database}")
        
        # 初始化PGVector
        vector_store = PGVector(
            embeddings=embeddings,
            connection=connection_string,
            collection_name=config.vector_db.pgvector_table_name,
            use_jsonb=True,
        )
        logger.info("✅ PGVector初始化成功")
        #  添加向量到数据库
        docs = [
            Document(
                page_content="there are cats in the pond",
                metadata={"id": 1, "location": "pond", "topic": "animals"},
            ),
            Document(
                page_content="ducks are also found in the pond",
                metadata={"id": 2, "location": "pond", "topic": "animals"},
            ),
            Document(
                page_content="fresh apples are available at the market",
                metadata={"id": 3, "location": "market", "topic": "food"},
            ),
            Document(
                page_content="the market also sells fresh oranges",
                metadata={"id": 4, "location": "market", "topic": "food"},
            ),
            Document(
                page_content="the new art exhibit is fascinating",
                metadata={"id": 5, "location": "museum", "topic": "art"},
            ),
            Document(
                page_content="a sculpture exhibit is also at the museum",
                metadata={"id": 6, "location": "museum", "topic": "art"},
            ),
            Document(
                page_content="a new coffee shop opened on Main Street",
                metadata={"id": 7, "location": "Main Street", "topic": "food"},
            ),
            Document(
                page_content="the book club meets at the library",
                metadata={"id": 8, "location": "library", "topic": "reading"},
            ),
            Document(
                page_content="the library hosts a weekly story time for kids",
                metadata={"id": 9, "location": "library", "topic": "reading"},
            ),
            Document(
                page_content="a cooking class for beginners is offered at the community center",
                metadata={"id": 10, "location": "community center", "topic": "classes"},
            ),
        ]

        ids = vector_store.add_documents(docs, ids=[doc.metadata["id"] for doc in docs])

        logger.info("✅创建向量成功，ids:",str(ids))
        vector_store.delete(filter={"document_id": "1"}) # 无效
        vector_store.delete(ids=["2"]) # 有用
        logger.info("✅删除向量成功")

        
        # 清理测试数据
        logger.info("清理现有测试数据...")
        try:
            # 删除所有包含test_的文档
            vector_store.delete(filter={"document_id": {"$regex": "test_.*"}})
            logger.info("✅ 测试数据清理完成")
        except Exception as e:
            logger.warning(f"清理数据时出现警告: {e}")
        
        # 创建一个简单的测试文档
        test_doc = Document(
            page_content="这是一个简单的测试文档",
            metadata={
                "document_id": "test_simple_001",
                "knowledge_base_id": "test_kb",
                "source": "test"
            }
        )
        
        # 生成唯一ID
        doc_id = str(uuid.uuid4())
        logger.info(f"准备添加文档，ID: {doc_id}")
        logger.info(f"文档内容: {test_doc.page_content}")
        logger.info(f"文档元数据: {test_doc.metadata}")
        
        # 添加单个文档
        logger.info("添加文档到向量存储...")
        returned_ids = vector_store.add_documents([test_doc], ids=[doc_id])
        logger.info(f"✅ 文档添加成功！")
        logger.info(f"指定的ID: {doc_id}")
        logger.info(f"返回的ID: {returned_ids}")
        
        # 验证文档是否添加成功
        logger.info("验证文档添加...")
        results = vector_store.similarity_search("测试", k=1)
        logger.info(f"✅ 找到 {len(results)} 个相关文档")
        if results:
            doc = results[0]
            logger.info(f"文档内容: {doc.page_content}")
            logger.info(f"文档元数据: {doc.metadata}")
        
        # 测试删除功能
        logger.info("测试删除功能...")
        vector_store.delete(ids=[doc_id])
        logger.info("✅ 文档删除成功")
        
        # 验证删除
        results_after_delete = vector_store.similarity_search("测试", k=1)
        logger.info(f"删除后找到 {len(results_after_delete)} 个相关文档")
        
        logger.info("🎉 简单PGVector测试完成！")
        
    except Exception as e:
        logger.error(f"❌ 简单PGVector测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()