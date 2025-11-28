"""PostgreSQL Execute Query MCP Tool for database query operations."""

import json
import os
import psycopg2
from typing import List, Dict, Any
from datetime import datetime
from urllib.parse import urlparse

from mcpserver.base import BaseTool, ToolParameter, ToolParameterType, ToolResult
from mcpserver.utils.logger import get_logger

logger = get_logger("postgresql_execute_query_tool")


class PostgreSQLExecuteQueryTool(BaseTool):
    """PostgreSQL MCP tool for executing SQL queries."""
    
    def __init__(self):
        super().__init__()
        self.connection = None
        self._initialize_connection()
    
    def get_name(self) -> str:
        return "postgresql_execute_query"
        
    def get_description(self) -> str:
        return "PostgreSQL SQL执行工具，用于执行SQL查询语句。"
        
    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="sql_query",
                type=ToolParameterType.STRING,
                description="要执行的SQL查询语句",
                required=True
            ),
            # ToolParameter(
            #     name="limit",
            #     type=ToolParameterType.INTEGER,
            #     description="查询结果限制数量，默认100",
            #     required=False,
            #     default=100
            # )
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
    
    def _execute_query(self, sql_query: str, limit: int = 100) -> Dict[str, Any]:
        """执行SQL查询"""
        cursor = self.connection.cursor()
        try:
            # 添加LIMIT限制（如果查询中没有）
            if limit and "LIMIT" not in sql_query.upper():
                sql_query = f"{sql_query.rstrip(';')} LIMIT {limit};"
            
            cursor.execute(sql_query)
            
            # 获取列名
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            # 获取结果
            if cursor.description:  # SELECT查询
                rows = cursor.fetchall()
                data = []
                for row in rows:
                    row_dict = {}
                    for i, value in enumerate(row):
                        if i < len(columns):
                            # 处理特殊数据类型
                            if isinstance(value, datetime):
                                row_dict[columns[i]] = value.isoformat()
                            else:
                                row_dict[columns[i]] = value
                    data.append(row_dict)
                
                return {
                    "success": True,
                    "data": data,
                    "columns": columns,
                    "row_count": len(data),
                    "query": sql_query
                }
            else:  # INSERT/UPDATE/DELETE查询
                affected_rows = cursor.rowcount
                return {
                    "success": True,
                    "affected_rows": affected_rows,
                    "query": sql_query,
                    "message": f"查询执行成功，影响 {affected_rows} 行"
                }
        finally:
            cursor.close()
    
    async def execute(self, **kwargs) -> ToolResult:
        """执行SQL查询"""
        try:
            if not self.connection:
                return ToolResult(
                    success=False,
                    error="数据库连接未初始化"
                )
                
            sql_query = kwargs.get("sql_query")
            limit = kwargs.get("limit", 100)
            
            if not sql_query:
                return ToolResult(
                    success=False,
                    error="缺少sql_query参数"
                )
            
            logger.info(f"执行SQL查询: {sql_query[:100]}...")
            query_result = self._execute_query(sql_query, limit)
            
            return ToolResult(
                success=True,
                result=query_result
            )
            
        except Exception as e:
            logger.error(f"PostgreSQL SQL执行失败: {str(e)}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"工具执行失败: {str(e)}"
            )