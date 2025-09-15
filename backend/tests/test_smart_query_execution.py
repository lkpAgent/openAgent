#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试程序：验证大模型生成的Python代码正确性
提取自 SmartExcelWorkflowManager._execute_smart_query 方法
"""

import os
import sys
import pandas as pd
import asyncio
import logging
from typing import Dict, Any, List
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from langchain_experimental.tools import PythonAstREPLTool
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputKeyToolsParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
# from open_agent.core.config import get_settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CodeExecutionError(Exception):
    """代码执行错误"""
    pass

class SmartQueryTester:
    """智能查询测试器"""
     
    def __init__(self):
        # 简化配置，直接使用环境变量或默认值
        self.openai_model = os.getenv('OPENAI_MODEL', 'deepseek-chat')
        self.openai_api_key = os.getenv('OPENAI_API_KEY', 'sk-4561c3417e8e459bb9f8335ab0ba0550')
        self.openai_base_url = os.getenv('OPENAI_BASE_URL', 'https://api.deepseek.com/v1')
        
        # 创建LLM实例
        self.llm = ChatOpenAI(
            model=self.openai_model,
            api_key=self.openai_api_key,
            base_url=self.openai_base_url,
            temperature=0.1
        )
        
        # 创建线程池执行器
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def _run_in_executor(self, func, *args):
        """在线程池中运行同步函数"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, func, *args)
        
    def load_test_dataframes(self) -> Dict[str, pd.DataFrame]:
        """
        加载测试用的Excel文件
        
        Returns:
            包含文件名和DataFrame的字典
        """
        # 这里需要指定两个测试文件的路径
        # 请根据实际情况修改文件路径
        test_files = {
            "2024年在手合同数据.xlsx": "E:\个人文件\安云数智.律为\项目相关\AI知识竞赛\\2024年在手合同数据.xlsx",
            "2025年在手合同数据.xlsx": "E:\个人文件\安云数智.律为\项目相关\AI知识竞赛\\2025年在手合同数据.xlsx"
        } 
        dataframes = {}
        
        for filename, filepath in test_files.items():
            try:
                if os.path.exists(filepath):
                    df = pd.read_excel(filepath)
                    dataframes[filename] = df
                    logger.info(f"成功加载文件: {filename}, 形状: {df.shape}")
                 
                    
            except Exception as e:
                logger.error(f"加载文件失败: {filename}, 错误: {str(e)}")
                continue
                
        return dataframes
    
    def build_dataset_info(self, dataframes: Dict[str, pd.DataFrame]) -> str:
        """
        构建数据集信息，包含文件名和前5行数据预览
        
        Args:
            dataframes: 数据框字典
            
        Returns:
            格式化的数据集信息字符串
        """
        dataset_info_parts = []
        
        for filename, df in dataframes.items():
            info_parts = [
                f"文件: {filename}",
                f"行数: {len(df)}",
                f"列数: {len(df.columns)}",
                f"列名: {', '.join([str(col) for col in df.columns.tolist()])}"
            ]
            
            # 添加前5行数据预览
            if len(df) > 0:
                preview_df = df.head(5).copy()
                
                # 处理数据预览中的特殊值
                for col in preview_df.columns:
                    preview_df[col] = preview_df[col].apply(lambda x: 
                        "" if pd.isna(x) else 
                        str(x)[:50] + "..." if isinstance(x, str) and len(str(x)) > 50 else 
                        str(x)
                    )
                
                info_parts.append("前5行数据预览:")
                info_parts.append(preview_df.to_string(index=False))
            
            dataset_info_parts.append("\n".join(info_parts))
        
        return "\n\n".join(dataset_info_parts)
    
    async def execute_smart_query(
        self, 
        user_query: str, 
        dataframes: Dict[str, pd.DataFrame]
    ) -> Dict[str, Any]:
        """
        执行智能查询，生成和运行pandas代码（严格按照原方法1025-1176行逻辑）
         
        Args:
            user_query: 用户查询
            dataframes: 数据框字典
             
        Returns:
            查询结果
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
                # 准备数据框字典，支持多个文件
                df_locals = {}
                var_name_to_filename = {}  # 变量名到文件名的映射
                for filename, df in dataframes.items():
                    # 使用简化的变量名
                    var_name = f"df_{len(df_locals) + 1}" if len(dataframes) > 1 else "df"
                    df_locals[var_name] = df
                    var_name_to_filename[var_name] = filename

                # 创建Python代码执行工具
                python_tool = PythonAstREPLTool(locals=df_locals)

                logger.info(f"创建Python工具成功，可用数据框: {list(df_locals.keys())}")

            except Exception as e:
                raise CodeExecutionError(f"创建Python工具失败: {str(e)}")

            # 构建数据集信息（包含文件名和前5行数据）
            dataset_info = []
            for var_name, df in df_locals.items():
                filename = var_name_to_filename[var_name]
                
                # 基本信息
                basic_info = f"- {var_name} (来源文件: {filename}): {len(df)}行 x {len(df.columns)}列"
                
                # 列名信息
                columns_info = f"  列名: {', '.join(str(col) for col in df.columns.tolist())}"
                
                # 前5行数据预览
                try:
                    preview_df = df.head(5)
                    preview_data = []
                    for idx, row in preview_df.iterrows():
                        row_data = []
                        for col in df.columns:
                            value = row[col]
                            # 处理空值和特殊值
                            if pd.isna(value):
                                row_data.append('NaN')
                            elif isinstance(value, (int, float)):
                                row_data.append(str(value))
                            else:
                                # 限制字符串长度避免过长
                                str_value = str(value)
                                if len(str_value) > 20:
                                    str_value = str_value[:17] + '...'
                                row_data.append(str_value)
                        preview_data.append(f"    行{idx}: {', '.join(row_data)}")
                    
                    preview_info = f"  前5行数据预览:\n{chr(10).join(preview_data)}"
                except Exception as e:
                    preview_info = f"  前5行数据预览: 无法生成预览 ({str(e)})"
                
                # 组合完整信息
                dataset_info.append(f"{basic_info}\n{columns_info}\n{preview_info}")

            # 构建系统提示
            system_prompt = f"""
                    你所有可以访问的数据来自于传递给您的python_tool里的locals里的pandas数据信（可能有多个）。
                    pandas数据集详细信息（文件来源、列名信息和数据预览）如下：
                    {chr(10).join(dataset_info)}
                    请根据用户提出的问题，结合给出的数据集的详细信息，直接编写Python相关代码来计算pandas中的值。要求：
                    1. 只返回代码，不返回其他内容
                    2. 只允许使用pandas和内置库
                    3. 确保代码能够直接执行并返回结果，包括import必要的内置库
                    4. 返回的结果应该是详细的、完整的数据，而不仅仅是简单答案 
                    5. 结果应该包含足够的上下文信息，让用户能够验证和理解答案 
                    6. 优先返回DataFrame格式的结果，便于展示为表格 
                    7. 务必不要再去写代码查看数据集的结构，提示词里已经给出了每个数据集的结构信息，直接根据提示词里的结构信息进行判断。
                    8. 要求代码中最后一次print的结果，必需是最后的正确结果（用户所需要的数据）
                    
                    示例：
                    - 如果问"哪个项目合同额最高"，不仅要返回项目名称，还要返回跟该项目其他有用的信息，比如合同额，合同时间，项目类型等（如果表格有该这些字段信息）
                    - 如果问"销售额最高的产品"，要返回产品名称、销售额、销售数量、市场占比等完整信息（如果表格有该这些字段信息）
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

            def debug_print(x):
                print('中间结果：', x)
                return x

            debug_node = RunnableLambda(debug_print)
            # 创建执行链
            llm_chain = prompt | llm_with_tools | debug_node| parser | debug_node| python_tool| debug_node

            # 执行查询
            try:
                logger.debug("开始执行Python工具查询")
                result = await self._run_in_executor(llm_chain.invoke, {"question": user_query})
                logger.debug(f"查询执行完成，结果: {str(result)[:200]}...")
            except Exception as e:
                error_msg = f"Python工具执行失败: {str(e)}"
                logger.error(error_msg)
                raise CodeExecutionError(error_msg)
            
            # 处理和返回结果
            return {
                'data': [{'result': str(result)}],
                'columns': [{'prop': 'result', 'label': '结果', 'width': 'auto'}],
                'total': 1,
                'result_type': 'text',
                'generated_code': 'N/A',  # 在工具链中生成的代码不直接可见
                'raw_result': str(result),
                'used_files': list(dataframes.keys()),
                'query': user_query,
                'metadata': {
                    'execution_time': 'N/A',
                    'dataframes': {
                        name: {
                            'rows': len(df), 
                            'columns': len(df.columns), 
                            'column_names': [str(col) for col in df.columns.tolist()]
                        } for name, df in dataframes.items()
                    }
                }
            }
             
        except CodeExecutionError:
            raise
        except Exception as e:
            error_msg = f"执行查询时发生错误: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise CodeExecutionError(error_msg)
    
    def _parse_dataframe_string_to_table_data(self, df_string: str, subindex: int = -2) -> Dict[str, Any]:
        """
        将字符串格式的DataFrame转换为表格数据
        （复制自原方法）
        """
        try:
            # 按行分割字符串
            lines = df_string.strip().split('\n')
            
            # 去掉最后两行（如因为最后两行可能是 "[12 rows x 11 columns]和空行"）
            if len(lines) >= 2 and subindex == -2:
                lines = lines[:subindex]
            
            if len(lines) < 2:
                # 如果行数不足，返回原始字符串
                return {
                    'columns': [{'prop': 'result', 'label': '结果', 'width': 'auto'}],
                    'data': [{'result': df_string}],
                    'total': 1
                }
            
            # 第一行是列名
            header_line = lines[0].strip()
            # 解析列名（去掉索引列）
            columns_raw = header_line.split()
            if columns_raw and columns_raw[0].isdigit() == False:
                # 如果第一列不是数字，说明包含了列名
                column_names = columns_raw
            else:
                # 否则使用默认列名
                column_names = [f'Column_{i}' for i in range(len(columns_raw))]
            
            # 构建列定义
            columns = []
            for i, col_name in enumerate(column_names):
                columns.append({
                    'prop': f'col_{i}',
                    'label': str(col_name),
                    'width': 'auto'
                })
            
            # 解析数据行
            data = []
            for line in lines[1:]:
                if line.strip():
                    # 分割数据行
                    row_values = line.strip().split()
                    if row_values:
                        row_data = {}
                        # 第一个值通常是索引
                        if len(row_values) > 0 and row_values[0].isdigit():
                            row_data['_index'] = row_values[0]
                            values = row_values[1:]
                        else:
                            values = row_values
                        
                        # 填充列数据
                        for i, value in enumerate(values):
                            if i < len(columns):
                                col_prop = f'col_{i}'
                                # 处理NaN值
                                if value.lower() == 'nan':
                                    row_data[col_prop] = ''
                                else:
                                    row_data[col_prop] = value
                        
                        data.append(row_data)
            
            return {
                'columns': columns,
                'data': data,
                'total': len(data)
            }
            
        except Exception as e:
            logger.warning(f"解析DataFrame字符串失败: {str(e)}")
            return {
                'columns': [{'prop': 'result', 'label': '结果', 'width': 'auto'}],
                'data': [{'result': df_string}],
                'total': 1
            }
    
    def _generate_mock_code(self, user_query: str, df_vars: List[str]) -> str:
        """
        根据查询生成模拟代码
        
        Args:
            user_query: 用户查询
            df_vars: 数据框变量列表
            
        Returns:
            生成的Python代码
        """
        query_lower = user_query.lower()
        
        # 根据查询类型生成不同的代码
        if "显示" in user_query and "所有" in user_query:
            return f"""
# 显示所有数据的概览
for var_name in {df_vars}:
    df = locals()[var_name]
    print(f"数据框 {{var_name}} 的基本信息:")
    print(f"形状: {{df.shape}}")
    print(f"列名: {{df.columns.tolist()}}")
    print(f"前5行数据:")
    print(df.head())
    print("\n" + "="*50 + "\n")

# 返回第一个数据框作为结果
result = {df_vars[0] if df_vars else 'None'}
result
"""
        
        elif "最高" in user_query or "最大" in user_query:
            return f"""
# 查找最高值
import pandas as pd

# 合并所有数据框
all_dfs = []
for var_name in {df_vars}:
    df = locals()[var_name].copy()
    df['数据来源'] = var_name
    all_dfs.append(df)

if all_dfs:
    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    # 查找包含金额、销售额、价格等列
    amount_cols = [col for col in combined_df.columns if any(keyword in str(col).lower() for keyword in ['金额', '销售额', '价格', '收入', 'amount', 'sales', 'price', 'revenue'])]
    
    if amount_cols:
        # 使用第一个金额列
        amount_col = amount_cols[0]
        max_row = combined_df.loc[combined_df[amount_col].idxmax()]
        print(f"最高{{amount_col}}的记录:")
        print(max_row)
        result = max_row.to_frame().T
    else:
        result = combined_df.head(1)
else:
    result = pd.DataFrame({{'结果': ['没有找到数据']}})

result
"""
        
        else:
            # 默认代码：显示数据概览
            return f"""
# 数据概览和基本统计
import pandas as pd

print("=== 数据概览 ===")
for var_name in {df_vars}:
    df = locals()[var_name]
    print(f"\n数据框 {{var_name}}:")
    print(f"形状: {{df.shape}}")
    print(f"列名: {{df.columns.tolist()}}")
    print("\n前3行数据:")
    print(df.head(3))
    print("\n" + "="*50)

# 返回第一个数据框的基本信息
if {df_vars}:
    first_df = locals()[{df_vars}[0]]
    result = pd.DataFrame({{
        '指标': ['总行数', '总列数'],
        '值': [len(first_df), len(first_df.columns)]
    }})
else:
    result = pd.DataFrame({{'结果': ['没有找到数据']}})

result
"""

