import pandas as pd
import pymysql
import psycopg2
import pyodbc
import tempfile
import os
from typing import Dict, Any, List
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_community.chat_models import ChatZhipuAI
from langchain_core.messages import HumanMessage

# 在 SmartQueryService 类中添加方法

from .table_metadata_service import TableMetadataService

class SmartQueryService:
    """
    智能问数服务基类
    """
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.table_metadata_service = None
    
    def set_db_session(self, db_session):
        """设置数据库会话"""
        self.table_metadata_service = TableMetadataService(db_session)
    
    async def _run_in_executor(self, func, *args):
        """在线程池中运行阻塞函数"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, func, *args)

class ExcelAnalysisService(SmartQueryService):
    """
    Excel数据分析服务
    """
    def __init__(self):
        super().__init__()
        self.user_dataframes = {}  # 存储用户的DataFrame
        
    def analyze_dataframe(self, df: pd.DataFrame, filename: str) -> Dict[str, Any]:
        """
        分析DataFrame并返回基本信息
        """
        try:
            # 基本统计信息
            rows, columns = df.shape
            
            # 列信息
            column_info = []
            for col in df.columns:
                col_info = {
                    'name': col,
                    'dtype': str(df[col].dtype),
                    'null_count': int(df[col].isnull().sum()),
                    'unique_count': int(df[col].nunique())
                }
                
                # 如果是数值列，添加统计信息
                if pd.api.types.is_numeric_dtype(df[col]):
                    df.fillna({col:0})  #数值列，将空值补0
                    col_info.update({
                        'mean': float(df[col].mean()) if not df[col].isnull().all() else None,
                        'std': float(df[col].std()) if not df[col].isnull().all() else None,
                        'min': float(df[col].min()) if not df[col].isnull().all() else None,
                        'max': float(df[col].max()) if not df[col].isnull().all() else None
                    })
                
                column_info.append(col_info)
            
            # 数据预览（前5行）
            preview_data = df.head().fillna('').to_dict('records')
            
            # 数据质量检查
            quality_issues = []
            
            # 检查缺失值
            missing_cols = df.columns[df.isnull().any()].tolist()
            if missing_cols:
                quality_issues.append({
                    'type': 'missing_values',
                    'description': f'以下列存在缺失值: {", ".join(map(str, missing_cols))}',
                    'columns': missing_cols
                })
            
            # 检查重复行
            duplicate_count = df.duplicated().sum()
            if duplicate_count > 0:
                quality_issues.append({
                    'type': 'duplicate_rows',
                    'description': f'发现 {duplicate_count} 行重复数据',
                    'count': int(duplicate_count)
                })
            
            return {
                'filename': filename,
                'rows': rows,
                'columns': columns,
                'column_names': [str(col) for col in df.columns.tolist()],
                'column_info': column_info,
                'preview': preview_data,
                'quality_issues': quality_issues,
                'memory_usage': f"{df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB"
            }
            
        except Exception as e:
            print(e)
            raise Exception(f"DataFrame分析失败: {str(e)}")
    
    def _create_pandas_agent(self, df: pd.DataFrame):
        """
        创建pandas代理
        """
        try:
            # 使用智谱AI作为LLM
            llm = ChatZhipuAI(
                model="glm-4",
                api_key=os.getenv("ZHIPUAI_API_KEY"),
                temperature=0.1
            )
            
            # 创建pandas代理
            agent = create_pandas_dataframe_agent(
                llm=llm,
                df=df,
                verbose=True,
                return_intermediate_steps=True,
                handle_parsing_errors=True,
                max_iterations=3,
                early_stopping_method="force",
                allow_dangerous_code=True  # 允许执行代码以支持数据分析
            )
            
            return agent
            
        except Exception as e:
            raise Exception(f"创建pandas代理失败: {str(e)}")
    
    def _execute_pandas_query(self, agent, query: str) -> Dict[str, Any]:
        """
        执行pandas查询
        """
        try:
            # 执行查询
            # 使用invoke方法来处理有多个输出键的情况
            agent_result = agent.invoke({"input": query})
            # 提取主要结果
            result = agent_result.get('output', agent_result)
            
            # 解析结果
            if isinstance(result, pd.DataFrame):
                # 如果结果是DataFrame
                data = result.fillna('').to_dict('records')
                columns = result.columns.tolist()
                total = len(result)
                
                return {
                    'data': data,
                    'columns': columns,
                    'total': total,
                    'result_type': 'dataframe'
                }
            else:
                # 如果结果是其他类型（字符串、数字等）
                return {
                    'data': [{'result': str(result)}],
                    'columns': ['result'],
                    'total': 1,
                    'result_type': 'scalar'
                }
                
        except Exception as e:
            raise Exception(f"pandas查询执行失败: {str(e)}")
    
    async def execute_natural_language_query(
        self, 
        query: str, 
        user_id: int, 
        page: int = 1, 
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        执行自然语言查询
        """
        try:
            # 查找用户的临时文件
            temp_dir = tempfile.gettempdir()
            user_files = [f for f in os.listdir(temp_dir) 
                         if f.startswith(f"excel_{user_id}_") and f.endswith('.pkl')]
            
            if not user_files:
                return {
                    'success': False,
                    'message': '未找到上传的Excel文件，请先上传文件'
                }
            
            # 使用最新的文件
            latest_file = sorted(user_files)[-1]
            file_path = os.path.join(temp_dir, latest_file)
            
            # 加载DataFrame
            df = pd.read_pickle(file_path)
            
            # 创建pandas代理
            agent = self._create_pandas_agent(df)
            
            # 执行查询
            query_result = await self._run_in_executor(
                self._execute_pandas_query, agent, query
            )
            
            # 分页处理
            total = query_result['total']
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            
            paginated_data = query_result['data'][start_idx:end_idx]
            
            # 生成AI总结
            summary = await self._generate_summary(query, query_result, df)
            
            return {
                'success': True,
                'data': {
                    'data': paginated_data,
                    'columns': query_result['columns'],
                    'total': total,
                    'page': page,
                    'page_size': page_size,
                    'generated_code': f"# 基于自然语言查询: {query}\n# 使用LangChain Pandas代理执行",
                    'summary': summary,
                    'result_type': query_result['result_type']
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"查询执行失败: {str(e)}"
            }
    
    async def _generate_summary(self, query: str, result: Dict[str, Any], df: pd.DataFrame) -> str:
        """
        生成AI总结
        """
        try:
            llm = ChatZhipuAI(
                model="glm-4",
                api_key=os.getenv("ZHIPUAI_API_KEY"),
                temperature=0.3
            )
            
            # 构建总结提示
            prompt = f"""
            用户查询: {query}
            
            数据集信息:
            - 总行数: {len(df)}
            - 总列数: {len(df.columns)}
            - 列名: {', '.join(str(col) for col in df.columns.tolist())}
            
            查询结果:
            - 结果类型: {result['result_type']}
            - 结果行数: {result['total']}
            - 结果列数: {len(result['columns'])}
            
            请基于以上信息，用中文生成一个简洁的分析总结，包括:
            1. 查询的主要目的
            2. 关键发现
            3. 数据洞察
            4. 建议的后续分析方向
            
            总结应该专业、准确、易懂，控制在200字以内。
            """
            
            response = await self._run_in_executor(
                lambda: llm.invoke([HumanMessage(content=prompt)])
            )
            
            return response.content
            
        except Exception as e:
            return f"查询已完成，但生成总结时出现错误: {str(e)}"

class DatabaseQueryService(SmartQueryService):
    """
    数据库查询服务
    """
    def __init__(self):
        super().__init__()
        self.user_connections = {}  # 存储用户的数据库连接信息
    
    def _create_connection(self, config: Dict[str, str]):
        """
        创建数据库连接
        """
        db_type = config['type'].lower()
        
        try:
            if db_type == 'mysql':
                connection = pymysql.connect(
                    host=config['host'],
                    port=int(config['port']),
                    user=config['username'],
                    password=config['password'],
                    database=config['database'],
                    charset='utf8mb4'
                )
            elif db_type == 'postgresql':
                connection = psycopg2.connect(
                    host=config['host'],
                    port=int(config['port']),
                    user=config['username'],
                    password=config['password'],
                    database=config['database']
                )

            elif db_type == 'sqlserver':
                connection_string = (
                    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                    f"SERVER={config['host']},{config['port']};"
                    f"DATABASE={config['database']};"
                    f"UID={config['username']};"
                    f"PWD={config['password']}"
                )
                connection = pyodbc.connect(connection_string)
            else:
                raise Exception(f"不支持的数据库类型: {db_type}")
            
            return connection
            
        except Exception as e:
            raise Exception(f"数据库连接失败: {str(e)}")
    
    async def test_connection(self, config: Dict[str, str]) -> bool:
        """
        测试数据库连接
        """
        try:
            connection = await self._run_in_executor(self._create_connection, config)
            connection.close()
            return True
        except Exception:
            return False
    
    async def connect_database(self, config: Dict[str, str], user_id: int) -> Dict[str, Any]:
        """
        连接数据库并获取表列表
        """
        try:
            connection = await self._run_in_executor(self._create_connection, config)
            
            # 获取表列表
            tables = await self._run_in_executor(self._get_tables, connection, config['type'])
            
            # 存储连接信息
            self.user_connections[user_id] = {
                'config': config,
                'connection': connection,
                'connected_at': datetime.now()
            }
            
            return {
                'success': True,
                'data': {
                    'tables': tables,
                    'database_type': config['type'],
                    'database_name': config['database']
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"数据库连接失败: {str(e)}"
            }
    
    def _get_tables(self, connection, db_type: str) -> List[str]:
        """
        获取数据库表列表
        """
        cursor = connection.cursor()
        
        try:
            if db_type.lower() == 'mysql':
                cursor.execute("SHOW TABLES")
                tables = [row[0] for row in cursor.fetchall()]
            elif db_type.lower() == 'postgresql':
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                tables = [row[0] for row in cursor.fetchall()]

            elif db_type.lower() == 'sqlserver':
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_type = 'BASE TABLE'
                """)
                tables = [row[0] for row in cursor.fetchall()]
            else:
                tables = []
            
            return tables
            
        finally:
            cursor.close()
    
    async def get_table_schema(self, table_name: str, user_id: int) -> Dict[str, Any]:
        """
        获取表结构
        """
        try:
            if user_id not in self.user_connections:
                return {
                    'success': False,
                    'message': '数据库连接已断开，请重新连接'
                }
            
            connection = self.user_connections[user_id]['connection']
            db_type = self.user_connections[user_id]['config']['type']
            
            schema = await self._run_in_executor(
                self._get_table_schema, connection, table_name, db_type
            )
            
            return {
                'success': True,
                'data': {
                    'schema': schema,
                    'table_name': table_name
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"获取表结构失败: {str(e)}"
            }
    
    def _get_table_schema(self, connection, table_name: str, db_type: str) -> List[Dict[str, Any]]:
        """
        获取表结构信息
        """
        cursor = connection.cursor()
        
        try:
            if db_type.lower() == 'mysql':
                cursor.execute(f"DESCRIBE {table_name}")
                columns = cursor.fetchall()
                schema = [{
                    'column_name': col[0],
                    'data_type': col[1],
                    'is_nullable': 'YES' if col[2] == 'YES' else 'NO',
                    'column_key': col[3],
                    'column_default': col[4]
                } for col in columns]
            elif db_type.lower() == 'postgresql':
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = %s
                    ORDER BY ordinal_position
                """, (table_name,))
                columns = cursor.fetchall()
                schema = [{
                    'column_name': col[0],
                    'data_type': col[1],
                    'is_nullable': col[2],
                    'column_default': col[3]
                } for col in columns]

            else:
                schema = []
            
            return schema
            
        finally:
            cursor.close()
    
    async def execute_natural_language_query(
        self, 
        query: str, 
        table_name: str, 
        user_id: int, 
        page: int = 1, 
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        执行自然语言数据库查询
        """
        try:
            if user_id not in self.user_connections:
                return {
                    'success': False,
                    'message': '数据库连接已断开，请重新连接'
                }
            
            connection = self.user_connections[user_id]['connection']
            
            # 这里应该集成MCP服务来将自然语言转换为SQL
            # 目前先使用简单的实现
            sql_query = await self._convert_to_sql(query, table_name, connection)
            
            # 执行SQL查询
            result = await self._run_in_executor(
                self._execute_sql_query, connection, sql_query, page, page_size
            )
            
            # 生成AI总结
            summary = await self._generate_db_summary(query, result, table_name)
            
            result['generated_code'] = sql_query
            result['summary'] = summary
            
            return {
                'success': True,
                'data': result
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"数据库查询执行失败: {str(e)}"
            }
    
    async def _convert_to_sql(self, query: str, table_name: str, connection) -> str:
        """
        将自然语言转换为SQL查询
        TODO: 集成MCP服务
        """
        # 这是一个简化的实现，实际应该使用MCP服务
        # 根据常见的查询模式生成SQL
        
        query_lower = query.lower()
        
        if '所有' in query or '全部' in query or 'all' in query_lower:
            return f"SELECT * FROM {table_name} LIMIT 100"
        elif '统计' in query or '总数' in query or 'count' in query_lower:
            return f"SELECT COUNT(*) as total_count FROM {table_name}"
        elif '最近' in query or 'recent' in query_lower:
            return f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT 10"
        elif '分组' in query or 'group' in query_lower:
            # 简单的分组查询，需要根据实际表结构调整
            return f"SELECT COUNT(*) as count FROM {table_name} GROUP BY id LIMIT 10"
        else:
            # 默认查询
            return f"SELECT * FROM {table_name} LIMIT 20"
    
    def _execute_sql_query(self, connection, sql_query: str, page: int, page_size: int) -> Dict[str, Any]:
        """
        执行SQL查询
        """
        cursor = connection.cursor()
        
        try:
            # 执行查询
            cursor.execute(sql_query)
            
            # 获取列名
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            # 获取所有结果
            all_results = cursor.fetchall()
            total = len(all_results)
            
            # 分页
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_results = all_results[start_idx:end_idx]
            
            # 转换为字典格式
            data = []
            for row in paginated_results:
                row_dict = {}
                for i, value in enumerate(row):
                    if i < len(columns):
                        row_dict[columns[i]] = value
                data.append(row_dict)
            
            return {
                'data': data,
                'columns': columns,
                'total': total,
                'page': page,
                'page_size': page_size
            }
            
        finally:
            cursor.close()
    
    async def _generate_db_summary(self, query: str, result: Dict[str, Any], table_name: str) -> str:
        """
        生成数据库查询总结
        """
        try:
            llm = ChatZhipuAI(
                model="glm-4",
                api_key=os.getenv("ZHIPUAI_API_KEY"),
                temperature=0.3
            )
            
            prompt = f"""
            用户查询: {query}
            目标表: {table_name}
            
            查询结果:
            - 结果行数: {result['total']}
            - 结果列数: {len(result['columns'])}
            - 列名: {', '.join(result['columns'])}
            
            请基于以上信息，用中文生成一个简洁的数据库查询分析总结，包括:
            1. 查询的主要目的
            2. 关键数据发现
            3. 数据特征分析
            4. 建议的后续查询方向
            
            总结应该专业、准确、易懂，控制在200字以内。
            """
            
            response = await self._run_in_executor(
                lambda: llm.invoke([HumanMessage(content=prompt)])
            )
            
            return response.content
            
        except Exception as e:
            return f"查询已完成，但生成总结时出现错误: {str(e)}"

    # 在 SmartQueryService 类中添加方法
    
    from .table_metadata_service import TableMetadataService
    
    class SmartQueryService:
        def __init__(self):
            super().__init__()
            self.table_metadata_service = None
        
        def set_db_session(self, db_session):
            """设置数据库会话"""
            self.table_metadata_service = TableMetadataService(db_session)
        
        async def get_database_context(self, user_id: int, query: str) -> str:
            """获取数据库上下文信息用于问答"""
            if not self.table_metadata_service:
                return ""
            
            try:
                # 获取用户的表元数据
                table_metadata_list = self.table_metadata_service.get_user_table_metadata(user_id)
                
                if not table_metadata_list:
                    return ""
                
                # 构建数据库上下文
                context_parts = []
                context_parts.append("=== 数据库表信息 ===")
                
                for metadata in table_metadata_list:
                    table_info = []
                    table_info.append(f"表名: {metadata.table_name}")
                    
                    if metadata.table_comment:
                        table_info.append(f"表描述: {metadata.table_comment}")
                    
                    if metadata.qa_description:
                        table_info.append(f"业务说明: {metadata.qa_description}")
                    
                    # 添加列信息
                    if metadata.columns_info:
                        columns = []
                        for col in metadata.columns_info:
                            col_desc = f"{col['column_name']} ({col['data_type']})"
                            if col.get('column_comment'):
                                col_desc += f" - {col['column_comment']}"
                            columns.append(col_desc)
                        table_info.append(f"字段: {', '.join(columns)}")
                    
                    # 添加示例数据
                    if metadata.sample_data:
                        table_info.append(f"示例数据: {metadata.sample_data[:2]}")
                    
                    table_info.append(f"总行数: {metadata.row_count}")
                    
                    context_parts.append("\n".join(table_info))
                    context_parts.append("---")
                
                return "\n".join(context_parts)
                
            except Exception as e:
                logger.error(f"获取数据库上下文失败: {str(e)}")
                return ""
        
        async def execute_smart_query(self, query: str, user_id: int, **kwargs) -> Dict[str, Any]:
            """执行智能查询（集成表元数据）"""
            try:
                # 获取数据库上下文
                db_context = await self.get_database_context(user_id, query)
                
                # 构建增强的提示词
                enhanced_prompt = f"""
    {db_context}
    
    用户问题: {query}
    
    请基于上述数据库表信息，生成相应的SQL查询语句。
    注意：
    1. 使用准确的表名和字段名
    2. 考虑数据类型和约束
    3. 参考示例数据理解数据格式
    4. 生成高效的查询语句
    """
                
                # 调用原有的查询逻辑
                return await super().execute_smart_query(enhanced_prompt, user_id, **kwargs)
                
            except Exception as e:
                logger.error(f"智能查询失败: {str(e)}")
                return {
                    'success': False,
                    'message': f"查询失败: {str(e)}"
                }