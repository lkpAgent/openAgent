"""PostgreSQL MCP工具全局管理器"""

from typing import Optional
from chat_agent.services.tools.postgresql_mcp import PostgreSQLMCPTool
from ..utils.logger import get_logger

logger = get_logger("postgresql_tool_manager")


class PostgreSQLToolManager:
    """PostgreSQL工具全局单例管理器"""
    
    _instance: Optional['PostgreSQLToolManager'] = None
    _postgresql_tool: Optional[PostgreSQLMCPTool] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def postgresql_tool(self) -> PostgreSQLMCPTool:
        """获取PostgreSQL工具实例"""
        if self._postgresql_tool is None:
            self._postgresql_tool = PostgreSQLMCPTool()
            logger.info("创建全局PostgreSQL工具实例")
        return self._postgresql_tool
    
    def get_tool(self) -> PostgreSQLMCPTool:
        """获取PostgreSQL工具实例（别名方法）"""
        return self.postgresql_tool


# 全局实例
postgresql_tool_manager = PostgreSQLToolManager()


def get_postgresql_tool() -> PostgreSQLMCPTool:
    """获取全局PostgreSQL工具实例"""
    return postgresql_tool_manager.get_tool()