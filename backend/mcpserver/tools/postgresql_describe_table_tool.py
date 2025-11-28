"""PostgreSQL Describe Table MCP Tool for database schema operations."""

import os
import psycopg2
from typing import List, Dict, Any
from urllib.parse import urlparse

from mcpserver.base import BaseTool, ToolParameter, ToolParameterType, ToolResult
from mcpserver.utils.logger import get_logger

logger = get_logger("postgresql_describe_table_tool")


class PostgreSQLDescribeTableTool(BaseTool):
    """PostgreSQL MCP tool for describing table structure."""
    
    def __init__(self):
        super().__init__()
        self.connection = None
        self._initialize_connection()
    
    def get_name(self) -> str:
        return "postgresql_describe_table"
        
    def get_description(self) -> str:
        return "PostgreSQL表结构查询工具，用于查看表的基本信息和结构。"
        
    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="table_name",
                type=ToolParameterType.STRING,
                description="要查询的表名",
                required=True
            )
        ]
    
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
            logger.error(f"Failed to initialize PostgreSQL connection: {str(e)}", exc_info=True)
            self.connection = None
    
    def _describe_table(self, table_name: str) -> Dict[str, Any]:
        """获取表结构信息"""
        cursor = self.connection.cursor()
        try:
            # 获取列信息
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length,
                    numeric_precision,
                    numeric_scale
                FROM information_schema.columns 
                WHERE table_name = %s AND table_schema = 'public'
                ORDER BY ordinal_position;
            """, (table_name,))
            
            columns = []
            for row in cursor.fetchall():
                columns.append({
                    "column_name": row[0],
                    "data_type": row[1],
                    "is_nullable": row[2],
                    "column_default": row[3],
                    "character_maximum_length": row[4],
                    "numeric_precision": row[5],
                    "numeric_scale": row[6]
                })
            
            # 获取主键信息
            cursor.execute("""
                SELECT column_name
                FROM information_schema.key_column_usage
                WHERE table_name = %s AND table_schema = 'public'
                AND constraint_name IN (
                    SELECT constraint_name
                    FROM information_schema.table_constraints
                    WHERE table_name = %s AND constraint_type = 'PRIMARY KEY'
                );
            """, (table_name, table_name))
            
            primary_keys = [row[0] for row in cursor.fetchall()]
            
            # 获取表行数
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            row_count = cursor.fetchone()[0]
            
            return {
                "table_name": table_name,
                "columns": columns,
                "primary_keys": primary_keys,
                "row_count": row_count
            }
        finally:
            cursor.close()
    
    async def execute(self, **kwargs) -> ToolResult:
        """执行表结构查询"""
        try:
            if not self.connection:
                return ToolResult(
                    success=False,
                    error="数据库连接未初始化"
                )
                
            table_name = kwargs.get("table_name")
            if not table_name:
                return ToolResult(
                    success=False,
                    error="缺少table_name参数"
                )
            
            logger.info(f"查询表结构: {table_name}")
            table_info = self._describe_table(table_name)
            
            return ToolResult(
                success=True,
                result=table_info
            )
            
        except Exception as e:
            logger.error(f"PostgreSQL表结构查询失败: {str(e)}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"工具执行失败: {str(e)}"
            )