from typing import Dict, Any, List, Optional, Union
import pandas as pd
import os
import tempfile
import json
import logging
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

from langchain_experimental.agents import create_pandas_dataframe_agent
from langchain_community.chat_models import ChatZhipuAI
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

from .smart_query import ExcelAnalysisService
from .excel_metadata_service import ExcelMetadataService
from ..core.config import get_settings

# 配置日志
logger = logging.getLogger(__name__)

class SmartWorkflowError(Exception):
    """智能工作流自定义异常"""
    pass

class FileLoadError(SmartWorkflowError):
    """文件加载异常"""
    pass

class FileSelectionError(SmartWorkflowError):
    """文件选择异常"""
    pass

class CodeExecutionError(SmartWorkflowError):
    """代码执行异常"""
    pass


class SmartWorkflowManager:
    """
    智能工作流管理器
    负责协调文件选择、代码生成和执行的完整流程
    """
    
    def __init__(self, db=None):
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.excel_service = ExcelAnalysisService()
        self.db = db
        if db:
            self.metadata_service = ExcelMetadataService(db)
        else:
            self.metadata_service = None
        
        # 获取当前LLM配置
        settings = get_settings()
        llm_config = settings.llm.get_current_config()
        
        # 根据配置动态选择LLM服务
        if settings.llm.provider == "zhipu":
            self.llm = ChatZhipuAI(
                model=llm_config["model"],
                api_key=llm_config["api_key"],
                temperature=llm_config["temperature"],
                streaming=False  # 禁用流式响应，避免pandas代理兼容性问题
            )
        else:
            # 使用ChatOpenAI兼容其他提供商
            self.llm = ChatOpenAI(
                model=llm_config["model"],
                api_key=llm_config["api_key"],
                base_url=llm_config["base_url"],
                temperature=llm_config["temperature"],
                max_tokens=llm_config["max_tokens"],
                streaming=False  # 禁用流式响应，避免pandas代理兼容性问题
            )
        
    async def _run_in_executor(self, func, *args):
        """在线程池中运行阻塞函数"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, func, *args)
    
    def _convert_dataframe_to_markdown(self, df_string: str) -> str:
        """
        将DataFrame的字符串表示转换为Markdown表格格式
        
        Args:
            df_string: DataFrame的字符串表示
            
        Returns:
            Markdown格式的表格字符串
        """
        try:
            lines = df_string.strip().split('\n')
            
            # 查找表格数据的开始位置
            table_start = -1
            for i, line in enumerate(lines):
                if '|' in line or (len(line.split()) > 1 and any(char.isdigit() for char in line)):
                    table_start = i
                    break
            
            if table_start == -1:
                return df_string  # 如果找不到表格，返回原始字符串
            
            # 提取表格行
            table_lines = []
            for line in lines[table_start:]:
                if line.strip() and not line.startswith('Name:') and not line.startswith('dtype:'):
                    table_lines.append(line.strip())
            
            if not table_lines:
                return df_string
            
            # 处理第一行作为表头
            if table_lines:
                # 检查是否已经是表格格式
                if '|' in table_lines[0]:
                    # 已经是表格格式，直接返回
                    markdown_lines = []
                    for i, line in enumerate(table_lines):
                        if i == 1 and not line.startswith('|'):
                            # 添加分隔行
                            cols = table_lines[0].count('|') + 1
                            separator = '|' + '---|' * (cols - 1) + '---|'
                            markdown_lines.append(separator)
                        markdown_lines.append(line)
                    return '\n'.join(markdown_lines)
                else:
                    # 转换为Markdown表格格式
                    markdown_lines = []
                    
                    # 处理表头
                    if len(table_lines) > 0:
                        # 假设第一行是索引和数据的混合
                        first_line = table_lines[0]
                        parts = first_line.split()
                        
                        if len(parts) > 1:
                            # 创建表头
                            header = '| 索引 | ' + ' | '.join(parts[1:]) + ' |'
                            markdown_lines.append(header)
                            
                            # 创建分隔行
                            separator = '|' + '---|' * len(parts) + ''
                            markdown_lines.append(separator)
                            
                            # 处理数据行
                            for line in table_lines[1:]:
                                if line.strip():
                                    parts = line.split()
                                    if len(parts) > 0:
                                        row = '| ' + ' | '.join(parts) + ' |'
                                        markdown_lines.append(row)
                    
                    if markdown_lines:
                        return '\n'.join(markdown_lines)
            
            return df_string  # 如果转换失败，返回原始字符串
            
        except Exception as e:
            logger.warning(f"DataFrame转Markdown失败: {str(e)}")
            return df_string  # 转换失败时返回原始字符串
    
    def _convert_dataframe_to_markdown(self, df_string: str) -> str:
        """
        将DataFrame的字符串表示转换为Markdown表格格式
        
        Args:
            df_string: DataFrame的字符串表示
            
        Returns:
            Markdown格式的表格字符串
        """
        try:
            lines = df_string.strip().split('\n')
            
            # 查找表格数据的开始位置
            table_start = -1
            for i, line in enumerate(lines):
                if '|' in line or (len(line.split()) > 1 and any(char.isdigit() for char in line)):
                    table_start = i
                    break
            
            if table_start == -1:
                return df_string  # 如果找不到表格，返回原始字符串
            
            # 提取表格行
            table_lines = []
            for line in lines[table_start:]:
                if line.strip() and not line.startswith('Name:') and not line.startswith('dtype:'):
                    table_lines.append(line.strip())
            
            if not table_lines:
                return df_string
            
            # 处理第一行作为表头
            if table_lines:
                # 检查是否已经是表格格式
                if '|' in table_lines[0]:
                    # 已经是表格格式，直接返回
                    markdown_lines = []
                    for i, line in enumerate(table_lines):
                        if i == 1 and not line.startswith('|'):
                            # 添加分隔行
                            cols = table_lines[0].count('|') + 1
                            separator = '|' + '---|' * (cols - 1) + '---|'
                            markdown_lines.append(separator)
                        markdown_lines.append(line)
                    return '\n'.join(markdown_lines)
                else:
                    # 转换为Markdown表格格式
                    markdown_lines = []
                    
                    # 处理表头
                    if len(table_lines) > 0:
                        # 假设第一行是索引和数据的混合
                        first_line = table_lines[0]
                        parts = first_line.split()
                        
                        if len(parts) > 1:
                            # 创建表头
                            header = '| 索引 | ' + ' | '.join(parts[1:]) + ' |'
                            markdown_lines.append(header)
                            
                            # 创建分隔行
                            separator = '|' + '---|' * len(parts) + ''
                            markdown_lines.append(separator)
                            
                            # 处理数据行
                            for line in table_lines[1:]:
                                if line.strip():
                                    parts = line.split()
                                    if len(parts) > 0:
                                        row = '| ' + ' | '.join(parts) + ' |'
                                        markdown_lines.append(row)
                    
                    if markdown_lines:
                        return '\n'.join(markdown_lines)
            
            return df_string  # 如果转换失败，返回原始字符串
            
        except Exception as e:
            logger.warning(f"DataFrame转Markdown失败: {str(e)}")
            return df_string  # 转换失败时返回原始字符串
    
    def _convert_dataframe_to_table_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        将DataFrame转换为前端Table组件可用的结构化数据
        
        Args:
            df: pandas DataFrame
            
        Returns:
            包含columns和data的字典
        """
        try:
            # 获取列信息
            columns = []
            for col in df.columns:
                columns.append({
                    'prop': str(col),
                    'label': str(col),
                    'width': 'auto'
                })
            
            # 获取数据
            data = []
            for index, row in df.iterrows():
                row_data = {'_index': str(index)}
                for col in df.columns:
                    # 处理各种数据类型
                    value = row[col]
                    if pd.isna(value):
                        row_data[str(col)] = ''
                    elif isinstance(value, (int, float)):
                        row_data[str(col)] = value
                    else:
                        row_data[str(col)] = str(value)
                data.append(row_data)
            
            return {
                'columns': columns,
                'data': data,
                'total': len(df)
            }
            
        except Exception as e:
            logger.warning(f"DataFrame转Table数据失败: {str(e)}")
            return {
                'columns': [{'prop': 'result', 'label': '结果'}],
                'data': [{'result': str(df)}],
                'total': 1
            }

    async def process_smart_query_stream(
        self, 
        user_query: str, 
        user_id: int, 
        conversation_id: Optional[int] = None,
        is_new_conversation: bool = False
    ):
        """
        流式处理智能问数查询的主要工作流
        实时推送每个工作流步骤
        
        Args:
            user_query: 用户问题
            user_id: 用户ID
            conversation_id: 对话ID
            is_new_conversation: 是否为新对话
            
        Yields:
            包含工作流步骤或最终结果的字典
        """
        workflow_steps = []
        
        try:
            logger.info(f"开始执行流式智能查询工作流 - 用户ID: {user_id}, 查询: {user_query[:50]}...")
            
            # 步骤1: 加载文件列表
            try:
                step_data = {
                    'type': 'workflow_step',
                    'step': 'file_loading',
                    'status': 'running',
                    'message': '正在加载用户文件列表...',
                    'timestamp': datetime.now().isoformat()
                }
                yield step_data
                
                if is_new_conversation or conversation_id is None:
                    file_list = await self._load_user_file_list(user_id)
                    if not file_list:
                        raise FileLoadError('未找到可用的Excel文件，请先上传文件')
                else:
                    file_list = await self._load_user_file_list(user_id)
                
                step_completed = {
                    'type': 'workflow_step',
                    'step': 'file_loading',
                    'status': 'completed',
                    'message': f'成功加载{len(file_list)}个文件',
                    'details': {'file_count': len(file_list)},
                    'timestamp': datetime.now().isoformat()
                }
                workflow_steps.append(step_completed)
                yield step_completed
                logger.info(f"文件加载完成 - 共{len(file_list)}个文件")
                
            except FileLoadError as e:
                step_failed = {
                    'type': 'workflow_step',
                    'step': 'file_loading',
                    'status': 'failed',
                    'message': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                workflow_steps.append(step_failed)
                yield step_failed
                
                yield {
                    'type': 'final_result',
                    'success': False,
                    'message': str(e),
                    'workflow_steps': workflow_steps
                }
                return
            
            # 步骤2: 智能文件选择
            try:
                step_data = {
                    'type': 'workflow_step',
                    'step': 'file_selection',
                    'status': 'running',
                    'message': '正在分析问题并选择相关文件...',
                    'timestamp': datetime.now().isoformat()
                }
                yield step_data
                
                selected_files = await self._select_relevant_files(user_query, file_list)
                
                if not selected_files:
                    raise FileSelectionError('未找到与问题相关的Excel文件')
                
                step_completed = {
                    'type': 'workflow_step',
                    'step': 'file_selection',
                    'status': 'completed',
                    'message': f'选择了{len(selected_files)}个相关文件',
                    'selected_files': [f['filename'] for f in selected_files],
                    'details': {'selection_count': len(selected_files)},
                    'timestamp': datetime.now().isoformat()
                }
                workflow_steps.append(step_completed)
                yield step_completed
                logger.info(f"文件选择完成 - 选择了{len(selected_files)}个文件")
                
            except FileSelectionError as e:
                step_failed = {
                    'type': 'workflow_step',
                    'step': 'file_selection',
                    'status': 'failed',
                    'message': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                workflow_steps.append(step_failed)
                yield step_failed
                
                yield {
                    'type': 'final_result',
                    'success': False,
                    'message': str(e),
                    'workflow_steps': workflow_steps
                }
                return
            
            # 步骤3: 数据加载
            try:
                step_data = {
                    'type': 'workflow_step',
                    'step': 'data_loading',
                    'status': 'running',
                    'message': '正在加载Excel数据...',
                    'timestamp': datetime.now().isoformat()
                }
                yield step_data
                
                dataframes = await self._load_selected_dataframes(selected_files, user_id)
                
                step_completed = {
                    'type': 'workflow_step',
                    'step': 'data_loading',
                    'status': 'completed',
                    'message': f'成功加载{len(dataframes)}个数据表',
                    'details': {
                        'dataframe_count': len(dataframes),
                        'total_rows': sum(len(df) for df in dataframes.values())
                    },
                    'timestamp': datetime.now().isoformat()
                }
                workflow_steps.append(step_completed)
                yield step_completed
                logger.info(f"数据加载完成 - 共{len(dataframes)}个数据表")
                
            except Exception as e:
                step_failed = {
                    'type': 'workflow_step',
                    'step': 'data_loading',
                    'status': 'failed',
                    'message': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                workflow_steps.append(step_failed)
                yield step_failed
                
                yield {
                    'type': 'final_result',
                    'success': False,
                    'message': str(e),
                    'workflow_steps': workflow_steps
                }
                return
            
            # 步骤4: 代码执行
            try:
                step_data = {
                    'type': 'workflow_step',
                    'step': 'code_execution',
                    'status': 'running',
                    'message': '正在生成并执行Python代码...',
                    'timestamp': datetime.now().isoformat()
                }
                yield step_data
                
                result = await self._execute_smart_query(user_query, dataframes, selected_files)
                
                step_completed = {
                    'type': 'workflow_step',
                    'step': 'code_execution',
                    'status': 'completed',
                    'message': '成功执行Python代码分析',
                    'details': {
                        'result_type': result.get('result_type'),
                        'data_count': result.get('total', 0)
                    },
                    'timestamp': datetime.now().isoformat()
                }
                workflow_steps.append(step_completed)
                yield step_completed
                logger.info("查询执行完成")
                
                # 发送最终结果
                yield {
                    'type': 'final_result',
                    'success': True,
                    'data': result,
                    'workflow_steps': workflow_steps
                }
                
            except CodeExecutionError as e:
                error_msg = f'代码执行失败: {str(e)}'
                step_failed = {
                    'type': 'workflow_step',
                    'step': 'code_execution',
                    'status': 'failed',
                    'message': error_msg,
                    'timestamp': datetime.now().isoformat()
                }
                workflow_steps.append(step_failed)
                yield step_failed
                logger.error(error_msg)
                
                yield {
                    'type': 'final_result',
                    'success': False,
                    'message': error_msg,
                    'workflow_steps': workflow_steps
                }
                return
            
        except SmartWorkflowError as e:
            logger.error(f"智能工作流异常: {str(e)}")
            yield {
                'type': 'final_result',
                'success': False,
                'message': str(e),
                'workflow_steps': workflow_steps
            }
        except Exception as e:
            logger.error(f"智能工作流未知异常: {str(e)}", exc_info=True)
            yield {
                'type': 'final_result',
                'success': False,
                'message': f'系统异常: {str(e)}',
                'workflow_steps': workflow_steps
            }
    
    async def process_smart_query(
        self, 
        user_query: str, 
        user_id: int, 
        conversation_id: Optional[int] = None,
        is_new_conversation: bool = False
    ) -> Dict[str, Any]:
        """
        处理智能问数查询的主要工作流
        
        Args:
            user_query: 用户问题
            user_id: 用户ID
            conversation_id: 对话ID
            is_new_conversation: 是否为新对话
            
        Returns:
            包含查询结果的字典
        """
        workflow_steps = []
        
        try:
            logger.info(f"开始执行智能查询工作流 - 用户ID: {user_id}, 查询: {user_query[:50]}...")
            
            # 步骤1: 加载文件列表
            try:
                if is_new_conversation or conversation_id is None:
                    file_list = await self._load_user_file_list(user_id)
                    if not file_list:
                        raise FileLoadError('未找到可用的Excel文件，请先上传文件')
                else:
                    file_list = await self._load_user_file_list(user_id)
                
                workflow_steps.append({
                    'step': 'file_loading',
                    'status': 'completed',
                    'message': f'成功加载{len(file_list)}个文件',
                    'details': {'file_count': len(file_list)}
                })
                logger.info(f"文件加载完成 - 共{len(file_list)}个文件")
                
            except FileLoadError as e:
                workflow_steps.append({
                    'step': 'file_loading',
                    'status': 'failed',
                    'message': str(e)
                })
                return {
                    'success': False,
                    'message': str(e),
                    'workflow_steps': workflow_steps
                }
            
            # 步骤2: 智能文件选择
            try:
                selected_files = await self._select_relevant_files(user_query, file_list)
                
                if not selected_files:
                    raise FileSelectionError('未找到与问题相关的Excel文件')
                
                workflow_steps.append({
                    'step': 'file_selection',
                    'status': 'completed',
                    'message': f'选择了{len(selected_files)}个相关文件',
                    'selected_files': [f['filename'] for f in selected_files],
                    'details': {'selection_count': len(selected_files)}
                })
                logger.info(f"文件选择完成 - 选中{len(selected_files)}个文件")
                
            except FileSelectionError as e:
                workflow_steps.append({
                    'step': 'file_selection',
                    'status': 'failed',
                    'message': str(e)
                })
                return {
                    'success': False,
                    'message': str(e),
                    'workflow_steps': workflow_steps
                }
            
            # 步骤3: 加载DataFrame
            try:
                dataframes = await self._load_selected_dataframes(selected_files, user_id)
                
                if not dataframes:
                    raise FileLoadError('无法加载选中的Excel文件数据')
                
                workflow_steps.append({
                    'step': 'dataframe_loading',
                    'status': 'completed',
                    'message': f'成功加载{len(dataframes)}个数据表',
                    'details': {
                        'dataframe_count': len(dataframes),
                        'total_rows': sum(len(df) for df in dataframes.values())
                    }
                })
                logger.info(f"DataFrame加载完成 - {len(dataframes)}个数据表")
                
            except Exception as e:
                error_msg = f'数据加载失败: {str(e)}'
                workflow_steps.append({
                    'step': 'dataframe_loading',
                    'status': 'failed',
                    'message': error_msg
                })
                logger.error(error_msg)
                return {
                    'success': False,
                    'message': error_msg,
                    'workflow_steps': workflow_steps
                }
            
            # 步骤4: 执行查询
            try:
                result = await self._execute_smart_query(user_query, dataframes, selected_files)
                
                workflow_steps.append({
                    'step': 'code_execution',
                    'status': 'completed',
                    'message': '成功执行pandas代码分析',
                    'details': {
                        'result_type': result.get('result_type'),
                        'data_count': result.get('total', 0)
                    }
                })
                logger.info("查询执行完成")
                
                return {
                    'success': True,
                    'data': result,
                    'workflow_steps': workflow_steps
                }
                
            except CodeExecutionError as e:
                error_msg = f'代码执行失败: {str(e)}'
                workflow_steps.append({
                    'step': 'code_execution',
                    'status': 'failed',
                    'message': error_msg
                })
                logger.error(error_msg)
                return {
                    'success': False,
                    'message': error_msg,
                    'workflow_steps': workflow_steps
                }
            
        except SmartWorkflowError as e:
            logger.error(f"智能工作流异常: {str(e)}")
            return {
                'success': False,
                'message': str(e),
                'workflow_steps': workflow_steps
            }
        except Exception as e:
            logger.error(f"工作流执行失败: {str(e)}", exc_info=True)
            workflow_steps.append({
                'step': 'error',
                'status': 'failed',
                'message': f'系统错误: {str(e)}'
            })
            return {
                'success': False,
                'message': f'工作流执行失败: {str(e)}',
                'workflow_steps': workflow_steps
            }
    
    async def _load_user_file_list(self, user_id: int) -> List[Dict[str, Any]]:
        """
        加载用户的所有文件列表信息
        """
        try:
            # 从数据库获取用户的文件元数据
            file_metadata = []
            if self.metadata_service:
                files, total = await self._run_in_executor(
                    self.metadata_service.get_user_files, user_id
                )
                file_metadata = files
            else:
                logger.warning("metadata_service未初始化，跳过数据库文件查询")
            
            # 同时检查临时目录中的文件
            temp_dir = tempfile.gettempdir()
            temp_files = [f for f in os.listdir(temp_dir) 
                         if f.startswith(f"excel_{user_id}_") and f.endswith('.pkl')]
            
            file_list = []
            
            # 合并数据库和临时文件信息
            for metadata in file_metadata:
                # 获取默认sheet的信息
                default_sheet = metadata.default_sheet or (metadata.sheet_names[0] if metadata.sheet_names else None)
                columns = metadata.columns_info.get(default_sheet, []) if metadata.columns_info and default_sheet else []
                row_count = metadata.total_rows.get(default_sheet, 0) if metadata.total_rows and default_sheet else 0
                column_count = metadata.total_columns.get(default_sheet, 0) if metadata.total_columns and default_sheet else 0
                
                file_info = {
                    'id': metadata.id,
                    'filename': metadata.original_filename,
                    'file_path': metadata.file_path,
                    'columns': columns,
                    'row_count': row_count,
                    'column_count': column_count,
                    'description': f'Excel文件，包含{str(len(metadata.sheet_names))}个工作表' if metadata.sheet_names else '',
                    'upload_time': metadata.upload_time.isoformat() if metadata.upload_time else None
                }
                file_list.append(file_info)
            
            return file_list
            
        except Exception as e:
            print(f"加载文件列表失败: {e}")
            return []
    
    async def _select_relevant_files(
        self, 
        user_query: str, 
        file_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        根据用户问题智能选择相关的Excel文件
        
        Args:
            user_query: 用户问题
            file_list: 可用文件列表
            
        Returns:
            选中的文件列表
            
        Raises:
            FileSelectionError: 文件选择过程中发生错误
        """
        if not file_list:
            logger.warning("文件列表为空，无法进行文件选择")
            raise FileSelectionError("没有可用的文件进行选择")
        
        # 如果只有一个文件，直接返回
        if len(file_list) == 1:
            logger.info("只有一个文件，直接选择")
            return file_list
        
        try:
            logger.info(f"开始智能文件选择 - 可用文件数: {len(file_list)}")
            
            # 构建文件选择提示
            file_descriptions = []
            for i, file_info in enumerate(file_list):
                # 确保数值类型转换为字符串
                row_count = str(file_info.get('row_count', 'unknown'))
                column_count = str(file_info.get('column_count', 'unknown'))
                columns = file_info.get('columns', [])
                # 确保列名都是字符串类型
                column_names = ', '.join(str(col) for col in columns)
                
                desc = f"""
文件{i+1}: {file_info['filename']}
- 行数: {row_count}
- 列数: {column_count}
- 列名: {column_names}
- 描述: {file_info.get('description', '无描述')}
"""
                file_descriptions.append(desc)
            
            prompt = f"""
用户问题: {user_query}

可用的Excel文件:
{chr(10).join(file_descriptions)}

请分析用户问题，选择最相关的Excel文件来回答问题。
如果问题涉及多个文件的数据关联，可以选择多个文件。
如果问题只涉及特定类型的数据，只选择相关的文件。

请返回JSON格式的结果，包含选中文件的索引（从1开始）:
{"selected_files": [1, 2, ...], "reason": "选择理由"}
"""
            
            # 调用LLM进行文件选择
            response = await self._run_in_executor(
                self.llm.invoke, [HumanMessage(content=prompt)]
            )
            
            # 解析LLM响应
            try:
                import re
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    selected_indices = result.get('selected_files', [])
                    reason = result.get('reason', '未提供理由')
                    
                    # 转换索引为实际文件
                    selected_files = []
                    for idx in selected_indices:
                        if 1 <= idx <= len(file_list):
                            selected_files.append(file_list[idx - 1])
                    
                    if not selected_files:
                        logger.warning("LLM选择结果为空，回退到选择所有文件")
                        return file_list
                    
                    logger.info(f"成功选择{len(selected_files)}个文件: {[f['filename'] for f in selected_files]}")
                    logger.info(f"选择理由: {reason}")
                    return selected_files
                else:
                    logger.warning("无法解析LLM响应中的JSON，回退到选择所有文件")
                    return file_list
                    
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"解析LLM响应失败: {str(e)}，回退到选择所有文件")
                return file_list
                
        except Exception as e:
            logger.error(f"文件选择过程中发生错误: {str(e)}")
            # 出错时返回所有文件作为备选方案
            logger.info("回退到选择所有文件")
            return file_list
    
    async def _load_selected_dataframes(
        self, 
        selected_files: List[Dict[str, Any]], 
        user_id: int
    ) -> Dict[str, pd.DataFrame]:
        """
        加载选中的Excel文件为DataFrame
        
        Args:
            selected_files: 选中的文件列表
            user_id: 用户ID
            
        Returns:
            文件名到DataFrame的映射
            
        Raises:
            FileLoadError: 文件加载失败
        """
        if not selected_files:
            raise FileLoadError("没有选中的文件需要加载")
        
        dataframes = {}
        temp_dir = tempfile.gettempdir()
        failed_files = []
        
        logger.info(f"开始加载{len(selected_files)}个选中的文件")
        
        for file_info in selected_files:
            filename = file_info['filename']
            try:
                logger.debug(f"正在加载文件: {filename}")
                
                # 查找对应的pickle文件
                pickle_files = [f for f in os.listdir(temp_dir) 
                               if f.startswith(f"excel_{user_id}_") and f.endswith('.pkl')]
                
                if pickle_files:
                    # 使用最新的文件
                    latest_file = sorted(pickle_files)[-1]
                    pickle_path = os.path.join(temp_dir, latest_file)
                    
                    logger.debug(f"从pickle文件加载: {pickle_path}")
                    df = pd.read_pickle(pickle_path)
                else:
                    # 如果没有pickle文件，尝试从原始文件路径加载
                    file_path = file_info.get('file_path')
                    if not file_path or not os.path.exists(file_path):
                        logger.warning(f"文件路径不存在: {file_path}")
                        failed_files.append(filename)
                        continue
                    
                    logger.debug(f"从原始文件加载: {file_path}")
                    if file_path.endswith('.csv'):
                        df = pd.read_csv(file_path, encoding='utf-8')
                    else:
                        df = pd.read_excel(file_path)
                
                # 验证DataFrame
                if df.empty:
                    logger.warning(f"文件 {filename} 加载后为空")
                    failed_files.append(filename)
                    continue
                
                dataframes[filename] = df
                logger.info(f"成功加载文件 {filename}: {len(df)} 行, {len(df.columns)} 列")
                
            except pd.errors.EmptyDataError:
                logger.error(f"文件 {filename} 为空或格式错误")
                failed_files.append(filename)
            except pd.errors.ParserError as e:
                logger.error(f"文件 {filename} 解析错误: {str(e)}")
                failed_files.append(filename)
            except Exception as e:
                logger.error(f"加载文件 {filename} 失败: {str(e)}")
                failed_files.append(filename)
        
        if not dataframes:
            error_msg = f"所有文件加载失败。失败文件: {', '.join(failed_files)}"
            logger.error(error_msg)
            raise FileLoadError(error_msg)
        
        if failed_files:
            logger.warning(f"部分文件加载失败: {', '.join(failed_files)}")
        
        logger.info(f"成功加载{len(dataframes)}个文件，失败{len(failed_files)}个文件")
        return dataframes
    
    async def _execute_smart_query(
        self, 
        user_query: str, 
        dataframes: Dict[str, pd.DataFrame], 
        selected_files: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        执行智能查询，生成和运行pandas代码
        
        Args:
            user_query: 用户查询
            dataframes: 加载的数据框字典
            selected_files: 选中的文件信息
            
        Returns:
            查询结果字典
            
        Raises:
            CodeExecutionError: 代码执行失败
        """
        if not dataframes:
            raise CodeExecutionError("没有可用的数据文件")
        
        logger.info(f"开始执行智能查询: {user_query[:50]}...")
        
        try:
            # 如果有多个DataFrame，合并或选择主要的一个
            if len(dataframes) == 1:
                main_df = list(dataframes.values())[0]
                main_filename = list(dataframes.keys())[0]
            else:
                # 多个文件时，选择行数最多的作为主DataFrame
                main_filename = max(dataframes.keys(), key=lambda k: len(dataframes[k]))
                main_df = dataframes[main_filename]
            
            logger.info(f"选择主数据文件: {main_filename}, 行数: {len(main_df)}, 列数: {len(main_df.columns)}")
            
            # 验证数据框
            if main_df.empty:
                raise CodeExecutionError(f"主数据文件 {main_filename} 为空")
            
            # 使用PythonAstREPLTool替代pandas代理
            try:
                from langchain_experimental.tools import PythonAstREPLTool
                from langchain_core.output_parsers import JsonOutputKeyToolsParser
                from langchain_core.prompts import ChatPromptTemplate
                
                # 准备数据框字典，支持多个文件
                df_locals = {}
                for filename, df in dataframes.items():
                    # 使用简化的变量名
                    var_name = f"df_{len(df_locals) + 1}" if len(dataframes) > 1 else "df"
                    df_locals[var_name] = df
                
                # 创建Python代码执行工具
                python_tool = PythonAstREPLTool(locals=df_locals)
                
                logger.info(f"创建Python工具成功，可用数据框: {list(df_locals.keys())}")
                
            except Exception as e:
                raise CodeExecutionError(f"创建Python工具失败: {str(e)}")
            
            # 构建数据集信息
            dataset_info = []
            for var_name, df in df_locals.items():
                dataset_info.append(f"- {var_name}: {len(df)}行 x {len(df.columns)}列，列名: {', '.join(str(col) for col in df.columns.tolist())}")
            
            # 构建系统提示
            system_prompt = f"""
你可以访问以下pandas数据框:
{chr(10).join(dataset_info)}

请根据用户提出的问题，编写Python代码来回答。要求：
1. 只返回代码，不返回其他内容
2. 只允许使用pandas和内置库
3. 确保代码能够直接执行并返回结果
4. 返回的结果应该是详细的、完整的数据，而不仅仅是简单答案
5. 当用户询问最高、最低、排名等问题时，除了返回答案本身，还要返回相关的详细数据
6. 结果应该包含足够的上下文信息，让用户能够验证和理解答案
7. 优先返回DataFrame格式的结果，便于展示为表格
8. 如果是统计分析，要包含相关的数值、百分比、排名等详细信息

示例：
- 如果问"哪个项目类型合同额最高"，不仅要返回项目类型，还要返回该类型的具体合同额、占比、相关项目数量等
- 如果问"销售额最高的产品"，要返回产品名称、销售额、销售数量、市场占比等完整信息
- 结果格式优先使用DataFrame，包含多列相关数据
"""
            
            # 创建提示模板
            prompt = ChatPromptTemplate([
                ("system", system_prompt),
                ("user", "{question}")
            ])
            
            # 创建解析器
            parser = JsonOutputKeyToolsParser(key_name=python_tool.name, first_tool_only=True)
            
            # 绑定工具到LLM
            llm_with_tools = self.llm.bind_tools([python_tool])
            
            # 创建执行链
            llm_chain = prompt | llm_with_tools | parser | python_tool
            
            # 执行查询
            try:
                logger.debug("开始执行Python工具查询")
                result = await self._run_in_executor(llm_chain.invoke, {"question": user_query})
                logger.debug(f"查询执行完成，结果: {str(result)[:200]}...")
            except Exception as e:
                error_msg = f"Python工具执行失败: {str(e)}"
                logger.error(error_msg)
                raise CodeExecutionError(error_msg)
            
            # 处理结果
            
            try:
                # 检查结果是否为pandas DataFrame
                if isinstance(result, pd.DataFrame):
                    # 转换为表格数据
                    table_data = self._convert_dataframe_to_table_data(result)
                    
                    data = table_data['data']
                    columns = table_data['columns'] 
                    total = table_data['total']
                    result_type = 'table_data'
                    logger.info(f"处理DataFrame结果: {len(result)}行 x {len(result.columns)}列")
                # PythonAstREPLTool返回的是字符串结果
                elif isinstance(result, str):
                    # 尝试解析结果中的数据
                    result_lines = result.strip().split('\n')
                    
                    # 检查是否是DataFrame的字符串表示
                    if any('DataFrame' in line or ('|' in line and len([l for l in result_lines if '|' in l]) > 1) for line in result_lines):
                        # 尝试将DataFrame字符串转换为Markdown表格
                        markdown_table = self._convert_dataframe_to_markdown(result)
                        data = [{'result': markdown_table}]
                        columns = ['result']
                        total = 1
                        result_type = 'markdown_table'
                    else:
                        # 简单的数值或文本结果
                        data = [{'result': result}]
                        columns = ['result']
                        total = 1
                        result_type = 'text'
                elif isinstance(result, (int, float, bool)):
                    data = [{'result': str(result)}]
                    columns = ['result']
                    total = 1
                    result_type = 'scalar'
                else:
                    # 处理其他类型的结果
                    data = [{'result': str(result)}]
                    columns = ['result']
                    total = 1
                    result_type = 'other'
                
                logger.info(f"结果处理完成: {result_type}, 数据行数: {total}")
                
            except Exception as e:
                error_msg = f"结果处理失败: {str(e)}"
                logger.error(error_msg)
                raise CodeExecutionError(error_msg)
            
            # 生成总结
            try:
                summary = await self._generate_query_summary(user_query, result, main_df)
            except Exception as e:
                logger.warning(f"生成总结失败: {str(e)}")
                summary = f"基于数据分析完成查询，共处理{len(main_df)}行数据。"
            
            return {
                'data': data,
                'columns': columns,
                'total': total,
                'result_type': result_type,
                'summary': summary,
                'used_files': list(dataframes.keys()),
                'generated_code': f"# 基于文件: {', '.join(dataframes.keys())}\n# 查询: {user_query}\n# 使用LangChain Python工具执行",
                'data_info': {
                    'source_files': list(dataframes.keys()),
                    'dataframes': {name: {'rows': len(df), 'columns': len(df.columns), 'column_names': [str(col) for col in df.columns.tolist()]} for name, df in dataframes.items()}
                }
            }
            
        except CodeExecutionError:
            raise
        except Exception as e:
            error_msg = f"查询执行过程中发生未知错误: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise CodeExecutionError(error_msg)
    
    async def _generate_query_summary(
        self, 
        query: str, 
        result: Any, 
        df: pd.DataFrame
    ) -> str:
        """
        生成查询结果的AI总结
        """
        try:
            logger.debug("开始生成查询总结")
            
            # 安全地获取数据集信息
            try:
                dataset_info = f"""
数据集信息:
- 总行数: {len(df)}
- 总列数: {len(df.columns)}
- 列名: {', '.join(str(col) for col in df.columns.tolist())}
"""
            except Exception as e:
                logger.warning(f"获取数据集信息失败: {str(e)}")
                dataset_info = "数据集信息: 无法获取"
            
            # 安全地处理查询结果
            try:
                if isinstance(result, pd.DataFrame):
                    if len(result) > 0:
                        result_preview = result.head(3).to_string(max_cols=5, max_rows=3)
                    else:
                        result_preview = "查询结果为空"
                else:
                    result_preview = str(result)[:500]  # 限制长度避免过长
            except Exception as e:
                logger.warning(f"生成结果预览失败: {str(e)}")
                result_preview = "无法生成结果预览"
            
            prompt = f"""
用户查询: {query}

{dataset_info}

查询结果: {result_preview}...

请生成一个简洁的中文总结，说明:
1. 查询的主要发现
2. 数据的关键特征
3. 结果的业务含义

总结应该在100字以内，通俗易懂。
"""
            
            try:
                response = await self._run_in_executor(
                    self.llm.invoke, [HumanMessage(content=prompt)]
                )
                
                summary = response.content.strip()
                
                # 验证总结长度
                if len(summary) > 200:
                    logger.warning("AI生成的总结过长，进行截取")
                    summary = summary[:200] + "..."
                
                logger.debug("查询总结生成完成")
                return summary
                
            except Exception as e:
                logger.warning(f"LLM总结生成失败: {str(e)}")
                # 生成基础总结
                if isinstance(result, pd.DataFrame):
                    return f"基于{len(df)}行数据完成了关于'{query}'的分析，返回了{len(result)}条结果。"
                else:
                    return f"基于{len(df)}行数据完成了关于'{query}'的分析查询。"
            
        except Exception as e:
            logger.error(f"生成查询总结时发生错误: {str(e)}")
            # 如果所有方法都失败，返回最基础的总结
            try:
                return f"基于数据分析完成查询，共处理{len(df)}行数据。"
            except:
                return "完成了数据分析查询。"