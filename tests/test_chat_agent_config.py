#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试chat-agent启动时的配置加载
"""

import sys
import os
from pathlib import Path

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

def test_chat_agent_config():
    """测试chat-agent配置加载"""
    print("=== 测试chat-agent配置加载 ===")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"Backend目录: {backend_dir}")
    
    try:
        # 直接导入配置模块，不导入会触发初始化的其他模块
        print("\n=== 导入配置模块 ===")
        from chat_agent.core.config import Settings, get_settings
        
        # 测试Settings.load_from_yaml()
        print("\n=== 测试Settings.load_from_yaml() ===")
        settings = Settings.load_from_yaml()
        
        print(f"向量数据库类型: {settings.vector_db.type}")
        print(f"pgvector主机: {settings.vector_db.pgvector_host}")
        print(f"pgvector端口: {settings.vector_db.pgvector_port}")
        print(f"pgvector数据库: {settings.vector_db.pgvector_database}")
        print(f"pgvector用户: {settings.vector_db.pgvector_user}")
        print(f"pgvector表名: {settings.vector_db.pgvector_table_name}")
        
        print(f"\n=== LLM和Embedding配置 ===")
        print(f"LLM提供商: {settings.llm.provider}")
        print(f"Embedding提供商: {settings.embedding.provider}")
        print(f"LLM智谱API密钥: {settings.llm.zhipu_api_key[:20]}..." if settings.llm.zhipu_api_key else "未设置")
        print(f"Embedding智谱API密钥: {settings.embedding.zhipu_api_key[:20]}..." if settings.embedding.zhipu_api_key else "未设置")
        
        # 验证关键配置
        success = True
        issues = []
        
        if settings.vector_db.type != "pgvector":
            success = False
            issues.append(f"向量数据库类型错误: {settings.vector_db.type}，应该是pgvector")
        
        if not settings.embedding.zhipu_api_key:
            success = False
            issues.append("Embedding智谱API密钥未设置")
        
        if not settings.llm.zhipu_api_key:
            success = False
            issues.append("LLM智谱API密钥未设置")
        
        if success:
            print("\n✅ 配置加载成功！所有关键配置都正确")
            return True
        else:
            print("\n❌ 配置加载有问题：")
            for issue in issues:
                print(f"  - {issue}")
            return False
            
    except Exception as e:
        print(f"\n❌ 配置加载测试失败: {e}")
        import traceback
        print(f"详细错误信息: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_chat_agent_config()
    if success:
        print("\n🎉 chat-agent配置测试通过！")
        print("\n现在可以启动chat-agent，应该会正确读取pgvector配置")
    else:
        print("\n💥 chat-agent配置测试失败！")
        sys.exit(1)