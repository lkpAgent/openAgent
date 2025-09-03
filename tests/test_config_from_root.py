#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试从根目录启动时配置文件加载是否正确
"""

import sys
import os
from pathlib import Path

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

# 直接导入配置类，避免导入会触发初始化的模块
from chat_agent.core.config import Settings

def test_config_from_root():
    """测试从根目录启动时的配置加载"""
    print("=== 从根目录测试配置文件加载 ===")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"Python路径: {sys.path[:3]}...")  # 只显示前3个路径
    
    try:
        # 直接调用Settings.load_from_yaml()而不是get_settings()
        settings = Settings.load_from_yaml()
        
        print(f"\n=== 配置加载结果 ===")
        print(f"向量数据库类型: {settings.vector_db.type}")
        print(f"pgvector主机: {settings.vector_db.pgvector_host}")
        print(f"pgvector端口: {settings.vector_db.pgvector_port}")
        print(f"pgvector数据库: {settings.vector_db.pgvector_database}")
        print(f"pgvector用户: {settings.vector_db.pgvector_user}")
        print(f"pgvector表名: {settings.vector_db.pgvector_table_name}")
        
        print(f"\n=== LLM配置 ===")
        print(f"LLM提供商: {settings.llm.provider}")
        print(f"智谱API密钥: {settings.llm.zhipu_api_key[:20]}..." if settings.llm.zhipu_api_key else "未设置")
        
        print(f"\n=== 配置文件路径测试 ===")
        # 测试不同的配置文件路径
        config_paths = [
            "configs/settings.yaml",
            "backend/configs/settings.yaml",
            str(Path(__file__).parent / "backend" / "configs" / "settings.yaml")
        ]
        
        for config_path in config_paths:
            config_file = Path(config_path)
            print(f"路径 '{config_path}' 存在: {config_file.exists()}")
        
        if settings.vector_db.type == "pgvector":
            print("\n✅ 配置文件加载成功！向量数据库类型为pgvector")
            return True
        else:
            print(f"\n❌ 配置文件加载失败！向量数据库类型为: {settings.vector_db.type}")
            return False
            
    except Exception as e:
        print(f"\n❌ 配置文件加载测试失败: {e}")
        import traceback
        print(f"详细错误信息: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_config_from_root()
    if success:
        print("\n🎉 从根目录启动的配置文件加载测试通过！")
    else:
        print("\n💥 从根目录启动的配置文件加载测试失败！")
        sys.exit(1)