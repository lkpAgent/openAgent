#!/usr/bin/env python3
"""
测试LLM配置加载
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

def test_llm_config():
    print("=== 测试LLM配置加载 ===")
    
    settings = get_settings()
    
    print(f"LLM Provider: {settings.llm.provider}")
    print(f"OpenAI API Key: {settings.llm.openai_api_key}")
    print(f"OpenAI Base URL: {settings.llm.openai_base_url}")
    print(f"OpenAI Model: {settings.llm.openai_model}")
    print(f"DeepSeek API Key: {settings.llm.deepseek_api_key}")
    print(f"DeepSeek Base URL: {settings.llm.deepseek_base_url}")
    print(f"DeepSeek Model: {settings.llm.deepseek_model}")
    
    print("\n=== 获取当前配置 ===")
    current_config = settings.llm.get_current_config()
    print(f"Current config type: {type(current_config)}")
    print(f"Current config: {current_config}")
    
    if current_config:
        print(f"\nAPI Key: {current_config.get('api_key')}")
        print(f"Base URL: {current_config.get('base_url')}")
        print(f"Model: {current_config.get('model')}")
        print(f"Temperature: {current_config.get('temperature')}")
        print(f"Max Tokens: {current_config.get('max_tokens')}")
    else:
        print("配置为None!")

if __name__ == "__main__":
    test_llm_config()