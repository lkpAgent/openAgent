from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
from langchain_openai import ChatOpenAI
from chat_agent.core.context import UserContext
from .smart_query import DatabaseQueryService
from .postgresql_tool_manager import get_postgresql_tool
from .table_metadata_service import TableMetadataService
from ..core.config import get_settings

# 配置日志
logger = logging.getLogger(__name__)

class SmartWorkflowError(Exception):
    """智能工作流自定义异常"""
    pass

class DatabaseConnectionError(SmartWorkflowError):
    """数据库连接异常"""
    pass

class TableSchemaError(SmartWorkflowError):
    """表结构获取异常"""
    pass

class SQLGenerationError(SmartWorkflowError):
    """SQL生成异常"""
    pass

class QueryExecutionError(SmartWorkflowError):
    """查询执行异常"""
    pass


class SmartDatabaseWorkflowManager:
    """
    智能数据库工作流管理器
    负责协调数据库连接、表元数据获取、SQL生成、查询执行和AI总结的完整流程
    """
    
    def __init__(self, db=None):
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.database_service = DatabaseQueryService()
        self.postgresql_tool = get_postgresql_tool()
        self.db = db
        self.table_metadata_service = TableMetadataService(db) if db else None
        
        from ..core.llm import create_llm
        self.llm = create_llm()
    
    async def _run_in_executor(self, func, *args):
        """在线程池中运行阻塞函数"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, func, *args)
    
    def _convert_query_result_to_table_data(self, query_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        将数据库查询结果转换为前端表格数据格式
        参考Excel处理方式，以表格形式返回结果
        """
        try:
            data = query_result.get('data', [])
            columns = query_result.get('columns', [])
            row_count = query_result.get('row_count', 0)
            
            if not data or not columns:
                return {
                    'result_type': 'table',
                    'columns': [],
                    'data': [],
                    'total': 0,
                    'message': '查询未返回数据'
                }
            
            # 构建列定义
            table_columns = []
            for i, col_name in enumerate(columns):
                table_columns.append({
                    'prop': f'col_{i}',
                    'label': str(col_name),
                    'width': 'auto'
                })
            
            # 转换数据行
            table_data = []
            for row_index, row in enumerate(data):
                row_data = {'_index': str(row_index)}
                # 处理字典格式的行数据
                if isinstance(row, dict):
                    for i, col_name in enumerate(columns):
                        col_prop = f'col_{i}'
                        value = row.get(col_name)
                        # 处理None值和特殊值
                        if value is None:
                            row_data[col_prop] = ''
                        elif isinstance(value, (int, float, str, bool)):
                            row_data[col_prop] = str(value)
                        else:
                            row_data[col_prop] = str(value)
                else:
                    # 处理列表格式的行数据（兼容性处理）
                    for i, value in enumerate(row):
                        col_prop = f'col_{i}'
                        # 处理None值和特殊值
                        if value is None:
                            row_data[col_prop] = ''
                        elif isinstance(value, (int, float, str, bool)):
                            row_data[col_prop] = str(value)
                        else:
                            row_data[col_prop] = str(value)
                
                table_data.append(row_data)
            
            return {
                'result_type': 'table_data',
                'columns': table_columns,
                'data': table_data,
                'total': row_count,
                'message': f'查询成功，共返回 {row_count} 条记录'
            }
            
        except Exception as e:
            logger.error(f"转换查询结果异常: {str(e)}")
            return {
                'result_type': 'error',
                'columns': [],
                'data': [],
                'total': 0,
                'message': f'结果转换失败: {str(e)}'
            }
    
    async def process_database_query_stream(
        self, 
        user_query: str, 
        user_id: int, 
        database_config_id: int
    ):
        """
        流式处理数据库智能问数查询的主要工作流（基于保存的表元数据）
        实时推送每个工作流步骤
        
        新流程：
        1. 根据database_config_id获取数据库配置并创建连接
        2. 从系统数据库读取表元数据（只包含启用问答的表）
        3. 根据表元数据生成SQL
        4. 执行SQL查询
        5. 查询数据后处理成表格形式
        6. 生成数据总结
        7. 返回结果
        
        Args:
            user_query: 用户问题
            user_id: 用户ID
            database_config_id: 数据库配置ID
            
        Yields:
            包含工作流步骤或最终结果的字典
        """
        workflow_steps = []
        
        try:
            logger.info(f"开始执行流式数据库查询工作流 - 用户ID: {user_id}, 数据库配置ID: {database_config_id}, 查询: {user_query[:50]}...")
            
            # 步骤1: 根据database_config_id获取数据库配置并创建连接
            try:
                step_data = {
                    'type': 'workflow_step',
                    'step': 'database_connection',
                    'status': 'running',
                    'message': '正在建立数据库连接...',
                    'timestamp': datetime.now().isoformat()
                }
                yield step_data
                
                # 获取数据库配置并建立连接
                connection_result = await self._connect_database(user_id, database_config_id)
                if not connection_result['success']:
                    raise DatabaseConnectionError(connection_result['message'])
                
                step_data.update({
                    'status': 'completed',
                    'message': '数据库连接成功',
                    'details': {'database': connection_result.get('database_name', 'Unknown')}
                })
                yield step_data
                
                workflow_steps.append({
                    'step': 'database_connection',
                    'status': 'completed',
                    'message': '数据库连接成功'
                })
                
            except Exception as e:
                error_msg = f'数据库连接失败: {str(e)}'
                step_data = {
                    'type': 'workflow_step',
                    'step': 'database_connection',
                    'status': 'failed',
                    'message': error_msg,
                    'timestamp': datetime.now().isoformat()
                }
                yield step_data
                
                yield {
                    'type': 'error',
                    'message': error_msg,
                    'workflow_steps': workflow_steps
                }
                return
            
            # 步骤2: 从系统数据库读取表元数据（只包含启用问答的表）
            try:
                step_data = {
                    'type': 'workflow_step',
                    'step': 'table_metadata',
                    'status': 'running',
                    'message': '正在从系统数据库读取表元数据...',
                    'timestamp': datetime.now().isoformat()
                }
                yield step_data
                
                # 从系统数据库读取已保存的表元数据（只包含启用问答的表）
                tables_info = await self._get_saved_tables_metadata(user_id, database_config_id)
                
                step_data.update({
                    'status': 'completed',
                    'message': f'成功读取 {len(tables_info)} 个启用问答的表元数据',
                    'details': {'table_count': len(tables_info), 'tables': list(tables_info.keys())}
                })
                yield step_data
                
                workflow_steps.append({
                    'step': 'table_metadata',
                    'status': 'completed',
                    'message': f'成功读取表元数据'
                })
                
            except Exception as e:
                error_msg = f'获取表元数据失败: {str(e)}'
                step_data = {
                    'type': 'workflow_step',
                    'step': 'table_metadata',
                    'status': 'failed',
                    'message': error_msg,
                    'timestamp': datetime.now().isoformat()
                }
                yield step_data
                
                yield {
                    'type': 'error',
                    'message': error_msg,
                    'workflow_steps': workflow_steps
                }
                return
            
            # 步骤3: 根据表元数据生成SQL
            try:
                step_data = {
                    'type': 'workflow_step',
                    'step': 'sql_generation',
                    'status': 'running',
                    'message': '正在根据表元数据生成SQL查询...',
                    'timestamp': datetime.now().isoformat()
                }
                yield step_data
                
                # 根据表元数据选择相关表并生成SQL
                target_tables, target_schemas = await self._select_target_table(user_query, tables_info)
                step_data = {
                    'type': 'workflow_step',
                    'step': 'table_selected',
                    'status': 'completed',
                    'message': f'已经智能选择了相关表: {", ".join(target_tables)}',
                    'timestamp': datetime.now().isoformat()
                }

                yield step_data
                workflow_steps.append({
                    'step': 'table_metadata',
                    'status': 'completed',
                    'message': f'已经智能选择了相关表: {", ".join(target_tables)}',
                })
                sql_query = await self._generate_sql_query(user_query, target_tables, target_schemas)
                
                step_data.update({
                    'status': 'completed',
                    'message': 'SQL查询生成成功',
                    'details': {
                        'target_tables': target_tables,
                        'generated_sql': sql_query[:100] + '...' if len(sql_query) > 100 else sql_query
                    }
                })
                yield step_data
                
                workflow_steps.append({
                    'step': 'sql_generation',
                    'status': 'completed',
                    'message': 'SQL语句生成成功'
                })
                
            except Exception as e:
                error_msg = f'SQL生成失败: {str(e)}'
                step_data = {
                    'type': 'workflow_step',
                    'step': 'sql_generation',
                    'status': 'failed',
                    'message': error_msg,
                    'timestamp': datetime.now().isoformat()
                }
                yield step_data
                
                yield {
                    'type': 'error',
                    'message': error_msg,
                    'workflow_steps': workflow_steps
                }
                return
            
            # 步骤4: 执行SQL查询
            try:
                step_data = {
                    'type': 'workflow_step',
                    'step': 'query_execution',
                    'status': 'running',
                    'message': '正在执行SQL查询...',
                    'timestamp': datetime.now().isoformat()
                }
                yield step_data
                
                query_result = await self._execute_database_query(user_id, sql_query)
                
                step_data.update({
                    'status': 'completed',
                    'message': f'查询执行成功，返回 {query_result.get("row_count", 0)} 条记录',
                    'details': {'row_count': query_result.get('row_count', 0)}
                })
                yield step_data
                
                workflow_steps.append({
                    'step': 'query_execution',
                    'status': 'completed',
                    'message': '查询执行成功'
                })
                
            except Exception as e:
                error_msg = f'查询执行失败: {str(e)}'
                step_data = {
                    'type': 'workflow_step',
                    'step': 'query_execution',
                    'status': 'failed',
                    'message': error_msg,
                    'timestamp': datetime.now().isoformat()
                }
                yield step_data
                
                yield {
                    'type': 'error',
                    'message': error_msg,
                    'workflow_steps': workflow_steps
                }
                return
            
            # 步骤5: 查询数据后处理成表格形式（在步骤6中完成）
            # 步骤6: 生成数据总结
            try:
                step_data = {
                    'type': 'workflow_step',
                    'step': 'ai_summary',
                    'status': 'running',
                    'message': '正在生成查询结果总结...',
                    'timestamp': datetime.now().isoformat()
                }
                yield step_data
                
                summary = await self._generate_database_summary(user_query, query_result, ', '.join(target_tables))
                
                step_data.update({
                    'status': 'completed',
                    'message': '总结生成完成',
                    'details': {
                        'tables_analyzed': target_tables,
                        'summary_length': len(summary)
                    }
                })
                yield step_data
                
                workflow_steps.append({
                    'step': 'ai_summary',
                    'status': 'completed',
                    'message': '总结生成完成'
                })
                
            except Exception as e:
                logger.warning(f'生成总结失败: {str(e)}')
                summary = '查询执行完成，但生成总结时出现问题。'
                
                workflow_steps.append({
                    'step': 'ai_summary',
                    'status': 'warning',
                    'message': '总结生成失败，但查询成功'
                })
            
            # 步骤7: 返回最终结果，且结果参考excel的处理方式，尽量以表格形式返回
            try:
                step_data = {
                    'type': 'workflow_step',
                    'step': 'result_formatting',
                    'status': 'running',
                    'message': '正在格式化查询结果...',
                    'timestamp': datetime.now().isoformat()
                }
                yield step_data
                
                # 转换为表格格式
                table_data = self._convert_query_result_to_table_data(query_result)
                
                step_data.update({
                    'status': 'completed',
                    'message': '结果格式化完成'
                })
                yield step_data
                
                workflow_steps.append({
                    'step': 'result_formatting',
                    'status': 'completed',
                    'message': '结果格式化完成'
                })
                
                # 返回最终结果
                final_result = {
                    'type': 'final_result',
                    'success': True,
                    'data': {
                        **table_data,
                        'generated_sql': sql_query,
                        'summary': summary,
                        'table_name': target_tables,
                        'query_result': query_result,
                        'metadata_source': 'saved_database'  # 标记元数据来源
                    },
                    'workflow_steps': workflow_steps,
                    'timestamp': datetime.now().isoformat()
                }
                
                yield final_result
                logger.info(f"数据库查询工作流完成 - 用户ID: {user_id}")
                
            except Exception as e:
                error_msg = f'结果格式化失败: {str(e)}'
                yield {
                    'type': 'error',
                    'message': error_msg,
                    'workflow_steps': workflow_steps
                }
                return
            
        except Exception as e:
            logger.error(f"数据库查询工作流异常: {str(e)}", exc_info=True)
            yield {
                'type': 'error',
                'message': f'系统异常: {str(e)}',
                'workflow_steps': workflow_steps
            }
    
    async def _connect_database(self, user_id: int, database_config_id: int) -> Dict[str, Any]:
        """连接数据库（判断用户现有连接）"""
        try:
            # 获取数据库配置
            from ..services.database_config_service import DatabaseConfigService
            config_service = DatabaseConfigService(self.db)
            config = config_service.get_config_by_id(database_config_id, user_id)
            
            if not config:
                return {'success': False, 'message': '数据库配置不存在'}
            
            # 测试连接（如果已经有连接则直接复用）
            connection_config = {
                'host': config.host,
                'port': config.port,
                'database': config.database,
                'username': config.username,
                'password': config_service._decrypt_password(config.password)
            }
            
            try:
                connection = self.postgresql_tool._test_connection(connection_config)
                if connection['success'] == True:
                    return {
                        'success': True,
                        'database_name': config.database,
                        'message': '连接成功'
                    }
                else:
                    return {
                        'success': False,
                        'database_name': config.database,
                        'message': '连接失败'
                    }
            except Exception as e:
                return {
                    'success': False,
                    'message': f'连接失败: {str(e)}'
                }
                
        except Exception as e:
            logger.error(f"数据库连接异常: {str(e)}")
            return {'success': False, 'message': f'连接异常: {str(e)}'}
    
    async def _get_saved_tables_metadata(self, user_id: int, database_config_id: int) -> Dict[str, Dict[str, Any]]:
        """从系统数据库中读取已保存的表元数据"""
        try:
            if not self.table_metadata_service:
                raise TableSchemaError("表元数据服务未初始化")
            
            # 从数据库中获取表元数据
            saved_metadata = self.table_metadata_service.get_user_table_metadata(
                user_id, database_config_id
            )
            
            if not saved_metadata:
                raise TableSchemaError(f"未找到数据库配置ID {database_config_id} 的表元数据，请先在数据库管理页面收集表元数据")
            
            # 转换为所需格式
            tables_metadata = {}
            for meta in saved_metadata:
                # 只处理启用问答的表
                if meta.is_enabled_for_qa:
                    tables_metadata[meta.table_name] = {
                        'table_name': meta.table_name,
                        'columns': meta.columns_info or [],
                        'primary_keys': meta.primary_keys or [],
                        'row_count': meta.row_count or 0,
                        'table_comment': meta.table_comment or '',
                        'qa_description': meta.qa_description or '',
                        'business_context': meta.business_context or '',
                        'from_saved_metadata': True  # 标记来源
                    }
            
            if not tables_metadata:
                raise TableSchemaError("没有启用问答的表，请在数据库管理页面启用相关表的问答功能")
            
            logger.info(f"从系统数据库读取表元数据成功，共 {len(tables_metadata)} 个启用问答的表")
            return tables_metadata
                
        except Exception as e:
            logger.error(f"读取保存的表元数据异常: {str(e)}")
            raise TableSchemaError(f'读取表元数据失败: {str(e)}')
    
    async def _get_table_schema(self, user_id: int, table_name: str) -> Dict[str, Any]:
        """获取指定表结构"""
        try:
            # 使用PostgreSQL MCP工具获取表结构
            schema_result = await self.postgresql_tool.describe_table(table_name)
            
            if schema_result.get('success'):
                return schema_result.get('schema', {})
            else:
                raise TableSchemaError(schema_result.get('error', '获取表结构失败'))
                
        except Exception as e:
            logger.error(f"获取表结构异常: {str(e)}")
            raise TableSchemaError(f'获取表结构失败: {str(e)}')
    
    async def _select_target_table(self, user_query: str, tables_info: Dict[str, Dict]) -> tuple[List[str], List[Dict]]:
        """根据用户查询选择相关的表，支持返回多个表"""
        try:
            if len(tables_info) == 1:
                # 只有一个表，直接返回
                table_name = list(tables_info.keys())[0]
                return [table_name], [tables_info[table_name]]
            
            # 多个表时，使用LLM选择相关的表
            tables_summary = []
            for table_name, schema in tables_info.items():
                columns = schema.get('columns', [])
                column_names = [col.get('column_name', col.get('name', '')) for col in columns]
                qa_desc = schema.get('qa_description', '')
                business_ctx = schema.get('business_context', '')
                tables_summary.append(f"表名: {table_name}\n字段: {', '.join(column_names[:10])}\n表描述: {qa_desc}\n业务上下文: {business_ctx}")
            
            prompt = f"""
            用户查询: {user_query}
            
            可用的表:
            {chr(10).join(tables_summary)}
            
            请根据用户查询选择相关的表，可以选择多个表。分析表之间可能的关联关系，返回所有相关的表名，用逗号分隔。
            可以通过qa_description（表描述），business_context(表的业务上下文），以及column_names几个字段判断要使用哪些表。
            注意：只返回表名列表，后面不要跟其他的内容。
            例如直接输出: table1,table2,table3
            """
            
            response = await self.llm.ainvoke(prompt)
            selected_tables = [t.strip() for t in response.content.strip().split(',')]
            
            # 验证选择的表是否存在
            valid_tables = []
            valid_schemas = []
            for table in selected_tables:
                if table in tables_info:
                    valid_tables.append(table)
                    valid_schemas.append(tables_info[table])
                else:
                    logger.warning(f"LLM选择的表 {table} 不存在")
            
            if valid_tables:
                return valid_tables, valid_schemas
            else:
                # 如果没有有效的表，选择第一个表
                table_name = list(tables_info.keys())[0]
                logger.warning(f"没有找到有效的表，使用默认表 {table_name}")
                return [table_name], [tables_info[table_name]]
                
        except Exception as e:
            logger.error(f"选择目标表异常: {str(e)}")
            # 出现异常时选择第一个表
            table_name = list(tables_info.keys())[0]
            return [table_name], [tables_info[table_name]]
    
    async def _generate_sql_query(self, user_query: str, table_names: List[str], table_schemas: List[Dict]) -> str:
        """生成SQL语句，支持多表关联查询"""
        try:
            # 构建所有表的结构信息
            tables_info = []
            for table_name, schema in zip(table_names, table_schemas):
                columns_info = []
                for col in schema.get('columns', []):
                    col_info = f"{col['column_name']} ({col['data_type']})"
                    columns_info.append(col_info)
                
                table_info = f"表名: {table_name}\n"
                table_info += f"表描述: {schema.get('qa_description', '')}\n"
                table_info += f"业务上下文: {schema.get('business_context', '')}\n"
                table_info += "字段信息:\n" + "\n".join(columns_info)
                tables_info.append(table_info)
            
            schema_text = "\n\n".join(tables_info)
            
            prompt = f"""
            基于以下表结构，将自然语言查询转换为SQL语句。如果需要关联多个表，请分析表之间的关系，使用合适的JOIN语法：
            
            {schema_text}
            
            用户查询: {user_query}
            
            请生成对应的SQL查询语句，要求：
            1. 只返回SQL语句，不要包含其他解释
            2. 如果查询涉及多个表，需要正确处理表之间的关联关系
            3. 使用合适的JOIN类型（INNER JOIN、LEFT JOIN等）
            4. 确保SELECT的字段来源明确，必要时使用表名前缀
            """
            
            # 使用LLM生成SQL
            response = await self.llm.ainvoke(prompt)
            sql_query = response.content.strip()
            
            # 清理SQL语句
            if sql_query.startswith('```sql'):
                sql_query = sql_query[6:]
            if sql_query.endswith('```'):
                sql_query = sql_query[:-3]
            
            sql_query = sql_query.strip()
            
            logger.info(f"生成的SQL查询: {sql_query}")
            return sql_query
            
        except Exception as e:
            logger.error(f"SQL生成异常: {str(e)}")
            raise SQLGenerationError(f'SQL生成失败: {str(e)}')
    
    async def _execute_database_query(self, user_id: int, sql_query: str) -> Dict[str, Any]:
        """执行SQL语句"""
        try:
            # 使用PostgreSQL MCP工具执行查询
            if str(user_id) in self.postgresql_tool.connections:
                query_result = self.postgresql_tool._execute_query(self.postgresql_tool.connections[str(user_id)]['connection'],sql_query)
            else:
                raise QueryExecutionError('请重新进行数据库连接')
            if query_result.get('success'):
                data = query_result.get('data', [])
                return {
                    'success': True,
                    'data': data,
                    'row_count': len(data),
                    'columns': query_result.get('columns', []),
                    'sql_query': sql_query
                }
            else:
                raise QueryExecutionError(query_result.get('error', '查询执行失败'))
                
        except Exception as e:
            logger.error(f"查询执行异常: {str(e)}")
            raise QueryExecutionError(f'查询执行失败: {str(e)}')
    
    async def _generate_database_summary(self, user_query: str, query_result: Dict, tables_str: str) -> str:
        """生成AI总结，支持多表查询结果"""
        try:
            data = query_result.get('data', [])
            row_count = query_result.get('row_count', 0)
            columns = query_result.get('columns', [])
            sql_query = query_result.get('sql_query', '')
            
            # 构建总结提示词
            prompt = f"""
用户查询: {user_query}
涉及的表: {tables_str}
查询结果: 共 {row_count} 条记录
查询的字段: {', '.join(columns)}
执行的SQL: {sql_query}

前几条数据示例:
{str(data[:3]) if data else '无数据'}

请基于以上信息，用中文生成一个简洁的查询结果总结，包括：
1. 查询涉及的表及其关系
2. 查询的主要发现和数据特征
3. 对用户问题的直接回答
4. 如果有关联查询，说明关联的结果特点

总结要求：
1. 语言简洁明了
2. 重点突出查询结果
3. 如果是多表查询，需要说明表之间的关系
4. 总结不超过300字
"""
            
            # 使用LLM生成总结
            response = await self.llm.ainvoke(prompt)
            summary = response.content.strip()
            
            logger.info(f"生成的总结: {summary[:100]}...")
            return summary
            
        except Exception as e:
            logger.error(f"总结生成异常: {str(e)}")
            return f"查询完成，共返回 {query_result.get('row_count', 0)} 条记录。涉及的表: {tables_str}"
    
    async def process_database_query(
        self, 
        user_query: str, 
        user_id: int, 
        database_config_id: int,
        table_name: Optional[str] = None,
        conversation_id: Optional[int] = None,
        is_new_conversation: bool = False
    ) -> Dict[str, Any]:
        """
        处理数据库智能问数查询的主要工作流（基于保存的表元数据）
        
        新流程：
        1. 根据database_config_id获取数据库配置
        2. 创建数据库连接
        3. 从系统数据库读取表元数据（只包含启用问答的表）
        4. 根据表元数据生成SQL
        5. 执行SQL查询
        6. 查询数据后处理成表格形式
        7. 生成数据总结
        8. 返回结果
        
        Args:
            user_query: 用户问题
            user_id: 用户ID
            database_config_id: 数据库配置ID
            table_name: 表名（可选）
            conversation_id: 对话ID
            is_new_conversation: 是否为新对话
            
        Returns:
            包含查询结果的字典
        """
        try:
            logger.info(f"开始执行数据库查询工作流 - 用户ID: {user_id}, 数据库配置ID: {database_config_id}, 查询: {user_query[:50]}...")
            
            # 步骤1: 根据database_config_id获取数据库配置并创建连接
            connection_result = await self._connect_database(user_id, database_config_id)
            if not connection_result['success']:
                raise DatabaseConnectionError(connection_result['message'])
            
            logger.info("数据库连接成功")
            
            # 步骤2: 从系统数据库读取表元数据（只包含启用问答的表）
            tables_info = await self._get_saved_tables_metadata(user_id, database_config_id)
            
            logger.info(f"表元数据读取完成 - 共{len(tables_info)}个启用问答的表")
            
            # 步骤3: 根据表元数据选择相关表并生成SQL
            target_tables, target_schemas = await self._select_target_table(user_query, tables_info)
            sql_query = await self._generate_sql_query(user_query, target_tables, target_schemas)
            
            logger.info(f"SQL生成完成 - 目标表: {', '.join(target_tables)}")
            
            # 步骤4: 执行SQL查询
            query_result = await self._execute_database_query(user_id, sql_query)
            logger.info("查询执行完成")
            
            # 步骤5: 查询数据后处理成表格形式
            table_data = self._convert_query_result_to_table_data(query_result)
            
            # 步骤6: 生成数据总结
            summary = await self._generate_database_summary(user_query, query_result, ', '.join(target_tables))
            
            # 步骤7: 返回结果
            return {
                'success': True,
                'data': {
                    **table_data,
                    'generated_sql': sql_query,
                    'summary': summary,
                    'table_names': target_tables,
                    'query_result': query_result,
                    'metadata_source': 'saved_database'  # 标记元数据来源
                }
            }
            
        except SmartWorkflowError as e:
            logger.error(f"数据库工作流异常: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
        except Exception as e:
            logger.error(f"数据库工作流未知异常: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'系统异常: {str(e)}',
                'error_type': 'SystemError'
            }