#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试配置类，避免导入其他模块
"""

import sys
import os
from pathlib import Path
import yaml
from typing import Any, Dict

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

def test_config_direct():
    """直接测试配置加载逻辑"""
    print("=== 直接测试配置加载逻辑 ===")
    print(f"当前工作目录: {os.getcwd()}")
    
    # 模拟Settings.load_from_yaml的逻辑
    config_path = "configs/settings.yaml"
    config_file = Path(config_path)
    
    print(f"\n=== 测试配置文件路径解析 ===")
    print(f"默认路径 '{config_path}' 存在: {config_file.exists()}")
    
    # 如果配置文件不存在，尝试从backend目录查找
    if not config_file.exists():
        print("默认路径不存在，尝试从backend目录查找...")
        # 获取当前文件所在目录（根目录）
        current_dir = Path(__file__).parent
        # 模拟config.py中的逻辑：从backend/chat_agent/core向上两级到backend目录
        backend_config_path = current_dir / "backend" / "configs" / "settings.yaml"
        print(f"Backend配置路径: {backend_config_path}")
        print(f"Backend配置路径存在: {backend_config_path.exists()}")
        
        if backend_config_path.exists():
            config_file = backend_config_path
            print(f"使用Backend配置文件: {config_file}")
    
    # 读取配置文件
    if config_file.exists():
        print(f"\n=== 读取配置文件: {config_file} ===")
        with open(config_file, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
        
        print(f"向量数据库类型: {config_data.get('vector_db', {}).get('type', 'NOT FOUND')}")
        print(f"LLM智谱API密钥: {config_data.get('llm', {}).get('zhipu_api_key', 'NOT FOUND')}")
        print(f"嵌入模型智谱API密钥: {config_data.get('embedding', {}).get('zhipu_api_key', 'NOT FOUND')}")
        
        # 检查配置是否正确
        vector_db_type = config_data.get('vector_db', {}).get('type')
        embedding_api_key = config_data.get('embedding', {}).get('zhipu_api_key')
        
        if vector_db_type == 'pgvector' and embedding_api_key:
            print("\n✅ 配置文件内容正确！")
            print(f"  - 向量数据库类型: {vector_db_type}")
            print(f"  - 嵌入模型API密钥: {embedding_api_key[:20]}...")
            return True
        else:
            print("\n❌ 配置文件内容有问题！")
            print(f"  - 向量数据库类型: {vector_db_type}")
            print(f"  - 嵌入模型API密钥: {embedding_api_key}")
            return False
    else:
        print("\n❌ 找不到配置文件！")
        return False

if __name__ == "__main__":
    success = test_config_direct()
    if success:
        print("\n🎉 配置文件测试通过！")
    else:
        print("\n💥 配置文件测试失败！")
        sys.exit(1)