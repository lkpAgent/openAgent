"""Workflow models."""

from sqlalchemy import Column, String, Text, Boolean, Integer, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from typing import Dict, Any, Optional, List
import enum

from ..db.base import BaseModel


class WorkflowStatus(enum.Enum):
    """工作流状态枚举"""
    DRAFT = "DRAFT"          # 草稿
    PUBLISHED = "PUBLISHED"  # 已发布
    ARCHIVED = "ARCHIVED"    # 已归档


class NodeType(enum.Enum):
    """节点类型枚举"""
    START = "start"          # 开始节点
    END = "end"              # 结束节点
    LLM = "llm"              # 大模型节点
    CONDITION = "condition"  # 条件分支节点
    LOOP = "loop"            # 循环节点
    CODE = "code"            # 代码执行节点
    HTTP = "http"            # HTTP请求节点
    TOOL = "tool"            # 工具节点


class ExecutionStatus(enum.Enum):
    """执行状态枚举"""
    PENDING = "pending"      # 等待执行
    RUNNING = "running"      # 执行中
    COMPLETED = "completed"  # 执行完成
    FAILED = "failed"        # 执行失败
    CANCELLED = "cancelled"  # 已取消


class Workflow(BaseModel):
    """工作流模型"""
    
    __tablename__ = "workflows"
    
    name = Column(String(100), nullable=False, comment="工作流名称")
    description = Column(Text, nullable=True, comment="工作流描述")
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.DRAFT, nullable=False, comment="工作流状态")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否激活")
    
    # 工作流定义（JSON格式存储节点和连接信息）
    definition = Column(JSON, nullable=False, comment="工作流定义")
    
    # 版本信息
    version = Column(String(20), default="1.0.0", nullable=False, comment="版本号")
    
    # 关联用户
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="所有者ID")
    
    # 关系
    executions = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Workflow(id={self.id}, name='{self.name}', status='{self.status.value}')>"
    
    def to_dict(self, include_definition=True):
        """转换为字典"""
        data = super().to_dict()
        data.update({
            'name': self.name,
            'description': self.description,
            'status': self.status.value,
            'is_active': self.is_active,
            'version': self.version,
            'owner_id': self.owner_id
        })
        
        if include_definition:
            data['definition'] = self.definition
            
        return data


class WorkflowExecution(BaseModel):
    """工作流执行记录"""
    
    __tablename__ = "workflow_executions"
    
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False, comment="工作流ID")
    status = Column(Enum(ExecutionStatus), default=ExecutionStatus.PENDING, nullable=False, comment="执行状态")
    
    # 执行输入和输出
    input_data = Column(JSON, nullable=True, comment="输入数据")
    output_data = Column(JSON, nullable=True, comment="输出数据")
    
    # 执行信息
    started_at = Column(String(50), nullable=True, comment="开始时间")
    completed_at = Column(String(50), nullable=True, comment="完成时间")
    error_message = Column(Text, nullable=True, comment="错误信息")
    
    # 执行者
    executor_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="执行者ID")
    
    # 关系
    workflow = relationship("Workflow", back_populates="executions")
    node_executions = relationship("NodeExecution", back_populates="workflow_execution", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<WorkflowExecution(id={self.id}, workflow_id={self.workflow_id}, status='{self.status.value}')>"
    
    def to_dict(self, include_nodes=False):
        """转换为字典"""
        data = super().to_dict()
        data.update({
            'workflow_id': self.workflow_id,
            'status': self.status.value,
            'input_data': self.input_data,
            'output_data': self.output_data,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'error_message': self.error_message,
            'executor_id': self.executor_id
        })
        
        if include_nodes:
            data['node_executions'] = [node.to_dict() for node in self.node_executions]
            
        return data


class NodeExecution(BaseModel):
    """节点执行记录"""
    
    __tablename__ = "node_executions"
    
    workflow_execution_id = Column(Integer, ForeignKey("workflow_executions.id"), nullable=False, comment="工作流执行ID")
    node_id = Column(String(50), nullable=False, comment="节点ID")
    node_type = Column(Enum(NodeType), nullable=False, comment="节点类型")
    node_name = Column(String(100), nullable=False, comment="节点名称")
    
    # 执行状态和结果
    status = Column(Enum(ExecutionStatus), default=ExecutionStatus.PENDING, nullable=False, comment="执行状态")
    input_data = Column(JSON, nullable=True, comment="输入数据")
    output_data = Column(JSON, nullable=True, comment="输出数据")
    
    # 执行时间
    started_at = Column(String(50), nullable=True, comment="开始时间")
    completed_at = Column(String(50), nullable=True, comment="完成时间")
    duration_ms = Column(Integer, nullable=True, comment="执行时长(毫秒)")
    
    # 错误信息
    error_message = Column(Text, nullable=True, comment="错误信息")
    
    # 关系
    workflow_execution = relationship("WorkflowExecution", back_populates="node_executions")
    
    def __repr__(self):
        return f"<NodeExecution(id={self.id}, node_id='{self.node_id}', status='{self.status.value}')>"
    
    def to_dict(self):
        """转换为字典"""
        data = super().to_dict()
        data.update({
            'workflow_execution_id': self.workflow_execution_id,
            'node_id': self.node_id,
            'node_type': self.node_type.value,
            'node_name': self.node_name,
            'status': self.status.value,
            'input_data': self.input_data,
            'output_data': self.output_data,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'duration_ms': self.duration_ms,
            'error_message': self.error_message
        })
        
        return data