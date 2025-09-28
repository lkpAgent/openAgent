import { api } from './request'
import type { PaginationParams, NodeInputOutput } from '@/types'

// 工作流类型定义
export interface WorkflowNode {
  id: string
  type: 'start' | 'end' | 'llm' | 'condition' | 'code' | 'http'
  name: string
  description?: string
  position: {
    x: number
    y: number
  }
  config: Record<string, any>
  parameters?: NodeInputOutput
}

export interface WorkflowConnection {
  id: string
  from: string
  to: string
}

export interface WorkflowDefinition {
  nodes: WorkflowNode[]
  connections: WorkflowConnection[]
}

export interface Workflow {
  id: number
  name: string
  description?: string
  version: string
  status: 'DRAFT' | 'PUBLISHED' | 'ARCHIVED'
  definition: WorkflowDefinition
  created_at: string
  updated_at: string
  created_by: number
  updated_by: number
}

export interface WorkflowCreate {
  name: string
  description?: string
  version?: string
  definition: WorkflowDefinition
}

export interface WorkflowUpdate {
  name?: string
  description?: string
  version?: string
  definition?: WorkflowDefinition
}

export interface WorkflowExecution {
  id: number
  workflow_id: number
  status: 'pending' | 'running' | 'completed' | 'failed'
  input_data?: Record<string, any>
  output_data?: Record<string, any>
  error_message?: string
  started_at: string
  completed_at?: string
  executor_id: number
  node_executions?: NodeExecution[]
  created_at: string
  updated_at: string
}

export interface WorkflowExecuteRequest {
  input_data?: Record<string, any>
}

export interface NodeExecution {
  id: number
  node_id: string
  node_type: string
  node_name: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  input_data?: Record<string, any>
  output_data?: Record<string, any>
  error_message?: string
  started_at?: string
  completed_at?: string
  duration_ms?: number
}

// 工作流API
export const workflowApi = {
  // 获取工作流列表
  getWorkflows(params?: PaginationParams & {
    search?: string
    status?: 'DRAFT' | 'PUBLISHED' | 'ARCHIVED'
    created_by?: number
  }) {
    return api.get<{
      workflows: Workflow[]
      total: number
      page: number
      size: number
    }>('/workflows/', { params })
  },

  // 获取工作流详情
  getWorkflow(workflowId: number) {
    return api.get<Workflow>(`/workflows/${workflowId}`)
  },

  // 创建工作流
  createWorkflow(data: WorkflowCreate) {
    return api.post<Workflow>('/workflows/', data)
  },

  // 更新工作流
  updateWorkflow(workflowId: number, data: WorkflowUpdate) {
    return api.put<Workflow>(`/workflows/${workflowId}`, data)
  },

  // 删除工作流
  deleteWorkflow(workflowId: number) {
    return api.delete(`/workflows/${workflowId}`)
  },

  // 激活工作流
  activateWorkflow(workflowId: number) {
    return api.post<Workflow>(`/workflows/${workflowId}/activate`)
  },

  // 停用工作流
  deactivateWorkflow(workflowId: number) {
    return api.post<Workflow>(`/workflows/${workflowId}/deactivate`)
  },

  // 执行工作流
  executeWorkflow(workflowId: number, data: WorkflowExecuteRequest) {
    return api.post<WorkflowExecution>(`/workflows/${workflowId}/execute`, data)
  },

  // 获取工作流执行历史
  getWorkflowExecutions(workflowId: number, params?: PaginationParams) {
    return api.get<{
      executions: WorkflowExecution[]
      total: number
      page: number
      size: number
    }>(`/workflows/${workflowId}/executions`, { params })
  },

  // 获取执行详情
  getExecution(executionId: number) {
    return api.get<WorkflowExecution>(`/workflows/executions/${executionId}`)
  },

  // 获取节点执行详情
  getNodeExecutions(executionId: number) {
    return api.get<{
      node_executions: NodeExecution[]
    }>(`/workflows/executions/${executionId}/nodes`)
  },

  // 停止执行
  stopExecution(executionId: number) {
    return api.post(`/workflows/executions/${executionId}/stop`)
  }
}