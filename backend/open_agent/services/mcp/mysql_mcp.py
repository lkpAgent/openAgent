"""MySQL MCP (Model Context Protocol) tool for database operations."""

import json
import pymysql
from typing import List, Dict, Any, Optional
from datetime import datetime

from open_agent.services.agent.base import BaseTool, ToolParameter, ToolParameterType, ToolResult
from open_agent.utils.logger import get_logger

logger = get_logger("mysql_mcp_tool")


class MySQLMCPTool(BaseTool):
    """MySQL MCP tool for database operations and intelligent querying."""
    
    def __init__(self):
        super().__init__()
        self.connections = {}  # 存储用户的数据库连接
    
    def get_name(self) -> str:
        return "mysql_mcp"
    
    def get_description(self) -> str:
        return "MySQL MCP服务工具，提供数据库连接、表结构查询、SQL执行等功能，支持智能数据问答。"
        
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
                WHERE table_schema = DATABASE()
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
                    numeric_scale,
                    column_comment
                FROM information_schema.columns 
                WHERE table_schema = DATABASE() AND table_name = %s
                ORDER BY ordinal_position;
            """, (table_name,))
            
            columns = []
            for row in cursor.fetchall():
                column_info = {
                    "column_name": row[0],
                    "data_type": row[1],
                    "is_nullable": row[2] == 'YES',
                    "column_default": row[3],
                    "character_maximum_length": row[4],
                    "numeric_precision": row[5],
                    "numeric_scale": row[6],
                    "column_comment": row[7] or ""
                }
                columns.append(column_info)
            
            # 获取主键信息
            cursor.execute("""
                SELECT column_name
                FROM information_schema.key_column_usage
                WHERE table_schema = DATABASE() 
                AND table_name = %s 
                AND constraint_name = 'PRIMARY'
                ORDER BY ordinal_position;
            """, (table_name,))
            
            primary_keys = [row[0] for row in cursor.fetchall()]
            
            # 获取外键信息
            cursor.execute("""
                SELECT 
                    column_name,
                    referenced_table_name,
                    referenced_column_name
                FROM information_schema.key_column_usage
                WHERE table_schema = DATABASE() 
                AND table_name = %s 
                AND referenced_table_name IS NOT NULL;
            """, (table_name,))
            
            foreign_keys = []
            for row in cursor.fetchall():
                foreign_keys.append({
                    "column_name": row[0],
                    "referenced_table": row[1],
                    "referenced_column": row[2]
                })
            
            # 获取索引信息
            cursor.execute("""
                SELECT 
                    index_name,
                    column_name,
                    non_unique
                FROM information_schema.statistics
                WHERE table_schema = DATABASE() 
                AND table_name = %s
                ORDER BY index_name, seq_in_index;
            """, (table_name,))
            
            indexes = []
            for row in cursor.fetchall():
                indexes.append({
                    "index_name": row[0],
                    "column_name": row[1],
                    "is_unique": row[2] == 0
                })
            
            # 获取表注释
            cursor.execute("""
                SELECT table_comment
                FROM information_schema.tables
                WHERE table_schema = DATABASE() AND table_name = %s;
            """, (table_name,))
            
            table_comment = ""
            result = cursor.fetchone()
            if result:
                table_comment = result[0] or ""
            
            return {
                "table_name": table_name,
                "columns": columns,
                "primary_keys": primary_keys,
                "foreign_keys": foreign_keys,
                "indexes": indexes,
                "table_comment": table_comment
            }
            
        finally:
            cursor.close()
    
    def _execute_query(self, connection, sql_query: str, limit: int = 100) -> Dict[str, Any]:
        """执行SQL查询"""
        cursor = connection.cursor()
        try:
            # 添加LIMIT限制（如果查询中没有LIMIT）
            if limit and limit > 0 and "LIMIT" not in sql_query.upper():
                sql_query = f"{sql_query.rstrip(';')} LIMIT {limit}"
            
            cursor.execute(sql_query)
            
            # 获取列名
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            # 获取数据
            rows = cursor.fetchall()
            
            # 转换为字典列表
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
            
        finally:
            cursor.close()
    
    def _create_connection(self, config: Dict[str, Any]) -> pymysql.Connection:
        """创建MySQL数据库连接"""
        try:
            connection = pymysql.connect(
                host=config['host'],
                port=int(config.get('port', 3306)),
                user=config['username'],
                password=config['password'],
                database=config['database'],
                connect_timeout=10,
                charset='utf8mb4'
            )
            return connection
        except Exception as e:
            raise Exception(f"MySQL连接失败: {str(e)}")
    
    def _test_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """测试数据库连接"""
        try:
            conn = self._create_connection(config)
            cursor = conn.cursor()
            
            # 获取数据库版本信息
            cursor.execute("SELECT VERSION();")
            version = cursor.fetchone()[0]
            
            # 获取数据库引擎信息
            cursor.execute("SHOW ENGINES;")
            engines = cursor.fetchall()
            has_innodb = any('InnoDB' in str(engine) for engine in engines)
            
            cursor.close()
            conn.close()
            
            return {
                "success": True,
                "version": version,
                "has_innodb": has_innodb,
                "message": "连接测试成功"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "连接测试失败"
            }



    async def execute(self, **kwargs) -> ToolResult:
        """Execute the MySQL MCP tool operation."""
        try:
            operation = kwargs.get("operation")
            connection_config = kwargs.get("connection_config", {})
            user_id = kwargs.get("user_id")
            table_name = kwargs.get("table_name")
            sql_query = kwargs.get("sql_query")
            limit = kwargs.get("limit", 100)
            
            logger.info(f"执行MySQL MCP操作: {operation}")
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
                if not connection_config:
                    return ToolResult(
                        success=False,
                        error="缺少connection_config参数"
                    )
                
                if not user_id:
                    return ToolResult(
                        success=False,
                        error="缺少user_id参数"
                    )
                
                try:
                    # 建立MySQL连接
                    connection = pymysql.connect(
                        host=connection_config["host"],
                        port=int(connection_config["port"]),
                        user=connection_config["username"],
                        password=connection_config["password"],
                        database=connection_config["database"],
                        charset='utf8mb4',
                        cursorclass=pymysql.cursors.Cursor
                    )
                    
                    # 存储连接
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
                    result=f"不支持的操作类型: {operation}",
                )
                
        except Exception as e:
            logger.error(f"MySQL MCP工具执行失败: {str(e)}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"工具执行失败: {str(e)}"
            )