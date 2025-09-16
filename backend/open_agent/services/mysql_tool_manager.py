"""MySQL MCP工具全局管理器"""

from typing import Optional
from open_agent.services.mcp.mysql_mcp import MySQLMCPTool
from ..utils.logger import get_logger

logger = get_logger("mysql_tool_manager")


class MySQLToolManager:
    """MySQL工具全局单例管理器"""
    
    _instance: Optional['MySQLToolManager'] = None
    _mysql_tool: Optional[MySQLMCPTool] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def mysql_tool(self) -> MySQLMCPTool:
        """获取MySQL工具实例"""
        if self._mysql_tool is None:
            self._mysql_tool = MySQLMCPTool()
            logger.info("创建全局MySQL工具实例")
        return self._mysql_tool
    
    def get_tool(self) -> MySQLMCPTool:
        """获取MySQL工具实例（别名方法）"""
        return self.mysql_tool


# 全局实例
mysql_tool_manager = MySQLToolManager()


def get_mysql_tool() -> MySQLMCPTool:
    """获取全局MySQL工具实例"""
    return mysql_tool_manager.get_tool()