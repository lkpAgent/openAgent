"""Workflow execution engine."""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from ..models.workflow import Workflow, WorkflowExecution, NodeExecution, ExecutionStatus, NodeType
from ..models.llm_config import LLMConfig
from ..services.llm_service import LLMService

from ..db.database import get_db
from ..utils.logger import get_logger

logger = get_logger("workflow_engine")


class WorkflowEngine:
    """工作流执行引擎"""
    
    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService()

    
    async def execute_workflow(self, workflow: Workflow, input_data: Optional[Dict[str, Any]] = None, 
                             user_id: int = None, db: Session = None) -> 'WorkflowExecutionResponse':
        """执行工作流"""
        from ..schemas.workflow import WorkflowExecutionResponse
        
        if db:
            self.db = db
            
        # 创建执行记录
        execution = WorkflowExecution(
            workflow_id=workflow.id,
            status=ExecutionStatus.RUNNING,
            input_data=input_data or {},
            executor_id=user_id,
            started_at=datetime.now().isoformat()
        )
        execution.set_audit_fields(user_id)
        
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)
        

        
        try:
            # 解析工作流定义
            definition = workflow.definition
            nodes = {node['id']: node for node in definition['nodes']}
            connections = definition['connections']
            
            # 构建节点依赖图
            node_graph = self._build_node_graph(nodes, connections)
            
            # 执行工作流
            result = await self._execute_nodes(execution, nodes, node_graph, input_data or {})
            
            # 更新执行状态
            execution.status = ExecutionStatus.COMPLETED
            execution.output_data = result
            execution.completed_at = datetime.now().isoformat()
            

            
        except Exception as e:
            logger.error(f"工作流执行失败: {str(e)}")
            execution.status = ExecutionStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.now().isoformat()
            

            
        execution.set_audit_fields(user_id, is_update=True)
        self.db.commit()
        self.db.refresh(execution)
        
        return WorkflowExecutionResponse.from_orm(execution)
    
    async def execute_workflow_stream(self, workflow: 'Workflow', input_data: Optional[Dict[str, Any]] = None, 
                                    user_id: int = None, db: Session = None):
        """流式执行工作流，实时推送节点状态"""
        from ..schemas.workflow import WorkflowExecutionResponse
        from typing import AsyncGenerator
        
        if db:
            self.db = db
            
        # 创建执行记录
        execution = WorkflowExecution(
            workflow_id=workflow.id,
            status=ExecutionStatus.RUNNING,
            input_data=input_data or {},
            executor_id=user_id,
            started_at=datetime.now().isoformat()
        )
        execution.set_audit_fields(user_id)
        
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)
        
        # 发送工作流开始执行的消息
        yield {
            'type': 'workflow_status',
            'execution_id': execution.id,
            'status': 'started',
            'data': {
                "workflow_id": workflow.id,
                "workflow_name": workflow.name,
                "input_data": input_data or {},
                "started_at": execution.started_at
            },
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # 解析工作流定义
            definition = workflow.definition
            nodes = {node['id']: node for node in definition['nodes']}
            connections = definition['connections']
            
            # 构建节点依赖图
            node_graph = self._build_node_graph(nodes, connections)
            
            # 执行工作流（流式版本）
            result = None
            async for step_data in self._execute_nodes_stream(execution, nodes, node_graph, input_data or {}):
                yield step_data
                # 如果是最终结果，保存它
                if step_data.get('type') == 'workflow_result':
                    result = step_data.get('data', {})
            
            # 更新执行状态
            execution.status = ExecutionStatus.COMPLETED
            execution.output_data = result
            execution.completed_at = datetime.now().isoformat()
            
            # 发送工作流完成的消息
            yield {
                'type': 'workflow_status',
                'execution_id': execution.id,
                'status': 'completed',
                'data': {
                    "output_data": result,
                    "completed_at": execution.completed_at
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"工作流执行失败: {str(e)}")
            execution.status = ExecutionStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.now().isoformat()
            
            # 发送工作流失败的消息
            yield {
                'type': 'workflow_status',
                'execution_id': execution.id,
                'status': 'failed',
                'data': {
                    "error_message": str(e),
                    "completed_at": execution.completed_at
                },
                'timestamp': datetime.now().isoformat()
            }
            
        execution.set_audit_fields(user_id, is_update=True)
        self.db.commit()
        self.db.refresh(execution)
    
    def _build_node_graph(self, nodes: Dict[str, Any], connections: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """构建节点依赖图"""
        graph = {}
        
        for node_id, node in nodes.items():
            graph[node_id] = {
                'node': node,
                'inputs': [],  # 输入节点
                'outputs': []  # 输出节点
            }
        
        for connection in connections:
            # 支持两种字段名格式：from/to 和 from_node/to_node
            from_node = connection.get('from') or connection.get('from_node')
            to_node = connection.get('to') or connection.get('to_node')
            
            if from_node in graph and to_node in graph:
                graph[from_node]['outputs'].append(to_node)
                graph[to_node]['inputs'].append(from_node)
        
        return graph
    
    async def _execute_nodes(self, execution: WorkflowExecution, nodes: Dict[str, Any], 
                           node_graph: Dict[str, Dict[str, Any]], workflow_input: Dict[str, Any]) -> Dict[str, Any]:
        """执行节点"""
        # 找到开始节点
        start_nodes = [node_id for node_id, info in node_graph.items() 
                      if info['node']['type'] == 'start']
        
        if not start_nodes:
            raise ValueError("未找到开始节点")
        
        if len(start_nodes) > 1:
            raise ValueError("存在多个开始节点")
        
        start_node_id = start_nodes[0]
        
        # 执行上下文
        context = {
            'workflow_input': workflow_input,
            'node_outputs': {}
        }
        
        # 从开始节点开始执行
        await self._execute_node_recursive(execution, start_node_id, node_graph, context)
        
        # 找到结束节点的输出作为工作流结果
        end_nodes = [node_id for node_id, info in node_graph.items() 
                    if info['node']['type'] == 'end']
        
        if end_nodes:
            end_node_id = end_nodes[0]
            return context['node_outputs'].get(end_node_id, {})
        
        return {}
    
    async def _execute_nodes_stream(self, execution: WorkflowExecution, nodes: Dict[str, Any], 
                                  node_graph: Dict[str, Dict[str, Any]], workflow_input: Dict[str, Any]):
        """流式执行节点，实时推送节点状态"""
        # 找到开始节点
        start_nodes = [node_id for node_id, info in node_graph.items() 
                      if info['node']['type'] == 'start']
        
        if not start_nodes:
            raise ValueError("未找到开始节点")
        
        if len(start_nodes) > 1:
            raise ValueError("存在多个开始节点")
        
        start_node_id = start_nodes[0]
        
        # 执行上下文
        context = {
            'workflow_input': workflow_input,
            'node_outputs': {}
        }
        
        # 从开始节点开始执行
        async for step_data in self._execute_node_recursive_stream(execution, start_node_id, node_graph, context):
            yield step_data
        
        # 找到结束节点的输出作为工作流结果
        end_nodes = [node_id for node_id, info in node_graph.items() 
                    if info['node']['type'] == 'end']
        
        if end_nodes:
            end_node_id = end_nodes[0]
            result = context['node_outputs'].get(end_node_id, {})
        else:
            result = {}
        
        # 发送最终结果
        yield {
            'type': 'workflow_result',
            'execution_id': execution.id,
            'data': result,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _execute_node_recursive_stream(self, execution: WorkflowExecution, node_id: str, 
                                           node_graph: Dict[str, Dict[str, Any]], context: Dict[str, Any]):
        """递归执行节点（流式版本）"""
        if node_id in context['node_outputs']:
            # 节点已执行过
            return
        
        node_info = node_graph[node_id]
        node = node_info['node']
        
        # 等待所有输入节点完成
        for input_node_id in node_info['inputs']:
            async for step_data in self._execute_node_recursive_stream(execution, input_node_id, node_graph, context):
                yield step_data
        
        # 发送节点开始执行的消息
        yield {
            'type': 'node_status',
            'execution_id': execution.id,
            'node_id': node_id,
            'status': 'started',
            'data': {
                'node_name': node.get('name', ''),
                'node_type': node.get('type', ''),
                'started_at': datetime.now().isoformat()
            },
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # 执行当前节点
            output = await self._execute_single_node(execution, node, context)
            context['node_outputs'][node_id] = output
            
            # 发送节点完成的消息
            yield {
                'type': 'node_status',
                'execution_id': execution.id,
                'node_id': node_id,
                'status': 'completed',
                'data': {
                    'node_name': node.get('name', ''),
                    'node_type': node.get('type', ''),
                    'output': output,
                    'completed_at': datetime.now().isoformat()
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            # 发送节点失败的消息
            yield {
                'type': 'node_status',
                'execution_id': execution.id,
                'node_id': node_id,
                'status': 'failed',
                'data': {
                    'node_name': node.get('name', ''),
                    'node_type': node.get('type', ''),
                    'error_message': str(e),
                    'failed_at': datetime.now().isoformat()
                },
                'timestamp': datetime.now().isoformat()
            }
            raise
        
        # 执行所有输出节点
        for output_node_id in node_info['outputs']:
            async for step_data in self._execute_node_recursive_stream(execution, output_node_id, node_graph, context):
                yield step_data
    
    async def _execute_node_recursive(self, execution: WorkflowExecution, node_id: str, 
                                    node_graph: Dict[str, Dict[str, Any]], context: Dict[str, Any]):
        """递归执行节点"""
        if node_id in context['node_outputs']:
            # 节点已执行过
            return
        
        node_info = node_graph[node_id]
        node = node_info['node']
        
        # 等待所有输入节点完成
        for input_node_id in node_info['inputs']:
            await self._execute_node_recursive(execution, input_node_id, node_graph, context)
        
        # 执行当前节点
        output = await self._execute_single_node(execution, node, context)
        context['node_outputs'][node_id] = output
        
        # 执行所有输出节点
        for output_node_id in node_info['outputs']:
            await self._execute_node_recursive(execution, output_node_id, node_graph, context)
    
    async def _execute_single_node(self, execution: WorkflowExecution, node: Dict[str, Any], 
                                 context: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个节点"""
        node_id = node['id']
        node_type = node['type']
        node_name = node['name']
        
        # 创建节点执行记录
        node_execution = NodeExecution(
            workflow_execution_id=execution.id,
            node_id=node_id,
            node_type=NodeType(node_type),
            node_name=node_name,
            status=ExecutionStatus.RUNNING,
            started_at=datetime.now().isoformat()
        )
        self.db.add(node_execution)
        self.db.commit()
        self.db.refresh(node_execution)
        
        start_time = time.time()
        
        try:
            # 准备输入数据
            input_data = self._prepare_node_input(node, context)
            
            # 为前端显示准备输入数据
            display_input_data = input_data.copy()
            
            # 对于开始节点，显示的输入应该是workflow_input
            if node_type == 'start':
                display_input_data = input_data['workflow_input']
            elif node_type == 'llm':
                # 对于LLM节点，先执行变量替换以获取处理后的提示词
                config = input_data['node_config']
                prompt_template = config.get('prompt', '')
                enable_variable_substitution = config.get('enable_variable_substitution', True)
                
                if enable_variable_substitution:
                    processed_prompt = self._substitute_variables(prompt_template, input_data)
                else:
                    processed_prompt = prompt_template
                
                display_input_data = {
                    'original_prompt': prompt_template,
                    'processed_prompt': processed_prompt,
                    'model_config': config,
                    'resolved_inputs': input_data.get('resolved_inputs', {})
                }
            
            node_execution.input_data = display_input_data
            self.db.commit()
            

            
            # 根据节点类型执行
            if node_type == 'start':
                output_data = await self._execute_start_node(node, input_data)
            elif node_type == 'end':
                output_data = await self._execute_end_node(node, input_data)
            elif node_type == 'llm':
                output_data = await self._execute_llm_node(node, input_data)
            elif node_type == 'condition':
                output_data = await self._execute_condition_node(node, input_data)
            elif node_type == 'code':
                output_data = await self._execute_code_node(node, input_data)
            elif node_type == 'http':
                output_data = await self._execute_http_node(node, input_data)
            else:
                raise ValueError(f"不支持的节点类型: {node_type}")
            
            # 更新执行状态
            end_time = time.time()
            node_execution.status = ExecutionStatus.COMPLETED
            node_execution.output_data = output_data
            node_execution.completed_at = datetime.now().isoformat()
            node_execution.duration_ms = int((end_time - start_time) * 1000)
            
            self.db.commit()
            

            
            return output_data
            
        except Exception as e:
            logger.error(f"节点 {node_id} 执行失败: {str(e)}")
            end_time = time.time()
            node_execution.status = ExecutionStatus.FAILED
            node_execution.error_message = str(e)
            node_execution.completed_at = datetime.now().isoformat()
            node_execution.duration_ms = int((end_time - start_time) * 1000)
            self.db.commit()
            

            
            raise
    
    def _prepare_node_input(self, node: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """准备节点输入数据"""
        # 基础输入数据
        input_data = {
            'workflow_input': context['workflow_input'],
            'node_config': node.get('config', {}),
            'previous_outputs': context['node_outputs']
        }
        
        # 处理节点参数配置
        node_parameters = node.get('parameters', {})
        if node_parameters and 'inputs' in node_parameters:
            resolved_inputs = {}
            
            for param in node_parameters['inputs']:
                param_name = param.get('name')
                param_source = param.get('source', 'default')
                param_default = param.get('default_value')
                variable_name = param.get('variable_name', '')
                
                # 优先使用variable_name，如果存在的话
                if variable_name:
                    resolved_value = self._resolve_variable_value(variable_name, context)
                    resolved_inputs[param_name] = resolved_value if resolved_value is not None else param_default
                elif param_source == 'workflow':
                    # 从工作流输入获取
                    source_param_name = param.get('source_param_name', param_name)
                    resolved_inputs[param_name] = context['workflow_input'].get(source_param_name, param_default)
                elif param_source == 'node':
                    # 从其他节点输出获取
                    source_node_id = param.get('source_node_id')
                    source_param_name = param.get('source_param_name', 'data')
                    
                    if source_node_id and source_node_id in context['node_outputs']:
                        source_output = context['node_outputs'][source_node_id]
                        if isinstance(source_output, dict):
                            resolved_inputs[param_name] = source_output.get(source_param_name, param_default)
                        else:
                            resolved_inputs[param_name] = source_output
                    else:
                        resolved_inputs[param_name] = param_default
                else:
                    # 使用默认值
                    resolved_inputs[param_name] = param_default
            
            # 将解析后的参数添加到输入数据
            input_data['resolved_inputs'] = resolved_inputs
        
        return input_data
    
    def _resolve_variable_value(self, variable_name: str, context: Dict[str, Any]) -> Any:
        """解析变量值，支持格式如 "node_id.output.field_name" 或更深层路径"""
        try:
            # 解析变量名格式：node_id.output.field_name 或 node_id.field1.field2.field3
            parts = variable_name.split('.')
            if len(parts) >= 2:
                source_node_id = parts[0]
                
                # 从previous_outputs中获取源节点的输出
                if source_node_id in context['node_outputs']:
                    source_output = context['node_outputs'][source_node_id]
                    
                    if isinstance(source_output, dict):
                        # 从第二个部分开始遍历路径
                        current_value = source_output
                        for field_name in parts[1:]:
                            if isinstance(current_value, dict) and field_name in current_value:
                                current_value = current_value[field_name]
                            else:
                                # 如果路径不存在，返回None
                                return None
                        
                        return current_value
                
            return None
        except Exception as e:
            logger.warning(f"解析变量值失败: {variable_name}, 错误: {str(e)}")
            return None
    
    async def _execute_start_node(self, node: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行开始节点"""
        # 开始节点的输入和输出应该一致，都是workflow_input
        workflow_input = input_data['workflow_input']
        return {
            'success': True,
            'message': '工作流开始',
            'data': workflow_input,
            'user_input': workflow_input  # 添加用户输入显示
        }
    
    async def _execute_end_node(self, node: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行结束节点"""
        previous_outputs = input_data.get('previous_outputs', {})
        
        # 处理结束节点的输出参数配置
        node_parameters = node.get('parameters', {})
        output_params = node_parameters.get('outputs', [])
        
        result_data = {}
        
        # 根据输出参数配置获取对应的值
        for param in output_params:
            param_name = param.get('name')
            variable_name = param.get('variable_name')
            
            if variable_name:
                # 解析variable_name，格式如: "node_1759022611056.output.response"
                try:
                    parts = variable_name.split('.')
                    if len(parts) >= 3:
                        source_node_id = parts[0]
                        output_type = parts[1]  # 通常是"output"
                        field_name = parts[2]   # 具体的字段名，如"response"
                        
                        # 从前一个节点的输出中获取值
                        if source_node_id in previous_outputs:
                            source_output = previous_outputs[source_node_id]
                            if isinstance(source_output, dict):
                                # 首先尝试从根级别获取字段（如LLM节点的response字段）
                                if field_name in source_output:
                                    result_data[param_name] = source_output[field_name]
                                # 如果根级别没有，再尝试从data字段中获取
                                elif 'data' in source_output and isinstance(source_output['data'], dict):
                                    if field_name in source_output['data']:
                                        result_data[param_name] = source_output['data'][field_name]
                                    else:
                                        result_data[param_name] = None
                                else:
                                    result_data[param_name] = None
                            else:
                                result_data[param_name] = source_output
                        else:
                            result_data[param_name] = None
                    else:
                        # 格式不正确，使用默认值
                        result_data[param_name] = param.get('default_value')
                except Exception as e:
                    logger.warning(f"解析variable_name失败: {variable_name}, 错误: {str(e)}")
                    result_data[param_name] = param.get('default_value')
            else:
                # 没有variable_name，使用默认值
                result_data[param_name] = param.get('default_value')
        
        # 如果没有配置输出参数，返回简化的前一个节点输出（保持向后兼容）
        if not output_params:
            simplified_outputs = {}
            for node_id, output in previous_outputs.items():
                if isinstance(output, dict):
                    simplified_outputs[node_id] = {
                        'success': output.get('success', False),
                        'message': output.get('message', ''),
                        'data': output.get('data', {}) if not isinstance(output.get('data'), dict) or node_id not in str(output.get('data', {})) else {}
                    }
                else:
                    simplified_outputs[node_id] = output
            result_data = simplified_outputs
        
        return {
            'success': True,
            'message': '工作流结束',
            'data': result_data
        }
    
    async def _execute_llm_node(self, node: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行LLM节点"""
        config = input_data['node_config']
        
        # 获取LLM配置
        model_id = config.get('model_id')
        if not model_id:
            # 兼容前端的model字段（可能是ID或名称）
            model_value = config.get('model_name', config.get('model'))
            if model_value:
                # 如果是整数，直接作为ID使用
                if isinstance(model_value, int):
                    model_id = model_value
                else:
                    # 如果是字符串，按名称查询
                    llm_config = self.db.query(LLMConfig).filter(LLMConfig.model_name == model_value).first()
                    if llm_config:
                        model_id = llm_config.id
        
        if not model_id:
            raise ValueError("未指定有效的大模型配置")
        
        llm_config = self.db.query(LLMConfig).filter(LLMConfig.id == model_id).first()
        if not llm_config:
            raise ValueError(f"大模型配置 {model_id} 不存在")
        
        # 准备提示词
        prompt_template = config.get('prompt', '')
        
        # 检查是否启用变量替换
        enable_variable_substitution = config.get('enable_variable_substitution', True)
        
        if enable_variable_substitution:
            # 使用增强的变量替换
            prompt = self._substitute_variables(prompt_template, input_data)
        else:
            prompt = prompt_template
        
        # 记录处理后的提示词到输入数据中，用于前端显示
        input_data['processed_prompt'] = prompt
        input_data['original_prompt'] = prompt_template
        
        # 调用LLM服务
        try:
            response = await self.llm_service.chat_completion(
                model_config=llm_config,
                messages=[{"role": "user", "content": prompt}],
                temperature=config.get('temperature', 0.7),
                max_tokens=config.get('max_tokens')
            )
            
            return {
                'success': True,
                'response': response,
                'prompt': prompt,
                'model': llm_config.model_name,
                'tokens_used': getattr(response, 'usage', {}).get('total_tokens', 0) if hasattr(response, 'usage') else 0
            }
            
        except Exception as e:
            logger.error(f"LLM调用失败: {str(e)}")
            raise ValueError(f"LLM调用失败: {str(e)}")
    
    def _substitute_variables(self, template: str, input_data: Dict[str, Any]) -> str:
        """变量替换函数"""
        import re
        
        # 获取解析后的输入参数
        resolved_inputs = input_data.get('resolved_inputs', {})
        
        # 获取工作流输入数据
        # input_data['workflow_input'] 包含了用户输入的参数
        workflow_input = input_data.get('workflow_input', {})
        
        # 构建变量上下文
        variable_context = {}
        
        # 首先添加解析后的参数
        variable_context.update(resolved_inputs)
        
        # 添加工作流输入的顶层字段
        variable_context.update(workflow_input)
        
        # 如果 workflow_input 包含 user_input 字段，将其内容提升到顶层
        if 'user_input' in workflow_input and isinstance(workflow_input['user_input'], dict):
            variable_context.update(workflow_input['user_input'])
        
        # 添加前一个节点的输出（简化访问）
        for node_id, output in input_data.get('previous_outputs', {}).items():
            if isinstance(output, dict):
                # 添加节点输出的直接访问
                variable_context[f'node_{node_id}'] = output.get('data', output)
                # 如果输出有response字段，也添加直接访问
                if 'response' in output:
                    variable_context[f'node_{node_id}_response'] = output['response']
        
        # 调试日志：打印变量上下文
        logger.info(f"变量替换上下文: {variable_context}")
        logger.info(f"原始模板: {template}")
        
        # 使用正则表达式替换变量 {{variable_name}} 和 {variable_name}
        def replace_variable(match):
            var_name = match.group(1)
            replacement = variable_context.get(var_name, match.group(0))
            logger.info(f"替换变量 {match.group(0)} -> {replacement}")
            return str(replacement)
        
        # 首先替换 {{variable_name}} 格式的变量
        result = re.sub(r'\{\{([^}]+)\}\}', replace_variable, template)
        # 然后替换 {variable_name} 格式的变量
        result = re.sub(r'\{([^}]+)\}', replace_variable, result)
        
        logger.info(f"替换后结果: {result}")
        return result
    
    async def _execute_condition_node(self, node: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行条件节点"""
        config = input_data['node_config']
        condition = config.get('condition', '')
        
        # 简单的条件评估（生产环境需要更安全的实现）
        try:
            # 构建评估上下文
            eval_context = {
                'input': input_data['workflow_input'],
                'previous': input_data['previous_outputs']
            }
            
            # 评估条件
            result = eval(condition, {"__builtins__": {}}, eval_context)
            
            return {
                'success': True,
                'condition': condition,
                'result': bool(result)
            }
            
        except Exception as e:
            logger.error(f"条件评估失败: {str(e)}")
            raise ValueError(f"条件评估失败: {str(e)}")
    
    async def _execute_code_node(self, node: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行代码节点"""
        config = input_data['node_config']
        language = config.get('language', 'python')
        code = config.get('code', '')
        
        if language == 'python':
            # 执行Python代码
            execution_result = await self._execute_python_code(code, input_data)
            
            # 处理输出参数配置
            node_parameters = node.get('parameters', {})
            if node_parameters and 'outputs' in node_parameters:
                output_params = node_parameters['outputs']
                code_result = execution_result.get('result', {})
                
                # 根据输出参数配置构建最终输出
                final_output = {
                    'success': execution_result['success'],
                    'code': execution_result['code'],
                    'input_parameters': execution_result.get('input_parameters', {})
                }
                
                # 如果代码返回的是字典，根据输出参数配置提取对应字段
                if isinstance(code_result, dict):
                    for output_param in output_params:
                        param_name = output_param.get('name')
                        if param_name and param_name in code_result:
                            final_output[param_name] = code_result[param_name]
                else:
                    # 如果代码返回的不是字典，且只有一个输出参数，直接使用返回值
                    if len(output_params) == 1:
                        param_name = output_params[0].get('name')
                        if param_name:
                            final_output[param_name] = code_result
                
                return final_output
            else:
                # 如果没有输出参数配置，返回原始结果
                return execution_result
        else:
            raise ValueError(f"不支持的代码语言: {language}")
    
    async def _execute_python_code(self, code: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行Python代码"""
        try:
            # 构建执行上下文
            safe_builtins = {
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'list': list,
                'dict': dict,
                'tuple': tuple,
                'set': set,
                'range': range,
                'enumerate': enumerate,
                'zip': zip,
                'sum': sum,
                'min': min,
                'max': max,
                'abs': abs,
                'round': round,
                'sorted': sorted,
                'reversed': reversed,
                'print': print,
                '__import__': __import__,
            }
            
            # 导入常用模块
            import json
            import datetime
            import math
            import re
            
            exec_context = {
                '__builtins__': safe_builtins,
                'json': json,  # 允许使用json模块
                'datetime': datetime,  # 允许使用datetime模块
                'math': math,  # 允许使用math模块
                're': re,  # 允许使用re模块
            }
            
            # 执行代码以定义函数
            exec(code, exec_context)
            
            # 检查是否定义了main函数
            if 'main' not in exec_context:
                raise ValueError("代码中必须定义一个main函数")
            
            main_function = exec_context['main']
            
            # 获取已解析的输入参数
            resolved_inputs = input_data.get('resolved_inputs', {})
            
            # 调用main函数并传递参数
            if resolved_inputs:
                # 使用解析后的输入参数调用main函数
                result = main_function(**resolved_inputs)
            else:
                # 如果没有输入参数，直接调用main函数
                result = main_function()
            
            return {
                'success': True,
                'result': result,
                'code': code,
                'input_parameters': resolved_inputs
            }
            
        except Exception as e:
            logger.error(f"Python代码执行失败: {str(e)}")
            raise ValueError(f"Python代码执行失败: {str(e)}")
    
    async def _execute_http_node(self, node: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行HTTP请求节点"""
        import aiohttp
        
        config = input_data['node_config']
        method = config.get('method', 'GET').upper()
        url = config.get('url', '')
        headers = config.get('headers', {})
        body = config.get('body')
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    data=body
                ) as response:
                    response_text = await response.text()
                    
                    return {
                        'success': True,
                        'status_code': response.status,
                        'response': response_text,
                        'headers': dict(response.headers)
                    }
                    
        except Exception as e:
            logger.error(f"HTTP请求失败: {str(e)}")
            raise ValueError(f"HTTP请求失败: {str(e)}")


# 工作流引擎实例
def get_workflow_engine(db: Session = None) -> WorkflowEngine:
    """获取工作流引擎实例"""
    if db is None:
        db = next(get_db())
    return WorkflowEngine(db)