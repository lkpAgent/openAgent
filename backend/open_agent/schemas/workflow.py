"""Workflow schemas."""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class WorkflowStatus(str, Enum):
    """工作流状态枚举"""
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class NodeType(str, Enum):
    """节点类型"""
    START = "start"
    END = "end"
    LLM = "llm"
    CONDITION = "condition"
    LOOP = "loop"
    CODE = "code"
    HTTP = "http"
    TOOL = "tool"


class ExecutionStatus(str, Enum):
    """执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# 节点定义相关模式
class NodePosition(BaseModel):
    """节点位置"""
    x: float
    y: float


# 参数定义相关模式
class ParameterType(str, Enum):
    """参数类型"""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"


class NodeParameter(BaseModel):
    """节点参数定义"""
    name: str = Field(..., min_length=1, max_length=50)
    type: ParameterType
    description: Optional[str] = None
    required: bool = True
    default_value: Optional[Any] = None
    source: Optional[str] = None  # 参数来源：'input'(用户输入), 'node'(其他节点输出), 'variable'(变量引用)
    source_node_id: Optional[str] = None  # 来源节点ID（当source为'node'时）
    source_field: Optional[str] = None  # 来源字段名
    variable_name: Optional[str] = None  # 变量名称（用于结束节点的输出参数）


class NodeInputOutput(BaseModel):
    """节点输入输出定义"""
    inputs: List[NodeParameter] = []
    outputs: List[NodeParameter] = []


class NodeConfig(BaseModel):
    """节点配置基类"""
    pass


class LLMNodeConfig(NodeConfig):
    """LLM节点配置"""
    model_id: Optional[int] = None  # 大模型配置ID
    model_name: Optional[str] = None  # 模型名称（兼容前端）
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: Optional[int] = Field(default=None, gt=0)
    prompt: str = Field(..., min_length=1)
    enable_variable_substitution: bool = True  # 是否启用变量替换


class ConditionNodeConfig(NodeConfig):
    """条件节点配置"""
    condition: str = Field(..., min_length=1)


class LoopNodeConfig(NodeConfig):
    """循环节点配置"""
    loop_type: str = Field(..., pattern="^(count|while|foreach)$")
    count: Optional[int] = Field(None, description="循环次数（当loop_type为count时）")
    condition: Optional[str] = Field(None, description="循环条件（当loop_type为while时）")
    iterable: Optional[str] = Field(None, description="可迭代对象（当loop_type为foreach时）")


class CodeNodeConfig(NodeConfig):
    """代码执行节点配置"""
    language: str = Field(..., pattern="^(python|javascript)$")
    code: str = Field(..., min_length=1)


class HttpNodeConfig(NodeConfig):
    """HTTP请求节点配置"""
    method: str = Field(..., pattern="^(GET|POST|PUT|DELETE|PATCH)$")
    url: str = Field(..., min_length=1)
    headers: Optional[Dict[str, str]] = None
    body: Optional[str] = None


class ToolNodeConfig(NodeConfig):
    """工具节点配置"""
    tool_type: str
    parameters: Optional[Dict[str, Any]] = None


class WorkflowNode(BaseModel):
    """工作流节点"""
    id: str
    type: NodeType
    name: str
    description: Optional[str] = None
    position: NodePosition
    config: Optional[Dict[str, Any]] = None
    parameters: Optional[NodeInputOutput] = None  # 节点输入输出参数定义


class WorkflowConnection(BaseModel):
    """工作流连接"""
    id: str
    from_node: str = Field(..., alias="from")
    to_node: str = Field(..., alias="to")
    from_point: str = Field(default="output")
    to_point: str = Field(default="input")


class WorkflowDefinition(BaseModel):
    """工作流定义"""
    nodes: List[WorkflowNode]
    connections: List[WorkflowConnection]


# 工作流CRUD模式
class WorkflowCreate(BaseModel):
    """创建工作流"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    definition: WorkflowDefinition
    status: WorkflowStatus = WorkflowStatus.DRAFT


class WorkflowUpdate(BaseModel):
    """更新工作流"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    definition: Optional[WorkflowDefinition] = None
    status: Optional[WorkflowStatus] = None
    is_active: Optional[bool] = None


class WorkflowResponse(BaseModel):
    """工作流响应"""
    id: int
    name: str
    description: Optional[str]
    status: WorkflowStatus
    is_active: bool
    version: str
    owner_id: int
    definition: Optional[WorkflowDefinition] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# 工作流执行相关模式
class WorkflowExecuteRequest(BaseModel):
    """工作流执行请求"""
    input_data: Optional[Dict[str, Any]] = None


class NodeExecutionResponse(BaseModel):
    """节点执行响应"""
    id: int
    node_id: str
    node_type: NodeType
    node_name: str
    status: ExecutionStatus
    input_data: Optional[Dict[str, Any]]
    output_data: Optional[Dict[str, Any]]
    started_at: Optional[str]
    completed_at: Optional[str]
    duration_ms: Optional[int]
    error_message: Optional[str]

    class Config:
        from_attributes = True


class WorkflowExecutionResponse(BaseModel):
    """工作流执行响应"""
    id: int
    workflow_id: int
    status: ExecutionStatus
    input_data: Optional[Dict[str, Any]]
    output_data: Optional[Dict[str, Any]]
    started_at: Optional[str]
    completed_at: Optional[str]
    error_message: Optional[str]
    executor_id: int
    node_executions: Optional[List[NodeExecutionResponse]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# 工作流列表响应
class WorkflowListResponse(BaseModel):
    """工作流列表响应"""
    workflows: List[WorkflowResponse]
    total: int
    page: int
    size: int