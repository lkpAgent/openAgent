#!/usr/bin/env python3
"""
测试Embedding配置加载
"""

import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
load_dotenv()

from chat_agent.core.config import get_settings

def test_embedding_config():
    print("=== 测试Embedding配置加载 ===")
    
    settings = get_settings()
    
    print(f"Embedding Provider: {settings.embedding.provider}")
    print(f"智谱AI API Key: {settings.embedding.zhipu_api_key}")
    print(f"智谱AI Base URL: {settings.embedding.zhipu_base_url}")
    print(f"智谱AI Embedding Model: {settings.embedding.zhipu_embedding_model}")
    
    print("\n=== 获取当前Embedding配置 ===")
    current_config = settings.embedding.get_current_config()
    print(f"Current embedding config type: {type(current_config)}")
    print(f"Current embedding config: {current_config}")
    
    if current_config:
        print(f"\nEmbedding API Key: {current_config.get('api_key')}")
        print(f"Embedding Base URL: {current_config.get('base_url')}")
        print(f"Embedding Model: {current_config.get('model')}")
    else:
        print("Embedding配置为None!")
    
    print("\n=== LLM配置对比 ===")
    llm_config = settings.llm.get_current_config()
    print(f"LLM Provider: {settings.llm.provider}")
    print(f"LLM Config: {llm_config}")
    
    print("\n=== 向量数据库配置 ===")
    print(f"Vector DB Type: {settings.vector_db.type}")
    print(f"Persist Directory: {settings.vector_db.persist_directory}")
    print(f"Collection Name: {settings.vector_db.collection_name}")
    print(f"Embedding Dimension: {settings.vector_db.embedding_dimension}")

if __name__ == "__main__":
    test_embedding_config()