async def main():
    """主测试函数"""
    tester = SmartQueryTester()
    
    # 加载测试数据
    print("=== 加载测试数据 ===")
    dataframes = tester.load_test_dataframes()
    
    if not dataframes:
        print("错误: 没有加载到任何数据")
        return
    
    print(f"成功加载 {len(dataframes)} 个数据文件:")
    for filename, df in dataframes.items():
        print(f"  - {filename}: {df.shape}")
        print(f"    列名: {', '.join(df.columns.tolist())}")
    
    # 测试查询列表
    test_queries = [
        "列举出2024年和2025年合同中的不同项目"
    ]
    
    print("\n=== 开始测试查询 ===")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- 测试 {i}: {query} ---")
        try:
            result = await tester.execute_smart_query(query, dataframes)
            
            print(f"✅ 查询成功")
            print(f"结果类型: {result['result_type']}")
            print(f"数据行数: {result['total']}")
            print(f"使用文件: {', '.join(result['used_files'])}")
            print(f"生成的代码:\n{result['generated_code']}")
            print(f"原始结果: {result['raw_result'][:200]}..." if len(result['raw_result']) > 200 else f"原始结果: {result['raw_result']}")
            
            if result['data'] and len(result['data']) > 0:
                print("前几行数据:")
                for j, row in enumerate(result['data'][:3]):
                    print(f"  行{j+1}: {row}")
            
        except Exception as e:
            print(f"❌ 查询失败: {str(e)}")
            logger.error(f"查询失败详情", exc_info=True)
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    asyncio.run(main())