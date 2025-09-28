/**
 * SSE (Server-Sent Events) 服务，用于实时接收工作流执行状态
 */

export interface WorkflowExecutionMessage {
  type: 'workflow_status' | 'node_status' | 'workflow_result' | 'error'
  execution_id?: number
  node_id?: string
  status?: string
  data?: any
  timestamp?: string
  message?: string
}

export interface WorkflowExecutionCallbacks {
  onWorkflowStarted?: (data: any) => void
  onWorkflowCompleted?: (data: any) => void
  onWorkflowFailed?: (data: any) => void
  onNodeStarted?: (nodeId: string, data: any) => void
  onNodeCompleted?: (nodeId: string, data: any) => void
  onNodeFailed?: (nodeId: string, data: any) => void
  onWorkflowResult?: (data: any) => void
  onError?: (error: string) => void
}

export class WorkflowSSEService {
  private callbacks: WorkflowExecutionCallbacks = {}
  private isConnected = false
  private abortController: AbortController | null = null
  private currentExecutionId: number | null = null

  /**
   * 开始监听工作流执行
   */
  async startWorkflowExecution(workflowId: number, inputData: any = {}): Promise<void> {
    // 如果已经有连接，先关闭
    if (this.abortController) {
      this.disconnect()
    }

    try {
      // 获取认证token
      const token = localStorage.getItem('access_token')
      if (!token) {
        throw new Error('未找到认证token')
      }

      // 执行工作流并处理流式响应
      await this.executeWorkflow(workflowId, inputData, token)

    } catch (error) {
      console.error('启动工作流执行失败:', error)
      this.callbacks.onError?.(error instanceof Error ? error.message : '启动工作流执行失败')
      throw error
    }
  }

  /**
   * 执行工作流
   */
  private async executeWorkflow(workflowId: number, inputData: any, token: string): Promise<void> {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    const url = `${baseUrl}/workflows/${workflowId}/execute-stream`

    // 创建AbortController来管理请求
    this.abortController = new AbortController()

    // 构建符合后端期望的数据结构
    const requestData = {
      input_data: inputData
    }

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(requestData),
      signal: this.abortController.signal
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    // 处理流式响应
    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('无法获取响应流')
    }

    this.isConnected = true
    this.processStream(reader)
  }

  /**
   * 处理流式响应
   */
  private async processStream(reader: ReadableStreamDefaultReader<Uint8Array>): Promise<void> {
    const decoder = new TextDecoder()
    let buffer = ''

    try {
      while (true) {
        const { done, value } = await reader.read()
        
        if (done) {
          break
        }

        // 解码数据
        buffer += decoder.decode(value, { stream: true })
        
        // 处理完整的消息
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // 保留不完整的行

        for (const line of lines) {
          if (line.trim()) {
            try {
              // 解析SSE格式的数据
              if (line.startsWith('data: ')) {
                const jsonData = line.substring(6)
                const message: WorkflowExecutionMessage = JSON.parse(jsonData)
                this.handleMessage(message)
              }
            } catch (error) {
              console.error('解析SSE消息失败:', error, line)
            }
          }
        }
      }
    } catch (error) {
      console.error('处理SSE流失败:', error)
      this.callbacks.onError?.(error instanceof Error ? error.message : '处理SSE流失败')
    } finally {
      this.isConnected = false
      reader.releaseLock()
    }
  }



  /**
   * 处理接收到的消息
   */
  private handleMessage(message: WorkflowExecutionMessage): void {
    console.log('收到SSE消息:', message)

    switch (message.type) {
      case 'workflow_start':
        // 处理工作流开始消息
        this.callbacks.onWorkflowStarted?.(message)
        break
      case 'execution_update':
        // 处理执行更新消息
        this.handleExecutionUpdate(message)
        break
      case 'workflow_status':
        this.handleWorkflowStatus(message)
        break
      case 'node_status':
        this.handleNodeStatus(message)
        break
      case 'workflow_result':
        this.handleWorkflowResult(message)
        break
      case 'error':
        this.callbacks.onError?.(message.message || '工作流执行错误')
        break
      default:
        console.warn('未知的消息类型:', message.type)
    }
  }

  /**
   * 处理工作流状态消息
   */
  private handleWorkflowStatus(message: WorkflowExecutionMessage): void {
    if (message.execution_id) {
      this.currentExecutionId = message.execution_id
    }

    switch (message.status) {
      case 'started':
        this.callbacks.onWorkflowStarted?.(message.data)
        break
      case 'completed':
        this.callbacks.onWorkflowCompleted?.(message.data)
        break
      case 'failed':
        this.callbacks.onWorkflowFailed?.(message.data)
        break
    }
  }

  /**
   * 处理节点状态消息
   */
  private handleNodeStatus(message: WorkflowExecutionMessage): void {
    if (!message.node_id) return

    switch (message.status) {
      case 'started':
        this.callbacks.onNodeStarted?.(message.node_id, message.data)
        break
      case 'completed':
        this.callbacks.onNodeCompleted?.(message.node_id, message.data)
        break
      case 'failed':
        this.callbacks.onNodeFailed?.(message.node_id, message.data)
        break
    }
  }

  /**
   * 处理工作流结果消息
   */
  private handleWorkflowResult(message: WorkflowExecutionMessage): void {
    this.callbacks.onWorkflowResult?.(message.data)
  }

  /**
   * 处理执行更新消息
   */
  private handleExecutionUpdate(message: any): void {
    const { update_type, data } = message
    
    switch (update_type) {
      case 'node_status':
        // 转换为node_status格式并处理
        const nodeMessage = {
          type: 'node_status',
          node_id: data.node_id,
          status: data.status,
          data: data.data
        }
        this.handleNodeStatus(nodeMessage)
        break
      case 'workflow_status':
        // 转换为workflow_status格式并处理
        const workflowMessage = {
          type: 'workflow_status',
          status: data.status,
          data: data.data
        }
        this.handleWorkflowStatus(workflowMessage)
        break
      default:
        console.warn('未知的执行更新类型:', update_type)
    }
  }

  /**
   * 设置回调函数
   */
  setCallbacks(callbacks: WorkflowExecutionCallbacks): void {
    this.callbacks = { ...this.callbacks, ...callbacks }
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    if (this.abortController) {
      this.abortController.abort()
      this.abortController = null
    }
    this.isConnected = false
    this.currentExecutionId = null
  }

  /**
   * 获取连接状态
   */
  isConnectedToWorkflow(): boolean {
    return this.isConnected
  }

  /**
   * 获取当前执行ID
   */
  getCurrentExecutionId(): number | null {
    return this.currentExecutionId
  }
}

// 创建单例实例
export const workflowSSEService = new WorkflowSSEService()