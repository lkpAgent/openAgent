"""MCP Server 配置管理"""

import os
from typing import Dict, Any

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    V2 = True
except ImportError:
    # 兼容旧版本的pydantic
    from pydantic import BaseSettings
    V2 = False


class MCPServerConfig(BaseSettings):
    """MCP服务器配置"""
    
    # 服务器配置（与 main.py / api.py 保持一致）
    HOST: str = "127.0.0.1"
    PORT: int = 8001
    DEBUG: bool = False
    DATABASE_URL: str = os.getenv("DATABASE_URL") or ""
    # 工具服务配置（字典形式以便按名称启用/禁用）
    ENABLED_TOOLS: Dict[str, bool] = {
        "mysql": False,
        "postgresql": True,
        "weather": True,
        "search": True,
    }
    
    # 数据库连接池配置
    MAX_CONNECTIONS_PER_USER: int = 5
    CONNECTION_TIMEOUT: int = 30
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "mcpserver.log"
    
    # v2 配置：忽略多余环境变量，设置前缀与 .env 文件
    if 'V2' in globals() and V2:
        model_config = SettingsConfigDict(
            env_prefix="MCP_",
            env_file=".env",
            extra="ignore"
        )
    else:
        # v1 配置：忽略多余环境变量
        class Config:
            env_prefix = "MCP_"
            env_file = ".env"
            extra = "ignore"


# 全局配置实例
config = MCPServerConfig()