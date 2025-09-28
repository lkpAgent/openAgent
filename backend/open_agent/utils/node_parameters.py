"""
节点参数默认配置工具
"""
from typing import Dict, List
from ..schemas.workflow import NodeInputOutput, NodeParameter, ParameterType, NodeType


def get_default_node_parameters(node_type: NodeType) -> NodeInputOutput:
    """获取节点类型的默认输入输出参数"""
    
    if node_type == NodeType.START:
        return NodeInputOutput(
            inputs=[
                NodeParameter(
                    name="workflow_input",
                    type=ParameterType.OBJECT,
                    description="工作流初始输入数据",
                    required=False,
                    source="input"
                )
            ],
            outputs=[
                NodeParameter(
                    name="data",
                    type=ParameterType.OBJECT,
                    description="开始节点输出数据"
                )
            ]
        )
    
    elif node_type == NodeType.END:
        return NodeInputOutput(
            inputs=[
                NodeParameter(
                    name="final_result",
                    type=ParameterType.OBJECT,
                    description="最终结果数据",
                    required=False,
                    source="node"
                )
            ],
            outputs=[
                NodeParameter(
                    name="workflow_result",
                    type=ParameterType.OBJECT,
                    description="工作流最终输出"
                )
            ]
        )
    
    elif node_type == NodeType.LLM:
        return NodeInputOutput(
            inputs=[
                NodeParameter(
                    name="prompt_variables",
                    type=ParameterType.OBJECT,
                    description="Prompt中使用的变量",
                    required=False,
                    source="node"
                ),
                NodeParameter(
                    name="user_input",
                    type=ParameterType.STRING,
                    description="用户输入文本",
                    required=False,
                    source="input"
                )
            ],
            outputs=[
                NodeParameter(
                    name="response",
                    type=ParameterType.STRING,
                    description="LLM生成的回复"
                ),
                NodeParameter(
                    name="tokens_used",
                    type=ParameterType.NUMBER,
                    description="使用的token数量"
                )
            ]
        )
    
    elif node_type == NodeType.CODE:
        return NodeInputOutput(
            inputs=[
                NodeParameter(
                    name="input_data",
                    type=ParameterType.OBJECT,
                    description="代码执行的输入数据",
                    required=False,
                    source="node"
                )
            ],
            outputs=[
                NodeParameter(
                    name="result",
                    type=ParameterType.OBJECT,
                    description="代码执行结果"
                ),
                NodeParameter(
                    name="output",
                    type=ParameterType.STRING,
                    description="代码输出内容"
                )
            ]
        )
    
    elif node_type == NodeType.HTTP:
        return NodeInputOutput(
            inputs=[
                NodeParameter(
                    name="url_params",
                    type=ParameterType.OBJECT,
                    description="URL参数",
                    required=False,
                    source="node"
                ),
                NodeParameter(
                    name="request_body",
                    type=ParameterType.OBJECT,
                    description="请求体数据",
                    required=False,
                    source="node"
                )
            ],
            outputs=[
                NodeParameter(
                    name="response_data",
                    type=ParameterType.OBJECT,
                    description="HTTP响应数据"
                ),
                NodeParameter(
                    name="status_code",
                    type=ParameterType.NUMBER,
                    description="HTTP状态码"
                )
            ]
        )
    
    elif node_type == NodeType.CONDITION:
        return NodeInputOutput(
            inputs=[
                NodeParameter(
                    name="condition_data",
                    type=ParameterType.OBJECT,
                    description="条件判断的输入数据",
                    required=True,
                    source="node"
                )
            ],
            outputs=[
                NodeParameter(
                    name="result",
                    type=ParameterType.BOOLEAN,
                    description="条件判断结果"
                ),
                NodeParameter(
                    name="branch",
                    type=ParameterType.STRING,
                    description="执行分支（true/false）"
                )
            ]
        )
    
    else:
        # 默认参数
        return NodeInputOutput(
            inputs=[
                NodeParameter(
                    name="input",
                    type=ParameterType.OBJECT,
                    description="节点输入数据",
                    required=False,
                    source="node"
                )
            ],
            outputs=[
                NodeParameter(
                    name="output",
                    type=ParameterType.OBJECT,
                    description="节点输出数据"
                )
            ]
        )


def validate_parameter_connections(nodes: List[Dict], connections: List[Dict]) -> List[str]:
    """验证节点参数连接的有效性"""
    errors = []
    node_dict = {node['id']: node for node in nodes}
    
    for node in nodes:
        if 'parameters' not in node or not node['parameters']:
            continue
            
        for input_param in node['parameters'].get('inputs', []):
            if input_param.get('source') == 'node':
                source_node_id = input_param.get('source_node_id')
                source_field = input_param.get('source_field')
                
                if not source_node_id:
                    errors.append(f"节点 {node['name']} 的输入参数 {input_param['name']} 缺少来源节点ID")
                    continue
                
                if source_node_id not in node_dict:
                    errors.append(f"节点 {node['name']} 的输入参数 {input_param['name']} 引用了不存在的节点 {source_node_id}")
                    continue
                
                source_node = node_dict[source_node_id]
                if 'parameters' in source_node and source_node['parameters']:
                    source_outputs = source_node['parameters'].get('outputs', [])
                    output_fields = [output['name'] for output in source_outputs]
                    
                    if source_field and source_field not in output_fields:
                        errors.append(f"节点 {node['name']} 的输入参数 {input_param['name']} 引用了节点 {source_node['name']} 不存在的输出字段 {source_field}")
    
    return errors