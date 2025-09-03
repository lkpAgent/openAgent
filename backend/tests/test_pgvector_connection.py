#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import psycopg2
from psycopg2 import sql
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_postgresql_connection():
    """测试PostgreSQL基本连接"""
    try:
        # PostgreSQL连接配置
        conn_params = {
            'host': '113.240.110.92',
            'port': 15432,
            'database': 'mydb',
            'user': 'myuser',
            'password': 'postgresqlpass@2025'
        }
        
        logger.info(f"尝试连接到PostgreSQL: {conn_params['host']}:{conn_params['port']}/{conn_params['database']}")
        
        # 建立连接
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        
        # 测试基本查询
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        logger.info(f"✅ PostgreSQL连接成功！版本: {version[0]}")
        
        # 检查pgvector扩展是否已安装
        cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
        vector_ext = cursor.fetchone()
        
        if vector_ext:
            logger.info("✅ pgvector扩展已安装")
            
            # 测试创建向量表
            test_table_name = "test_embeddings"
            
            # 删除测试表（如果存在）
            cursor.execute(f"DROP TABLE IF EXISTS {test_table_name};")
            
            # 创建测试表
            create_table_sql = f"""
            CREATE TABLE {test_table_name} (
                id SERIAL PRIMARY KEY,
                content TEXT,
                metadata JSONB,
                embedding VECTOR(1024)
            );
            """
            cursor.execute(create_table_sql)
            logger.info(f"✅ 成功创建测试表: {test_table_name}")
            
            # 插入测试向量数据
            import numpy as np
            test_vector = np.random.rand(1024).tolist()
            
            insert_sql = f"""
            INSERT INTO {test_table_name} (content, metadata, embedding) 
            VALUES (%s, %s, %s);
            """
            cursor.execute(insert_sql, (
                "测试文档内容",
                '{"source": "test"}',
                test_vector
            ))
            
            # 测试向量相似性搜索
            search_vector = np.random.rand(1024).tolist()
            search_sql = f"""
            SELECT content, metadata, embedding <-> %s::vector as distance 
            FROM {test_table_name} 
            ORDER BY embedding <-> %s::vector 
            LIMIT 1;
            """
            cursor.execute(search_sql, (search_vector, search_vector))
            result = cursor.fetchone()
            
            if result:
                logger.info(f"✅ 向量相似性搜索测试成功！距离: {result[2]}")
            
            # 清理测试表
            cursor.execute(f"DROP TABLE {test_table_name};")
            logger.info("✅ 清理测试表完成")
            
        else:
            logger.warning("⚠️ pgvector扩展未安装，尝试安装...")
            try:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                conn.commit()
                logger.info("✅ pgvector扩展安装成功")
            except Exception as e:
                logger.error(f"❌ 无法安装pgvector扩展: {e}")
                logger.info("请联系数据库管理员安装pgvector扩展")
                return False
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("✅ PostgreSQL pgvector连接和功能测试完成！")
        return True
        
    except Exception as e:
        logger.error(f"❌ PostgreSQL连接测试失败: {e}")
        return False

def test_langchain_pgvector():
    """测试LangChain PGVector集成"""
    try:
        from langchain_community.vectorstores import PGVector
        from langchain_community.embeddings import FakeEmbeddings
        from langchain.schema import Document
        
        logger.info("开始测试LangChain PGVector集成...")
        
        # 构建连接字符串
        connection_string = "postgresql://myuser:postgresqlpass@2025@113.240.110.92:15432/mydb"
        
        # 初始化嵌入模型（使用假的嵌入模型进行测试）
        embeddings = FakeEmbeddings(size=1024)
        
        # 创建测试文档
        documents = [
            Document(page_content="这是第一个测试文档", metadata={"source": "test1"}),
            Document(page_content="这是第二个测试文档", metadata={"source": "test2"})
        ]
        
        # 创建向量存储
        collection_name = "test_collection"
        vector_store = PGVector.from_documents(
            documents=documents,
            embedding=embeddings,
            connection_string=connection_string,
            collection_name=collection_name,
            pre_delete_collection=True  # 删除已存在的集合
        )
        
        logger.info("✅ LangChain PGVector向量存储创建成功")
        
        # 执行相似性搜索
        query = "测试查询"
        results = vector_store.similarity_search(query, k=2)
        
        logger.info(f"✅ 相似性搜索成功，返回 {len(results)} 个结果")
        for i, doc in enumerate(results):
            logger.info(f"  结果 {i+1}: {doc.page_content[:50]}...")
        
        # 执行带分数的相似性搜索
        results_with_scores = vector_store.similarity_search_with_score(query, k=2)
        
        logger.info(f"✅ 带分数的相似性搜索成功")
        for i, (doc, score) in enumerate(results_with_scores):
            logger.info(f"  结果 {i+1} (分数: {score:.4f}): {doc.page_content[:50]}...")
        
        logger.info("✅ LangChain PGVector集成测试完成！")
        return True
        
    except Exception as e:
        logger.error(f"❌ LangChain PGVector集成测试失败: {e}")
        return False

if __name__ == "__main__":
    logger.info("开始PostgreSQL pgvector连接测试...")
    
    # 测试基本PostgreSQL连接
    if test_postgresql_connection():
        # 测试LangChain集成
        test_langchain_pgvector()
    else:
        logger.error("基本连接测试失败，跳过LangChain集成测试")
        sys.exit(1)