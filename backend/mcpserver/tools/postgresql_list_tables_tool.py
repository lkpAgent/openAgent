"""PostgreSQL List Tables MCP Tool for database table listing operations."""

import os
import psycopg2
from typing import List, Dict, Any
from urllib.parse import urlparse

from mcpserver.base import BaseTool, ToolParameter, ToolParameterType, ToolResult
from mcpserver.utils.logger import get_logger

logger = get_logger("postgresql_list_tables_tool")


class PostgreSQLListTablesTool(BaseTool):
    """PostgreSQL MCP tool for listing all tables in the database."""
    
    def __init__(self):
        super().__init__()
        self.connection = None
        self._initialize_connection()
    
    def get_name(self) -> str:
        return "postgresql_list_tables"
        
    def get_description(self) -> str:
        return "PostgreSQL表列表工具，用于列举数据库中的所有表名。"
        
    def get_parameters(self) -> List[ToolParameter]:
        return []  # 不需要参数
    
    def _initialize_connection(self):
        """Initialize database connection from environment variables"""
        try:
            database_url = os.getenv('DATABASE_URL') or os.getenv('MCP_POSTGRESQL_DATABASE_URL')
            
            if database_url:
                parsed = urlparse(database_url)
                self.connection = psycopg2.connect(
                    host=parsed.hostname,
                    port=parsed.port or 5432,
                    user=parsed.username,
                    password=parsed.password,
                    database=parsed.path.lstrip('/')
                )
                logger.info("PostgreSQL connection initialized successfully")
            else:
                logger.warning("No database URL found for PostgreSQL connection")
                
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL connection: {e}")
            self.connection = None
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the list tables operation."""
        try:
            if not self.connection:
                return ToolResult(
                    success=False,
                    error="数据库连接未初始化，请检查环境变量配置"
                )
            
            with self.connection.cursor() as cursor:
                # 查询所有表名
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """)
                
                tables = cursor.fetchall()
                
                # 提取表名列表
                table_names = [table[0] for table in tables]
                
                logger.info(f"Found {len(table_names)} tables in database")
                
                return ToolResult(
                    success=True,
                    result={
                        "tables": table_names,
                        "count": len(table_names)
                    }
                )
                
        except Exception as e:
            logger.error(f"Failed to list tables: {e}")
            return ToolResult(
                success=False,
                error=f"获取表列表失败: {str(e)}"
            )