#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试上传文档和问答时embedding配置的一致性
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from open_agent.services.document_processor import DocumentProcessor
from open_agent.services.embedding_factory import EmbeddingFactory
from open_agent.services.knowledge_chat import KnowledgeChatService
from open_agent.core.config import get_settings
from open_agent.db.database import get_db

def test_embedding_consistency():
    """测试embedding配置一致性"""
    print("=== 测试Embedding配置一致性 ===")
    
    settings = get_settings()
    
    print(f"\n当前配置:")
    print(f"Embedding Provider: {settings.embedding.provider}")
    print(f"智谱AI API Key: {settings.embedding.zhipu_api_key[:20]}...")
    print(f"智谱AI Base URL: {settings.embedding.zhipu_base_url}")
    print(f"智谱AI Embedding Model: {settings.embedding.zhipu_embedding_model}")
    
    # 1. 测试DocumentProcessor的embedding配置
    print("\n=== 1. DocumentProcessor Embedding配置 ===")
    doc_processor = DocumentProcessor()
    doc_embeddings = doc_processor.embeddings
    
    print(f"DocumentProcessor embedding类型: {type(doc_embeddings).__name__}")
    if hasattr(doc_embeddings, 'api_key'):
        print(f"API Key: {doc_embeddings.api_key[:20] if doc_embeddings.api_key else 'None'}...")
    if hasattr(doc_embeddings, 'base_url'):
        print(f"Base URL: {doc_embeddings.base_url}")
    if hasattr(doc_embeddings, 'model'):
        print(f"Model: {doc_embeddings.model}")
    if hasattr(doc_embeddings, 'dimensions'):
        print(f"Dimensions: {doc_embeddings.dimensions}")
    
    # 2. 测试EmbeddingFactory直接创建的embedding
    print("\n=== 2. EmbeddingFactory直接创建的Embedding ===")
    factory_embeddings = EmbeddingFactory.create_embeddings()
    
    print(f"EmbeddingFactory embedding类型: {type(factory_embeddings).__name__}")
    if hasattr(factory_embeddings, 'api_key'):
        print(f"API Key: {factory_embeddings.api_key[:20] if factory_embeddings.api_key else 'None'}...")
    if hasattr(factory_embeddings, 'base_url'):
        print(f"Base URL: {factory_embeddings.base_url}")
    if hasattr(factory_embeddings, 'model'):
        print(f"Model: {factory_embeddings.model}")
    if hasattr(factory_embeddings, 'dimensions'):
        print(f"Dimensions: {factory_embeddings.dimensions}")
    
    # 3. 测试KnowledgeChatService的embedding配置
    print("\n=== 3. KnowledgeChatService Embedding配置 ===")
    try:
        db_gen = get_db()
        db = next(db_gen)
        chat_service = KnowledgeChatService(db)
        chat_embeddings = chat_service.embeddings
        
        print(f"KnowledgeChatService embedding类型: {type(chat_embeddings).__name__}")
        if hasattr(chat_embeddings, 'api_key'):
            print(f"API Key: {chat_embeddings.api_key[:20] if chat_embeddings.api_key else 'None'}...")
        if hasattr(chat_embeddings, 'base_url'):
            print(f"Base URL: {chat_embeddings.base_url}")
        if hasattr(chat_embeddings, 'model'):
            print(f"Model: {chat_embeddings.model}")
        if hasattr(chat_embeddings, 'dimensions'):
            print(f"Dimensions: {chat_embeddings.dimensions}")
    except Exception as e:
        print(f"创建KnowledgeChatService失败: {e}")
    
    # 4. 比较配置一致性
    print("\n=== 4. 配置一致性检查 ===")
    
    # 检查类型是否一致
    doc_type = type(doc_embeddings).__name__
    factory_type = type(factory_embeddings).__name__
    
    print(f"DocumentProcessor vs EmbeddingFactory类型: {doc_type} vs {factory_type}")
    if doc_type == factory_type:
        print("✅ Embedding类型一致")
    else:
        print("❌ Embedding类型不一致")
    
    # 检查配置参数是否一致
    config_consistent = True
    
    if hasattr(doc_embeddings, 'api_key') and hasattr(factory_embeddings, 'api_key'):
        if doc_embeddings.api_key != factory_embeddings.api_key:
            print("❌ API Key不一致")
            config_consistent = False
        else:
            print("✅ API Key一致")
    
    if hasattr(doc_embeddings, 'base_url') and hasattr(factory_embeddings, 'base_url'):
        if doc_embeddings.base_url != factory_embeddings.base_url:
            print("❌ Base URL不一致")
            config_consistent = False
        else:
            print("✅ Base URL一致")
    
    if hasattr(doc_embeddings, 'model') and hasattr(factory_embeddings, 'model'):
        if doc_embeddings.model != factory_embeddings.model:
            print("❌ Model不一致")
            config_consistent = False
        else:
            print("✅ Model一致")
    
    if hasattr(doc_embeddings, 'dimensions') and hasattr(factory_embeddings, 'dimensions'):
        if doc_embeddings.dimensions != factory_embeddings.dimensions:
            print("❌ Dimensions不一致")
            config_consistent = False
        else:
            print("✅ Dimensions一致")
    
    # 5. 测试实际embedding结果
    print("\n=== 5. 实际Embedding结果测试 ===")
    test_text = "这是一个测试文本"
    
    try:
        doc_embedding = doc_embeddings.embed_query(test_text)
        factory_embedding = factory_embeddings.embed_query(test_text)
        
        print(f"DocumentProcessor embedding维度: {len(doc_embedding)}")
        print(f"EmbeddingFactory embedding维度: {len(factory_embedding)}")
        print(f"DocumentProcessor前3个值: {doc_embedding[:3]}")
        print(f"EmbeddingFactory前3个值: {factory_embedding[:3]}")
        
        # 检查向量是否相同
        if doc_embedding == factory_embedding:
            print("✅ Embedding结果完全一致")
        else:
            print("❌ Embedding结果不一致")
            config_consistent = False
            
    except Exception as e:
        print(f"Embedding测试失败: {e}")
        config_consistent = False
    
    # 总结
    print("\n=== 总结 ===")
    if config_consistent:
        print("🎉 上传文档和问答时的embedding配置完全一致！")
    else:
        print("⚠️  上传文档和问答时的embedding配置存在不一致！")
    
    return config_consistent

if __name__ == "__main__":
    test_embedding_consistency()