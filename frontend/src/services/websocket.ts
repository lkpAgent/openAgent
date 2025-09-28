/**
 * WebSocket服务，用于实时接收工作流执行状态
 */

export interface WorkflowExecutionMessage {
  type: 'workflow_status' | 'node_status' | 'connection_established' | 'subscription_confirmed' | 'unsubscription_confirmed' | 'error' | 'pong'
  execution_id?: number
  node_id?: string
  status?: string
  data?: any
  timestamp?: string
  message?: string
  connection_id?: string
  user_id?: number
}

export interface WorkflowExecutionCallbacks {
  onWorkflowStarted?: (data: any) => void
  onWorkflowCompleted?: (data: any) => void
  onWorkflowFailed?: (data: any) => void
  onNodeStarted?: (nodeId: string, data: any) => void
  onNodeCompleted?: (nodeId: string, data: any) => void
  onNodeFailed?: (nodeId: string, data: any) => void
  onConnectionEstablished?: (connectionId: string) => void
  onError?: (error: string) => void
}

class WorkflowWebSocketService {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private callbacks: WorkflowExecutionCallbacks = {}
  private subscribedExecutions = new Set<number>()
  private connectionId: string | null = null
  private token: string | null = null
  private isConnecting = false

  /**
   * 连接WebSocket
   */
  async connect(token: string): Promise<void> {
    if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
      return
    }

    this.isConnecting = true
    this.token = token

    try {
      const wsUrl = `ws://localhost:8000/api/v1/ws/workflow-execution?token=${encodeURIComponent(token)}`
      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = () => {
        console.log('WebSocket连接已建立')
        this.reconnectAttempts = 0
        this.isConnecting = false
        
        // 发送心跳
        this.startHeartbeat()
      }

      this.ws.onmessage = (event) => {
        try {
          const message: WorkflowExecutionMessage = JSON.parse(event.data)
          this.handleMessage(message)
        } catch (error) {
          console.error('解析WebSocket消息失败:', error)
        }
      }

      this.ws.onclose = (event) => {
        console.log('WebSocket连接已关闭:', event.code, event.reason)
        this.isConnecting = false
        this.connectionId = null
        
        // 如果不是主动关闭，尝试重连
        if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.scheduleReconnect()
        }
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket连接错误:', error)
        this.isConnecting = false
        this.callbacks.onError?.('WebSocket连接错误')
      }

    } catch (error) {
      this.isConnecting = false
      console.error('创建WebSocket连接失败:', error)
      throw error
    }
  }

  /**
   * 断开WebSocket连接
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close(1000, '主动断开连接')
      this.ws = null
    }
    this.connectionId = null
    this.subscribedExecutions.clear()
    this.stopHeartbeat()
  }

  /**
   * 设置回调函数
   */
  setCallbacks(callbacks: WorkflowExecutionCallbacks): void {
    this.callbacks = { ...this.callbacks, ...callbacks }
  }

  /**
   * 订阅工作流执行状态
   */
  subscribeToExecution(executionId: number): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket未连接，无法订阅执行状态')
      return
    }

    this.subscribedExecutions.add(executionId)
    
    const message = {
      type: 'subscribe_execution',
      execution_id: executionId
    }

    this.ws.send(JSON.stringify(message))
    console.log(`已订阅工作流执行: ${executionId}`)
  }

  /**
   * 取消订阅工作流执行状态
   */
  unsubscribeFromExecution(executionId: number): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return
    }

    this.subscribedExecutions.delete(executionId)
    
    const message = {
      type: 'unsubscribe_execution',
      execution_id: executionId
    }

    this.ws.send(JSON.stringify(message))
    console.log(`已取消订阅工作流执行: ${executionId}`)
  }

  /**
   * 处理WebSocket消息
   */
  private handleMessage(message: WorkflowExecutionMessage): void {
    console.log('收到WebSocket消息:', message)

    switch (message.type) {
      case 'connection_established':
        this.connectionId = message.connection_id || null
        this.callbacks.onConnectionEstablished?.(message.connection_id || '')
        break

      case 'workflow_status':
        this.handleWorkflowStatus(message)
        break

      case 'node_status':
        this.handleNodeStatus(message)
        break

      case 'subscription_confirmed':
        console.log(`订阅确认: ${message.execution_id}`)
        break

      case 'unsubscription_confirmed':
        console.log(`取消订阅确认: ${message.execution_id}`)
        break

      case 'error':
        console.error('WebSocket错误:', message.message)
        this.callbacks.onError?.(message.message || '未知错误')
        break

      case 'pong':
        // 心跳响应，无需处理
        break

      default:
        console.warn('未知消息类型:', message.type)
    }
  }

  /**
   * 处理工作流状态消息
   */
  private handleWorkflowStatus(message: WorkflowExecutionMessage): void {
    const status = message.data?.status
    const data = message.data?.data || {}

    switch (status) {
      case 'started':
        this.callbacks.onWorkflowStarted?.(data)
        break
      case 'completed':
        this.callbacks.onWorkflowCompleted?.(data)
        break
      case 'failed':
        this.callbacks.onWorkflowFailed?.(data)
        break
    }
  }

  /**
   * 处理节点状态消息
   */
  private handleNodeStatus(message: WorkflowExecutionMessage): void {
    const nodeId = message.node_id
    const status = message.data?.status || message.status
    const data = message.data || {}

    if (!nodeId) return

    switch (status) {
      case 'started':
        this.callbacks.onNodeStarted?.(nodeId, data)
        break
      case 'completed':
        this.callbacks.onNodeCompleted?.(nodeId, data)
        break
      case 'failed':
        this.callbacks.onNodeFailed?.(nodeId, data)
        break
    }
  }

  /**
   * 安排重连
   */
  private scheduleReconnect(): void {
    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)
    
    console.log(`${delay}ms后尝试第${this.reconnectAttempts}次重连...`)
    
    setTimeout(() => {
      if (this.token) {
        this.connect(this.token)
      }
    }, delay)
  }

  /**
   * 心跳检测
   */
  private heartbeatInterval: number | null = null

  private startHeartbeat(): void {
    this.stopHeartbeat()
    
    this.heartbeatInterval = window.setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        const message = {
          type: 'ping',
          timestamp: new Date().toISOString()
        }
        this.ws.send(JSON.stringify(message))
      }
    }, 30000) // 每30秒发送一次心跳
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }
  }

  /**
   * 获取连接状态
   */
  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }

  /**
   * 获取连接ID
   */
  get getConnectionId(): string | null {
    return this.connectionId
  }
}

// 创建全局实例
export const workflowWebSocketService = new WorkflowWebSocketService()

export default workflowWebSocketService