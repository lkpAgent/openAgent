#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试配置文件加载，不导入任何会触发初始化的模块
"""

import sys
import os
from pathlib import Path
import yaml

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

def test_config_loading():
    """测试配置文件加载"""
    print("=== 测试配置文件加载 ===")
    print(f"当前工作目录: {os.getcwd()}")
    
    # 测试不同的配置文件路径
    config_paths = [
        "configs/settings.yaml",
        "backend/configs/settings.yaml",
        str(Path(__file__).parent / "backend" / "configs" / "settings.yaml")
    ]
    
    print("\n=== 配置文件路径测试 ===")
    for config_path in config_paths:
        config_file = Path(config_path)
        print(f"路径 '{config_path}' 存在: {config_file.exists()}")
        if config_file.exists():
            print(f"  绝对路径: {config_file.absolute()}")
    
    # 直接读取YAML文件
    backend_config_path = Path(__file__).parent / "backend" / "configs" / "settings.yaml"
    if backend_config_path.exists():
        print(f"\n=== 直接读取YAML文件 ===")
        with open(backend_config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
        
        print(f"向量数据库类型: {config_data.get('vector_db', {}).get('type', 'NOT FOUND')}")
        print(f"智谱API密钥: {config_data.get('llm', {}).get('zhipu_api_key', 'NOT FOUND')}")
        print(f"嵌入模型智谱API密钥: {config_data.get('embedding', {}).get('zhipu_api_key', 'NOT FOUND')}")
    
    # 现在测试Settings类的加载
    try:
        print("\n=== 测试Settings类加载 ===")
        # 只导入Settings类，不导入其他模块
        from chat_agent.core.config import Settings
        
        # 测试默认路径加载
        print("\n1. 测试默认路径加载:")
        settings_default = Settings.load_from_yaml()
        print(f"  向量数据库类型: {settings_default.vector_db.type}")
        print(f"  智谱API密钥: {settings_default.llm.zhipu_api_key}")
        print(f"  嵌入模型智谱API密钥: {settings_default.embedding.zhipu_api_key}")
        
        # 测试指定路径加载
        print("\n2. 测试指定路径加载:")
        settings_specific = Settings.load_from_yaml(str(backend_config_path))
        print(f"  向量数据库类型: {settings_specific.vector_db.type}")
        print(f"  智谱API密钥: {settings_specific.llm.zhipu_api_key}")
        print(f"  嵌入模型智谱API密钥: {settings_specific.embedding.zhipu_api_key}")
        
        # 比较两种加载方式的结果
        if settings_default.vector_db.type == settings_specific.vector_db.type:
            print("\n✅ 两种加载方式结果一致")
        else:
            print("\n❌ 两种加载方式结果不一致！")
            print(f"  默认路径结果: {settings_default.vector_db.type}")
            print(f"  指定路径结果: {settings_specific.vector_db.type}")
        
    except Exception as e:
        print(f"\n❌ Settings类加载失败: {e}")
        import traceback
        print(f"详细错误信息: {traceback.format_exc()}")

if __name__ == "__main__":
    test_config_loading()