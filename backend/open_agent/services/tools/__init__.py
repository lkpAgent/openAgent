"""Agent tools package."""

from .weather import WeatherQueryTool
from .search import TavilySearchTool
from .datetime_tool import DateTimeTool
from open_agent.services.mcp.postgresql_mcp import PostgreSQLMCPTool
from open_agent.services.mcp.mysql_mcp import MySQLMCPTool


# Try to import LangChain native tools if available
try:
    from .langchain_native_tools import LANGCHAIN_NATIVE_TOOLS
except ImportError:
    LANGCHAIN_NATIVE_TOOLS = []

__all__ = [
    'WeatherQueryTool',
    'TavilySearchTool',
    'DateTimeTool',
    'PostgreSQLMCPTool',
    'MySQLMCPTool',
    'LANGCHAIN_NATIVE_TOOLS'
]