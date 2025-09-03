#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from pathlib import Path
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from chat_agent.core.config import Settings

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_config_loading():
    """测试配置文件加载"""
    try:
        logger.info("测试配置文件加载...")
        
        # 使用绝对路径
        config_path = Path(__file__).parent / "configs" / "settings.yaml"
        logger.info(f"配置文件路径: {config_path}")
        logger.info(f"配置文件是否存在: {config_path.exists()}")
        
        if config_path.exists():
            settings = Settings.load_from_yaml(str(config_path))
        else:
            logger.warning("配置文件不存在，使用默认配置")
            settings = Settings()
        
        logger.info(f"向量数据库类型: {settings.vector_db.type}")
        logger.info(f"pgvector主机: {settings.vector_db.pgvector_host}")
        logger.info(f"pgvector端口: {settings.vector_db.pgvector_port}")
        logger.info(f"pgvector数据库: {settings.vector_db.pgvector_database}")
        logger.info(f"pgvector用户: {settings.vector_db.pgvector_user}")
        logger.info(f"pgvector表名: {settings.vector_db.pgvector_table_name}")
        
        if settings.vector_db.type == "pgvector":
            logger.info("✅ 配置文件加载成功，向量数据库类型为pgvector")
            return True
        else:
            logger.error(f"❌ 配置文件加载失败，向量数据库类型为: {settings.vector_db.type}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 配置文件加载测试失败: {e}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_config_loading()
    if success:
        print("\n✅ 配置文件加载测试通过！")
    else:
        print("\n❌ 配置文件加载测试失败！")
        sys.exit(1)