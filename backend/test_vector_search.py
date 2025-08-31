#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from dotenv import load_dotenv
from pathlib import Path

# 手动加载.env文件
load_dotenv(Path(".env"))

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chat_agent.services.document_processor import document_processor
from chat_agent.services.knowledge_base import KnowledgeBaseService
from chat_agent.db.database import get_db
from sqlalchemy.orm import Session

def test_vector_search():
    """测试向量搜索功能"""
    print("=== 测试向量搜索功能 ===")
    
    # 假设我们有一个知识库ID为1
    kb_id = 1
    
    # 1. 测试document_processor的搜索功能
    print("\n1. 测试DocumentProcessor搜索功能:")
    try:
        search_query = "人工智能"
        results = document_processor.search_similar_documents(
            knowledge_base_id=kb_id,
            query=search_query,
            k=5
        )
        
        print(f"搜索查询: '{search_query}'")
        print(f"找到 {len(results)} 个结果")
        
        for i, result in enumerate(results, 1):
            content = result.get('content', '')[:100]
            distance_score = result.get('similarity_score', 0)
            normalized_score = result.get('normalized_score', 0)
            source = result.get('source', 'unknown')
            
            print(f"\n结果 {i}:")
            print(f"  来源: {source}")
            print(f"  距离分数: {distance_score:.4f}")
            print(f"  归一化分数: {normalized_score:.4f}")
            print(f"  内容预览: {content}...")
            
    except Exception as e:
        print(f"DocumentProcessor搜索失败: {e}")
    
    # 2. 测试KnowledgeBaseService的搜索功能
    print("\n2. 测试KnowledgeBaseService搜索功能:")
    try:
        # 创建数据库会话
        db_gen = get_db()
        db = next(db_gen)
        
        kb_service = KnowledgeBaseService(db)
        
        # 测试不同的相似度阈值
        thresholds = [0.3, 0.5, 0.7]
        
        for threshold in thresholds:
            print(f"\n测试相似度阈值: {threshold}")
            
            import asyncio
            results = asyncio.run(kb_service.search(
                kb_id=kb_id,
                query="机器学习算法",
                top_k=5,
                similarity_threshold=threshold
            ))
            
            print(f"找到 {len(results)} 个结果（阈值: {threshold}）")
            
            for i, result in enumerate(results, 1):
                content = result.get('content', '')[:80]
                score = result.get('score', 0)
                source = result.get('source', 'unknown')
                
                print(f"  结果 {i}: 分数={score:.4f}, 来源={source}, 内容={content}...")
        
        db.close()
        
    except Exception as e:
        print(f"KnowledgeBaseService搜索失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. 测试不同类型的查询
    print("\n3. 测试不同类型的查询:")
    test_queries = [
        "深度学习",
        "神经网络",
        "自然语言处理",
        "计算机视觉",
        "推荐系统"
    ]
    
    for query in test_queries:
        try:
            results = document_processor.search_similar_documents(
                knowledge_base_id=kb_id,
                query=query,
                k=3
            )
            
            print(f"\n查询: '{query}' - 找到 {len(results)} 个结果")
            
            if results:
                best_result = results[0]
                print(f"  最佳匹配: 分数={best_result.get('normalized_score', 0):.4f}")
                print(f"  内容: {best_result.get('content', '')[:60]}...")
            
        except Exception as e:
            print(f"查询 '{query}' 失败: {e}")
    
    print("\n=== 向量搜索测试完成 ===")

if __name__ == "__main__":
    test_vector_search()