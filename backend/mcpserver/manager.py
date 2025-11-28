"""MCP服务管理器，统一管理所有工具服务"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from .config import MCPServerConfig
from .tools import MySQLMCPTool, PostgreSQLDescribeTableTool, PostgreSQLExecuteQueryTool, PostgreSQLListTablesTool, \
    WeatherNowMCPTool, SearchMCPTool, WeatherFutherMCPTool

from mcpserver.utils.logger import get_logger

logger = get_logger("mcp_manager")


class MCPServiceManager:
    """MCP服务管理器，负责管理所有工具服务的生命周期"""
    
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.tools: Dict[str, Any] = {}
        self.initialized = False
        
    async def initialize(self):
        """初始化所有工具服务"""
        if self.initialized:
            return
            
        logger.info("初始化MCP服务管理器...")
        
        # 根据配置初始化工具
        if self.config.ENABLED_TOOLS.get("mysql", False):
            self.tools["mysql"] = MySQLMCPTool()
            logger.info("MySQL MCP工具已加载")
            
        if self.config.ENABLED_TOOLS.get("postgresql", False):
            self.tools["postgresql_describe_table"] = PostgreSQLDescribeTableTool()
            self.tools["postgresql_execute_query"] = PostgreSQLExecuteQueryTool()
            self.tools["postgresql_list_tables"] = PostgreSQLListTablesTool()
            logger.info("PostgreSQL MCP工具已加载")

        if self.config.ENABLED_TOOLS.get("weather", False):
            self.tools["weather_now"] = WeatherNowMCPTool()
            self.tools["weather_futher"] = WeatherFutherMCPTool()
            logger.info("Weather MCP工具已加载")

        if self.config.ENABLED_TOOLS.get("search", False):
            self.tools["search"] = SearchMCPTool()
            logger.info("Search MCP工具已加载")
            
        self.initialized = True
        logger.info(f"MCP服务管理器初始化完成，已加载 {len(self.tools)} 个工具")
        
    def get_tool(self, tool_name: str) -> Optional[Any]:
        """获取指定的工具实例"""
        return self.tools.get(tool_name)
        
    def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有可用的工具"""
        tools_info = []
        for name, tool in self.tools.items():
            tools_info.append({
                "name": name,
                "display_name": tool.get_name(),
                "description": tool.get_description(),
                "parameters": [
                    {
                        "name": param.name,
                        "type": param.type.value,
                        "description": param.description,
                        "required": param.required,
                        "default": getattr(param, 'default', None),
                        "enum": getattr(param, 'enum', None)
                    }
                    for param in tool.get_parameters()
                ]
            })
        return tools_info
        
    async def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """执行指定工具的操作"""
        if not self.initialized:
            await self.initialize()
            
        tool = self.get_tool(tool_name)
        if not tool:
            return {
                "success": False,
                "error": f"工具 '{tool_name}' 不存在或未启用",
                "available_tools": list(self.tools.keys())
            }
            
        try:
            logger.info(f"执行工具 {tool_name}，参数: {kwargs}")
            result = await tool.execute(**kwargs)
            
            return {
                "success": result.success,
                "result": result.result,
                "error": result.error,
                "tool_name": tool_name,
                "executed_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"执行工具 {tool_name} 时发生错误: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"工具执行失败: {str(e)}",
                "tool_name": tool_name,
                "executed_at": datetime.now().isoformat()
            }
            
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "status": "healthy",
            "initialized": self.initialized,
            "tools_count": len(self.tools),
            "available_tools": list(self.tools.keys()),
            "timestamp": datetime.now().isoformat()
        }
        
    async def shutdown(self):
        """关闭服务管理器"""
        logger.info("关闭MCP服务管理器...")
        
        # 清理工具连接
        for tool_name, tool in self.tools.items():
            try:
                if hasattr(tool, 'connections'):
                    for user_id, conn_info in tool.connections.items():
                        if 'connection' in conn_info:
                            conn_info['connection'].close()
                    tool.connections.clear()
                    logger.info(f"已清理 {tool_name} 工具的连接")
            except Exception as e:
                logger.error(f"清理 {tool_name} 工具连接时发生错误: {str(e)}")
                
        self.tools.clear()
        self.initialized = False
        logger.info("MCP服务管理器已关闭")


# 全局服务管理器实例
_manager_instance: Optional[MCPServiceManager] = None


def get_mcp_manager(config: Optional[MCPServerConfig] = None) -> MCPServiceManager:
    """获取MCP服务管理器单例"""
    global _manager_instance
    
    if _manager_instance is None:
        if config is None:
            config = MCPServerConfig()
        _manager_instance = MCPServiceManager(config)
        
    return _manager_instance


async def initialize_mcp_manager(config: Optional[MCPServerConfig] = None):
    """初始化MCP服务管理器"""
    manager = get_mcp_manager(config)
    await manager.initialize()
    return manager