import sys
import os
from pathlib import Path
import logging
import psycopg2
import psycopg2.extras
import numpy as np
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from open_agent.core.config import Settings
from open_agent.services.embedding_factory import EmbeddingFactory

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_manual_pgvector():
    """手动测试PGVector向量创建和搜索"""
    try:
        logger.info("开始手动PGVector测试...")
        
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
        
        # 连接数据库
        conn = psycopg2.connect(
            host=settings.vector_db.pgvector_host,
            port=settings.vector_db.pgvector_port,
            database=settings.vector_db.pgvector_database,
            user=settings.vector_db.pgvector_user,
            password=settings.vector_db.pgvector_password
        )
        
        logger.info("✅ 数据库连接成功")
        
        cursor = conn.cursor()
        
        # 创建测试表
        table_name = "test_vectors_manual"
        
        # 删除已存在的表
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        
        # 创建新表
        cursor.execute(f"""
            CREATE TABLE {table_name} (
                id SERIAL PRIMARY KEY,
                content TEXT,
                metadata JSONB,
                embedding vector(2048)
            )
        """)
        
        logger.info(f"✅ 创建测试表 {table_name} 成功")
        
        # 准备测试文档
        test_docs = [
            {"content": "这是一个关于人工智能的测试文档。", "metadata": {"source": "test1.txt", "type": "test"}},
            {"content": "机器学习是人工智能的一个重要分支。", "metadata": {"source": "test2.txt", "type": "test"}},
            {"content": "深度学习使用神经网络来模拟人脑的工作方式。", "metadata": {"source": "test3.txt", "type": "test"}}
        ]
        
        # 生成嵌入并插入数据
        for i, doc in enumerate(test_docs):
            # 生成嵌入向量
            embedding_vector = embeddings.embed_query(doc["content"])
            
            # 插入数据
            cursor.execute(f"""
                INSERT INTO {table_name} (content, metadata, embedding)
                VALUES (%s, %s, %s)
            """, (
                doc["content"],
                psycopg2.extras.Json(doc["metadata"]),
                embedding_vector
            ))
            
            logger.info(f"✅ 插入文档 {i+1}: {doc['content'][:30]}...")
        
        conn.commit()
        logger.info(f"✅ 成功插入 {len(test_docs)} 个文档")
        
        # 测试相似性搜索
        query = "人工智能"
        query_embedding = embeddings.embed_query(query)
        
        logger.info(f"测试查询: '{query}'")
        
        # 执行相似性搜索（使用余弦距离）
        cursor.execute(f"""
            SELECT content, metadata, embedding <=> %s::vector as distance
            FROM {table_name}
            ORDER BY embedding <=> %s::vector
            LIMIT 3
        """, (query_embedding, query_embedding))
        
        results = cursor.fetchall()
        
        logger.info(f"搜索结果数量: {len(results)}")
        for i, (content, metadata, distance) in enumerate(results):
            logger.info(f"结果 {i+1} (距离: {distance:.4f}): {content}")
            logger.info(f"  元数据: {metadata}")
        
        # 测试点积相似性
        logger.info("\n测试点积相似性搜索...")
        cursor.execute(f"""
            SELECT content, metadata, (embedding <#> %s::vector) * -1 as similarity
            FROM {table_name}
            ORDER BY embedding <#> %s::vector
            LIMIT 3
        """, (query_embedding, query_embedding))
        
        results = cursor.fetchall()
        
        logger.info(f"点积搜索结果数量: {len(results)}")
        for i, (content, metadata, similarity) in enumerate(results):
            logger.info(f"结果 {i+1} (相似度: {similarity:.4f}): {content}")
        
        # 清理测试数据
        cursor.execute(f"DROP TABLE {table_name}")
        conn.commit()
        logger.info("✅ 测试数据清理完成")
        
        cursor.close()
        conn.close()
        logger.info("✅ 数据库连接已关闭")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    logger.info("开始手动PGVector向量测试...")
    
    success = test_manual_pgvector()
    if success:
        print("\n✅ 手动PGVector向量测试通过！")
        print("向量创建、存储和搜索功能正常")
    else:
        print("\n❌ 手动PGVector向量测试失败！")
        print("请检查配置和数据库权限")
        sys.exit(1)