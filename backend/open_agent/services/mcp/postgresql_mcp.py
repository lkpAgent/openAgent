"""PostgreSQL MCP (Model Context Protocol) tool for database operations."""

import json
import psycopg2
from typing import List, Dict, Any, Optional
from datetime import datetime

from open_agent.services.agent.base import BaseTool, ToolParameter, ToolParameterType, ToolResult
from open_agent.utils.logger import get_logger

logger = get_logger("postgresql_mcp_tool")


class PostgreSQLMCPTool(BaseTool):
    """PostgreSQL MCP tool for database operations and intelligent querying."""
    
    def __init__(self):
        super().__init__()
        self.connections = {}  # 存储用户的数据库连接
    
    def get_name(self) -> str:
        return "postgresql_mcp"
        
    def get_description(self) -> str:
        return "PostgreSQL MCP服务工具，提供数据库连接、表结构查询、SQL执行等功能，支持智能数据问答。"
        
    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="operation",
                type=ToolParameterType.STRING,
                description="操作类型",
                required=True,
                enum=["connect", "list_tables", "describe_table", "execute_query", "test_connection", "disconnect"]
            ),
            ToolParameter(
                name="connection_config",
                type=ToolParameterType.OBJECT,
                description="数据库连接配置 {host, port, database, username, password}",
                required=False
            ),
            ToolParameter(
                name="user_id",
                type=ToolParameterType.STRING,
                description="用户ID，用于管理连接",
                required=False
            ),
            ToolParameter(
                name="table_name",
                type=ToolParameterType.STRING,
                description="表名（用于describe_table操作）",
                required=False
            ),
            ToolParameter(
                name="sql_query",
                type=ToolParameterType.STRING,
                description="SQL查询语句（用于execute_query操作）",
                required=False
            ),
            ToolParameter(
                name="limit",
                type=ToolParameterType.INTEGER,
                description="查询结果限制数量，默认100",
                required=False,
                default=100
            )
        ]
    
    def _create_connection(self, config: Dict[str, Any]) -> psycopg2.extensions.connection:
        """创建PostgreSQL数据库连接"""
        try:
            connection = psycopg2.connect(
                host=config['host'],
                port=int(config.get('port', 5432)),
                user=config['username'],
                password=config['password'],
                database=config['database'],
                connect_timeout=10
            )
            return connection
        except Exception as e:
            raise Exception(f"PostgreSQL连接失败: {str(e)}")
    
    def _test_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """测试数据库连接"""
        try:
            conn = self._create_connection(config)
            cursor = conn.cursor()
            
            # 获取数据库版本信息
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            
            # 检查pgvector扩展
            cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
            has_vector = bool(cursor.fetchall())
            
            cursor.close()
            conn.close()
            
            return {
                "success": True,
                "version": version,
                "has_pgvector": has_vector,
                "message": "连接测试成功"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "连接测试失败"
            }
    
    def _get_tables(self, connection) -> List[Dict[str, Any]]:
        """获取数据库表列表"""
        cursor = connection.cursor()
        try:
            cursor.execute("""
                SELECT 
                    table_name,
                    table_type,
                    table_schema
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            
            tables = []
            for row in cursor.fetchall():
                tables.append({
                    "table_name": row[0],
                    "table_type": row[1],
                    "table_schema": row[2]
                })
            
            return tables
        finally:
            cursor.close()
    
    def _describe_table(self, connection, table_name: str) -> Dict[str, Any]:
        """获取表结构信息"""
        cursor = connection.cursor()
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
    
    def _execute_query(self, connection, sql_query: str, limit: int = 100) -> Dict[str, Any]:
        """执行SQL查询"""
        cursor = connection.cursor()
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
    
    async def execute(self, operation: str, connection_config: Optional[Dict[str, Any]] = None, 
                     user_id: Optional[str] = None, table_name: Optional[str] = None,
                     sql_query: Optional[str] = None, limit: int = 100) -> ToolResult:
        """执行PostgreSQL MCP操作"""
        try:
            logger.info(f"执行PostgreSQL MCP操作: {operation}")
            
            if operation == "test_connection":
                if not connection_config:
                    return ToolResult(
                        success=False,
                        error="缺少连接配置参数"
                    )
                
                result = self._test_connection(connection_config)
                return ToolResult(
                    success=result["success"],
                    result=result,
                    error=result.get("error")
                )
            
            elif operation == "connect":
                if not connection_config or not user_id:
                    return ToolResult(
                        success=False,
                        error="缺少连接配置或用户ID参数"
                    )
                
                try:
                    connection = self._create_connection(connection_config)
                    self.connections[user_id] = {
                        "connection": connection,
                        "config": connection_config,
                        "connected_at": datetime.now().isoformat()
                    }
                    
                    # 获取表列表
                    tables = self._get_tables(connection)
                    
                    return ToolResult(
                        success=True,
                        result={
                            "message": "数据库连接成功",
                            "database": connection_config["database"],
                            "tables": tables,
                            "table_count": len(tables)
                        }
                    )
                except Exception as e:
                    return ToolResult(
                        success=False,
                        error=f"连接失败: {str(e)}"
                    )
            
            elif operation == "list_tables":
                if not user_id or user_id not in self.connections:
                    return ToolResult(
                        success=False,
                        error="用户未连接数据库，请先执行connect操作"
                    )
                
                connection = self.connections[user_id]["connection"]
                tables = self._get_tables(connection)
                
                return ToolResult(
                    success=True,
                    result={
                        "tables": tables,
                        "table_count": len(tables)
                    }
                )
            
            elif operation == "describe_table":
                if not user_id or user_id not in self.connections:
                    return ToolResult(
                        success=False,
                        error="用户未连接数据库，请先执行connect操作"
                    )
                
                if not table_name:
                    return ToolResult(
                        success=False,
                        error="缺少table_name参数"
                    )
                
                connection = self.connections[user_id]["connection"]
                table_info = self._describe_table(connection, table_name)
                
                return ToolResult(
                    success=True,
                    result=table_info
                )
            
            elif operation == "execute_query":
                if not user_id or user_id not in self.connections:
                    return ToolResult(
                        success=False,
                        error="用户未连接数据库，请先执行connect操作"
                    )
                
                if not sql_query:
                    return ToolResult(
                        success=False,
                        error="缺少sql_query参数"
                    )
                
                connection = self.connections[user_id]["connection"]
                query_result = self._execute_query(connection, sql_query, limit)
                
                return ToolResult(
                    success=True,
                    result=query_result
                )
            
            elif operation == "disconnect":
                if user_id and user_id in self.connections:
                    try:
                        self.connections[user_id]["connection"].close()
                        del self.connections[user_id]
                        return ToolResult(
                            success=True,
                            result={"message": "数据库连接已断开"}
                        )
                    except Exception as e:
                        return ToolResult(
                            success=False,
                            error=f"断开连接失败: {str(e)}"
                        )
                else:
                    return ToolResult(
                        success=True,
                        result={"message": "用户未连接数据库"}
                    )
            
            else:
                return ToolResult(
                    success=False,
                    error=f"不支持的操作类型: {operation}"
                )
                
        except Exception as e:
            logger.error(f"PostgreSQL MCP工具执行失败: {str(e)}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"工具执行失败: {str(e)}"
            )