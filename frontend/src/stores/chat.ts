import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { chatApi } from '@/api'
import type { 
  Conversation, 
  ConversationCreate, 
  ConversationUpdate, 
  Message, 
  ChatRequest 
} from '@/types'

export const useChatStore = defineStore('chat', () => {
  // State
  const conversations = ref<Conversation[]>([])
  const currentConversation = ref<Conversation | null>(null)
  const messages = ref<Message[]>([])
  const isLoading = ref(false)
  const isStreaming = ref(false)
  const isLoadingMessages = ref(false)
  const searchQuery = ref('')
  const includeArchived = ref(false)
  const totalCount = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(20)
  
  // Getters
  const sortedConversations = computed(() => {
    return [...conversations.value].sort((a, b) => 
      new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
    )
  })
  
  const activeConversations = computed(() => {
    return conversations.value.filter(conv => !conv.is_archived)
  })
  
  const archivedConversations = computed(() => {
    return conversations.value.filter(conv => conv.is_archived)
  })
  
  // Actions
  const loadConversations = async (params?: {
    search?: string
    include_archived?: boolean
    page?: number
    limit?: number
    order_by?: string
    order_desc?: boolean
  }) => {
    try {
      isLoading.value = true
      const queryParams = {
        search: params?.search || searchQuery.value,
        include_archived: params?.include_archived ?? includeArchived.value,
        skip: ((params?.page || currentPage.value) - 1) * pageSize.value,
        limit: params?.limit || pageSize.value,
        order_by: params?.order_by || 'updated_at',
        order_desc: params?.order_desc ?? true
      }
      
      const response = await chatApi.getConversations(queryParams)
      conversations.value = response.data.data || response.data || []
      
      // Load total count
      const countResponse = await chatApi.getConversationsCount({
        search: queryParams.search,
        include_archived: queryParams.include_archived
      })
      totalCount.value = countResponse.data.count || countResponse.data.data?.count || 0
    } catch (error: any) {
      console.error('Load conversations failed:', error)
      ElMessage.error('加载对话列表失败')
    } finally {
      isLoading.value = false
    }
  }
  
  const createConversation = async (data: ConversationCreate) => {
    try {
      isLoading.value = true
      console.log('Creating conversation with data:', data)
      const response = await chatApi.createConversation(data)
      console.log('Create conversation response:', response)
      
      const newConversation = response.data
      console.log('New conversation:', newConversation)
      
      conversations.value.unshift(newConversation)
      currentConversation.value = newConversation
      messages.value = []
      
      ElMessage.success('创建对话成功')
      return newConversation
    } catch (error: any) {
      console.error('Create conversation failed:', error)
      console.error('Error response:', error.response?.data)
      console.error('Error status:', error.response?.status)
      ElMessage.error('创建对话失败: ' + (error.response?.data?.detail || error.message))
      return null
    } finally {
      isLoading.value = false
    }
  }
  
  const loadConversation = async (conversationId: string) => {
    try {
      isLoading.value = true
      const response = await chatApi.getConversation(conversationId)
      currentConversation.value = response.data.data || response.data
      
      // Update conversation in list if exists
      const index = conversations.value.findIndex(conv => conv.id.toString() === conversationId)
      if (index !== -1) {
        conversations.value[index] = currentConversation.value
      }
      
      return currentConversation.value
    } catch (error: any) {
      console.error('Load conversation failed:', error)
      ElMessage.error('加载对话失败')
      return null
    } finally {
      isLoading.value = false
    }
  }
  
  const updateConversation = async (conversationId: string, data: ConversationUpdate) => {
    try {
      const response = await chatApi.updateConversation(conversationId, data)
      const updatedConversation = response.data.data || response.data
      
      // Update in list
      const index = conversations.value.findIndex(conv => conv.id.toString() === conversationId)
      if (index !== -1) {
        conversations.value[index] = updatedConversation
      }
      
      // Update current if it's the same
      if (currentConversation.value?.id.toString() === conversationId) {
        currentConversation.value = updatedConversation
      }
      
      ElMessage.success('对话更新成功')
      return updatedConversation
    } catch (error: any) {
      console.error('Update conversation failed:', error)
      ElMessage.error('更新对话失败')
      return null
    }
  }
  
  const deleteConversation = async (conversationId: string) => {
    try {
      await chatApi.deleteConversation(conversationId)
      
      // Remove from list
      conversations.value = conversations.value.filter(conv => conv.id.toString() !== conversationId)
      
      // Clear current if it's the same
      if (currentConversation.value?.id.toString() === conversationId) {
        currentConversation.value = null
        messages.value = []
      }
      
      ElMessage.success('对话删除成功')
      return true
    } catch (error: any) {
      console.error('Delete conversation failed:', error)
      ElMessage.error('删除对话失败')
      return false
    }
  }
  
  const loadMessages = async (conversationId: string, forceReload = false) => {
    try {
      isLoadingMessages.value = true
      const response = await chatApi.getMessages(conversationId)
      const loadedMessages = response.data.data || response.data || []
      
      // 只有在强制重新加载或消息为空时才替换消息数组
      console.log(forceReload)
      if (forceReload || messages.value.length === 0) {
        messages.value = loadedMessages
      }
      // messages.value = loadedMessages
      return loadedMessages
    } catch (error: any) {
      console.error('Load messages failed:', error)
      ElMessage.error('加载消息失败')
      return []
    } finally {
      isLoadingMessages.value = false
    }
  }
  
  const sendMessage = async (data: ChatRequest) => {
    try {
      console.log('sendMessage called with data:', data)
      isStreaming.value = true
      
      // Add user message to local state immediately
      const userMessage: Message = {
        id: `temp-${Date.now()}`,
        conversation_id: data.conversation_id || '',
        role: 'user',
        content: data.message,
        message_type: 'text',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }
      messages.value.push(userMessage)
      
      console.log('Calling chatApi.sendMessage...')
      // Convert conversation_id to string for API call
      const conversationId = String(data.conversation_id!)
      const response = await chatApi.sendMessage(conversationId, data)
      console.log('API response:', response)
      const { user_message, assistant_message } = response.data
      
      // Remove temp user message and add real messages
      messages.value = messages.value.filter(msg => msg.id !== userMessage.id)
      
      // Add both user and assistant messages from response
      messages.value.push(user_message)
      messages.value.push(assistant_message)
      
      // Update current conversation if needed
      if (currentConversation.value) {
        const index = conversations.value.findIndex(conv => conv.id === currentConversation.value!.id)
        if (index !== -1) {
          // Update conversation in list
          conversations.value[index] = { ...conversations.value[index], updated_at: new Date().toISOString() }
        }
      }
      
      return { user_message, assistant_message }
    } catch (error: any) {
      console.error('Send message failed:', error)
      console.error('Error details:', error.response?.data || error.message)
      ElMessage.error('发送消息失败: ' + (error.response?.data?.detail || error.message))
      
      // Remove temp user message on error
      messages.value = messages.value.filter(msg => !msg.id.startsWith('temp-'))
      
      return null
    } finally {
      isStreaming.value = false
    }
  }
  
  const sendMessageStream = async (data: ChatRequest, onChunk?: (chunk: string) => void) => {
    try {
      isStreaming.value = true
      
      // Add user message immediately
      const userMessage: Message = {
        id: Date.now(),
        conversation_id: data.conversation_id || 0,
        role: 'user',
        content: data.message,
        message_type: 'text',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }
      messages.value.push(userMessage)
      
      // Add assistant message placeholder
      const assistantMessage: Message = {
        id: Date.now() + 1,
        conversation_id: data.conversation_id || 0,
        role: 'assistant',
        content: '',
        message_type: 'text',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }
      messages.value.push(assistantMessage)
      
      // Convert conversation_id to string for API call
      const conversationId = String(data.conversation_id!)
      const stream = await chatApi.sendMessageStreamFetch(conversationId, data)
      if (!stream) {
        throw new Error('Failed to get stream')
      }
      
      const reader = stream.getReader()
      const decoder = new TextDecoder()
      
      try {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          
          const chunk = decoder.decode(value, { stream: true })
          const lines = chunk.split('\n')
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6).trim()
              if (data === '[DONE]') {
                break
              }
              
              try {
                const parsed = JSON.parse(data)
                
                // 处理智能体模式的流式响应
                const lastMessageIndex = messages.value.length - 1
                if (lastMessageIndex >= 0 && messages.value[lastMessageIndex].role === 'assistant') {
                  // 初始化智能体数据结构
                  if (!messages.value[lastMessageIndex].agent_data) {
                    messages.value[lastMessageIndex].agent_data = {
                      status: 'thinking',
                      steps: [],
                      current_tool: null
                    }
                  }
                  
                  const agentData = messages.value[lastMessageIndex].agent_data
                  
                  if (parsed.type === 'thinking') {
                    // 处理思考过程
                    console.log('🤔 Thinking:', parsed.content)
                    agentData.status = 'thinking'
                    agentData.steps.push({
                      id: Date.now(),
                      type: 'thinking',
                      content: parsed.content,
                      timestamp: new Date().toISOString(),
                      node_name: parsed.node_name || 'agent',
                      raw_output: parsed.raw_output
                    })
                    
                  } else if (parsed.type === 'tool_end') {
                    // 处理工具执行完成
                    console.log('🔧 Tool end:', parsed.content)
                    agentData.status = 'tool_calling'
                    agentData.steps.push({
                      id: Date.now(),
                      type: 'tool_end',
                      content: parsed.content,
                      timestamp: new Date().toISOString(),
                      node_name: parsed.node_name || 'tools',
                      tool_name: parsed.tool_name,
                      tool_output: parsed.tool_output
                    })
                    
                  } else if (parsed.type === 'response') {
                    // 处理最终响应
                    console.log('💬 Response:', parsed.content)
                    agentData.status = 'completed'
                    agentData.steps.push({
                      id: Date.now(),
                      type: 'response',
                      content: parsed.content,
                      timestamp: new Date().toISOString(),
                      intermediate_steps: parsed.intermediate_steps
                    })
                    
                    // 设置消息内容
                    messages.value[lastMessageIndex].content = parsed.content
                    
                  } else if (parsed.type === 'status') {
                    // 处理状态消息
                    console.log('📊 Status:', parsed.content)
                    messages.value[lastMessageIndex].status = parsed.content
                  }
                }
                
                // 处理其他类型的流式数据
                if (parsed.type === 'content') {
                  // 处理内容块
                  const lastMessageIndex = messages.value.length - 1
                  if (lastMessageIndex >= 0 && messages.value[lastMessageIndex].role === 'assistant') {
                    messages.value[lastMessageIndex].content += parsed.content
                  }
                } else if (parsed.type === 'tool' || parsed.type === 'tool_result') {
                  // 工具执行相关消息
                  console.log('Tool execution:', parsed.content)
                  const lastMessageIndex = messages.value.length - 1
                  if (lastMessageIndex >= 0 && messages.value[lastMessageIndex].role === 'assistant') {
                    // 显示工具执行状态
                    messages.value[lastMessageIndex].status = parsed.content
                  }
                } else if (parsed.type === 'content') {
                  // 流式内容块，累积到消息内容
                  const lastMessageIndex = messages.value.length - 1
                  if (lastMessageIndex >= 0 && messages.value[lastMessageIndex].role === 'assistant') {
                    if (!messages.value[lastMessageIndex].content) {
                      messages.value[lastMessageIndex].content = ''
                    }
                    messages.value[lastMessageIndex].content += parsed.content
                    // 清除状态显示
                    messages.value[lastMessageIndex].status = undefined
                    
                    // 更新智能体状态为生成中
                    if (messages.value[lastMessageIndex].agent_data) {
                      messages.value[lastMessageIndex].agent_data.status = 'generating'
                    }
                  }
                  onChunk?.(parsed.content)
                } else if (parsed.type === 'response' && parsed.content) {
                  // 完整响应内容，直接设置
                  const lastMessageIndex = messages.value.length - 1
                  if (lastMessageIndex >= 0 && messages.value[lastMessageIndex].role === 'assistant') {
                    messages.value[lastMessageIndex].content = parsed.content
                    // 清除状态显示
                    messages.value[lastMessageIndex].status = undefined
                    
                    // 更新智能体状态为完成
                    if (messages.value[lastMessageIndex].agent_data) {
                      messages.value[lastMessageIndex].agent_data.status = 'completed'
                      // 添加完成步骤
                      const step = {
                        id: Date.now(),
                        type: 'completed',
                        content: '回答生成完成',
                        timestamp: new Date().toISOString()
                      }
                      messages.value[lastMessageIndex].agent_data.steps.push(step)
                    }
                    
                    // 兼容旧的思考过程数据
                    if (messages.value[lastMessageIndex].thinking_data) {
                      messages.value[lastMessageIndex].thinking_data.status = 'completed'
                      messages.value[lastMessageIndex].thinking_data.current_step = '思考完成'
                    }
                  }
                  onChunk?.(parsed.content)
                } else if (parsed.content) {
                  // 兼容旧格式的流式响应
                  const lastMessageIndex = messages.value.length - 1
                  if (lastMessageIndex >= 0 && messages.value[lastMessageIndex].role === 'assistant') {
                    if (!messages.value[lastMessageIndex].content) {
                      messages.value[lastMessageIndex].content = ''
                    }
                    messages.value[lastMessageIndex].content += parsed.content
                  }
                  onChunk?.(parsed.content)
                }
                
                // 检查是否流式传输完成
                if (parsed.done === true || parsed.finish_reason) {
                  // 流式传输完成
                  break
                }
              } catch (e) {
                console.warn('Failed to parse SSE data:', data)
              }
            }
          }
        }
      } finally {
        reader.releaseLock()
      }
      
    } catch (error: any) {
      console.error('Stream message failed:', error)
      ElMessage.error('发送消息失败: ' + (error.response?.data?.detail || error.message))
      
      // Remove temp messages on error
      messages.value = messages.value.filter(msg => msg.id < Date.now() - 1000)
    } finally {
      isStreaming.value = false
    }
  }
  
  const setCurrentConversation = async (conversationId: number) => {
    try {
      const conversation = await loadConversation(conversationId.toString())
      if (conversation) {
        // 只有在消息为空且切换到不同对话时才加载消息
        // 如果当前有消息且是同一个对话，不要重新加载以保持消息连续性
        const shouldLoadMessages = messages.value.length === 0 && 
          (!currentConversation.value || currentConversation.value.id !== conversationId)
        
        if (shouldLoadMessages) {
          await loadMessages(conversationId.toString())
        }
      }
      return conversation
    } catch (error) {
      console.error('Set current conversation failed:', error)
      return null
    }
  }
  
  const clearCurrentConversation = () => {
    currentConversation.value = null
    messages.value = []
  }
  
  const clearMessages = () => {
    messages.value = []
  }
  
  const addMessage = (message: Message) => {
    messages.value.push(message)
  }
  
  const archiveConversation = async (conversationId: string) => {
    try {
      await chatApi.archiveConversation(conversationId)
      const conversation = conversations.value.find(c => c.id.toString() === conversationId)
      if (conversation) {
        conversation.is_archived = true
      }
      ElMessage.success('对话已归档')
    } catch (error: any) {
      console.error('Archive conversation failed:', error)
      ElMessage.error('归档对话失败')
    }
  }
  
  const unarchiveConversation = async (conversationId: string) => {
    try {
      await chatApi.unarchiveConversation(conversationId)
      const conversation = conversations.value.find(c => c.id.toString() === conversationId)
      if (conversation) {
        conversation.is_archived = false
      }
      ElMessage.success('对话已取消归档')
    } catch (error: any) {
      console.error('Unarchive conversation failed:', error)
      ElMessage.error('取消归档对话失败')
    }
  }
  
  const setSearchQuery = (query: string) => {
    searchQuery.value = query
  }
  
  const setIncludeArchived = (include: boolean) => {
    includeArchived.value = include
  }
  
  const setCurrentPage = (page: number) => {
    currentPage.value = page
  }
  
  return {
    // State
    conversations,
    currentConversation,
    messages,
    isLoading,
    isStreaming,
    isLoadingMessages,
    searchQuery,
    includeArchived,
    totalCount,
    currentPage,
    pageSize,
    
    // Getters
    sortedConversations,
    activeConversations,
    archivedConversations,
    
    // Actions
    loadConversations,
    createConversation,
    loadConversation,
    updateConversation,
    deleteConversation,
    loadMessages,
    sendMessage,
    sendMessageStream,
    setCurrentConversation,
    clearCurrentConversation,
    clearMessages,
    addMessage,
    archiveConversation,
    unarchiveConversation,
    setSearchQuery,
    setIncludeArchived,
    setCurrentPage
  }
})