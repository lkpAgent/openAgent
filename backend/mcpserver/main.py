"""MCP服务器主启动文件"""

import sys
import os
import argparse
import asyncio
from pathlib import Path

# 移除不必要的路径修改
# project_root = Path(__file__).parent.parent
# sys.path.insert(0, str(project_root))

from .config import MCPServerConfig
from .api import run_server
from .utils.logger import get_logger

logger = get_logger("mcp_main")


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="MCP服务器")
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="服务器主机地址 (默认: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="服务器端口 (默认: 8001)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="启用自动重载 (开发模式)"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="配置文件路径"
    )
    parser.add_argument(
        "--enable-mysql",
        action="store_true",
        help="启用MySQL工具"
    )
    parser.add_argument(
        "--enable-postgresql",
        action="store_true",
        help="启用PostgreSQL工具"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="日志级别 (默认: INFO)"
    )
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    
    # 创建配置
    config = MCPServerConfig()
    
    # 应用命令行参数
    if args.host:
        config.HOST = args.host
    if args.port:
        config.PORT = args.port
    if args.log_level:
        config.LOG_LEVEL = args.log_level
        
    # 工具启用配置
    if args.enable_mysql:
        config.ENABLED_TOOLS["mysql"] = True
    if args.enable_postgresql:
        config.ENABLED_TOOLS["postgresql"] = True
        
    # 如果没有启用任何工具，默认启用所有工具
    if not any(config.ENABLED_TOOLS.values()):
        config.ENABLED_TOOLS = {
            "mysql": True,
            "postgresql": True
        }
    
    logger.info("=" * 50)
    logger.info("MCP服务器启动配置:")
    logger.info(f"  主机地址: {config.HOST}")
    logger.info(f"  端口: {config.PORT}")
    logger.info(f"  日志级别: {config.LOG_LEVEL}")
    logger.info(f"  启用的工具: {[k for k, v in config.ENABLED_TOOLS.items() if v]}")
    logger.info(f"  自动重载: {args.reload}")
    logger.info("=" * 50)
    
    try:
        # 启动服务器
        run_server(
            host=config.HOST,
            port=config.PORT,
            reload=args.reload
        )
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭服务器...")
    except Exception as e:
        logger.error(f"服务器启动失败: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()