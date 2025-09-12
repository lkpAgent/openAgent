<template>
  <div class="chat-container">
    <!-- 对话模式选择头部 -->
    <div class="mode-selector">
      <div class="mode-tabs">
        <div 
          v-for="mode in chatModes" 
          :key="mode.key"
          :class="['mode-tab', { active: currentMode === mode.key }]"
          @click="switchMode(mode.key)"
        >
          <el-icon><component :is="mode.icon" /></el-icon>
          <span>{{ mode.label }}</span>
        </div>
        
        <!-- 历史对话按钮 -->
        <div 
          :class="['mode-tab', 'history-tab', { active: showHistoryPanel }]"
          @click="toggleHistoryPanel"
        >
          <el-icon><Clock /></el-icon>
          <span>历史对话</span>
        </div>
      </div>
      
      <div class="mode-config">
        <!-- RAG模式配置 -->
        <div v-if="currentMode === 'rag'" class="config-item">
          <el-select 
            v-model="selectedKnowledgeBase" 
            placeholder="选择知识库"
            size="small"
            style="width: 200px;"
          >
            <el-option
              v-for="kb in knowledgeBases"
              :key="kb.id"
              :label="kb.name"
              :value="kb.id"
            />
          </el-select>
        </div>
        

        
        <el-button 
          type="primary" 
          size="small" 
          @click="createNewConversation"
          :icon="Promotion"
        >
          新对话
        </el-button>
      </div>
    </div>

    <!-- 历史对话面板 -->
    <div v-if="showHistoryPanel" class="history-panel" @click.self="showHistoryPanel = false">
      <div class="history-content">
        <div class="history-header">
          <h3>历史对话</h3>
          <el-button size="small" text @click="toggleHistoryPanel">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
        
        <!-- 搜索框 -->
        <div class="history-search">
          <el-input
            :model-value="chatStore.searchQuery"
            @input="handleSearch"
            placeholder="搜索对话..."
            size="small"
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
        
        <div class="history-list">
          <div 
            v-for="conversation in filteredConversations" 
            :key="conversation.id"
            class="history-item"
            @click="selectConversation(conversation)"
          >
            <div class="conversation-info">
              <div class="conversation-title">{{ conversation.title }}</div>
              <div class="conversation-meta">
                <span class="conversation-time">{{ formatConversationTime(conversation.updated_at) }}</span>
                <span class="conversation-count">{{ conversation.message_count }}条消息</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 左侧对话区域 -->
      <div class="chat-area" :class="{ 'with-agent-panel': currentMode === 'agent' }">
        <!-- 消息列表 -->
        <div class="messages-container" ref="messagesContainer">
          <!-- 欢迎消息 -->
          <div v-if="messages.length === 0" class="welcome-message">
            <div class="welcome-content">
              <h3>{{ chatModes.find(m => m.key === currentMode)?.label }}模式</h3>
              <p>{{ chatModes.find(m => m.key === currentMode)?.description }}</p>
              
              <div class="quick-actions">
                <div class="quick-action-title">快速开始：</div>
                <div class="quick-buttons">
                  <el-button 
                    v-for="action in quickActions" 
                    :key="action.text"
                    size="small"
                    type="primary"
                    plain
                    @click="inputMessage = action.text; sendMessage()"
                  >
                    {{ action.text }}
                  </el-button>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 真实消息 -->
          <div v-for="message in messages" :key="message.id" class="message-item">
            <div :class="['message', message.role]">
              <div class="message-avatar">
                <el-avatar v-if="message.role === 'user'" :size="32">
                  <el-icon><User /></el-icon>
                </el-avatar>
                <el-avatar v-else :size="32" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)">
                  <el-icon><Service /></el-icon>
                </el-avatar>
              </div>
              
              <div class="message-content">
                <!-- 智能体模式下的简化状态显示 -->
                <div v-if="message.role === 'assistant' && currentMode === 'agent' && message.agent_data && message.agent_data.status !== 'completed'" class="agent-status-simple">
                  <!-- 显示最新步骤的图标和状态文字，但只在未完成时显示 -->
                  <div v-if="message.agent_data.steps && message.agent_data.steps.length > 0" class="agent-current-status">
                    <template v-for="(step, index) in message.agent_data.steps" :key="step.id">
                      <div v-if="index === message.agent_data.steps.length - 1 && step.type !== 'response' && !hasResponseStep(message.agent_data.steps)" class="current-step-display">
                        <span v-if="step.type === 'thinking'" class="step-status">
                          <span class="type-icon">🤔</span>
                          <span class="status-text">大模型思考中</span>
                        </span>
                        <span v-else-if="step.type.includes('tool')" class="step-status">
                          <span class="type-icon">🔧</span>
                          <span class="status-text">正在调用工具: {{ step.tool_name || '未知工具' }}</span>
                        </span>
                        <span v-else class="step-status">
                          <span class="type-icon">📝</span>
                          <span class="status-text">处理中</span>
                        </span>
                      </div>
                    </template>
                  </div>
                </div>
                
                <!-- 如果有状态信息，显示状态 -->
                <div v-if="message.status" class="message-status">
                  <el-icon class="status-icon"><Loading /></el-icon>
                  <span>{{ message.status }}</span>
                </div>
                <!-- 如果是空的assistant消息且没有状态，显示打字指示器 -->
                <div v-else-if="message.role === 'assistant' && message.content === ''" class="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
                <!-- 智能体模式：只显示最后一个response类型的内容 -->
                <div v-else-if="message.role === 'assistant' && currentMode === 'agent'" class="message-text">
                  <!-- 检查是否有response类型的步骤，如果有则显示最后一个response的内容 -->
                  <div v-if="message.agent_data && message.agent_data.steps">
                    <div v-if="getLastResponseStep(message.agent_data.steps)" v-html="renderMarkdown(getLastResponseStep(message.agent_data.steps).content)"></div>
                  </div>
                  <!-- 如果没有response步骤但有消息内容，显示消息内容 -->
                  <div v-else-if="message.content" v-html="renderMarkdown(message.content)"></div>
                </div>
                <!-- 普通模式显示正常消息内容 -->
                <div v-else class="message-text" v-html="renderMarkdown(message.content)"></div>
                <div class="message-time">{{ formatTime(message.created_at) }}</div>
              </div>
            </div>
          </div>
          
          <!-- 加载中状态 - 只在没有空的assistant消息时显示 -->
          <div v-if="isLoading && !hasEmptyAssistantMessage" class="message-item">
            <div class="message assistant">
              <div class="message-avatar">
                <el-avatar :size="32" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%)">
                  <el-icon><Service /></el-icon>
                </el-avatar>
              </div>
              <div class="message-content">
                <div class="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 输入区域 -->
        <div class="input-area">
          <div class="input-container">
            <el-input
              v-model="inputMessage"
              type="textarea"
              :rows="3"
              placeholder="输入您的问题..."
              @keydown.ctrl.enter="sendMessage"
              :disabled="isLoading"
            />
            <div class="input-actions">
              <div class="input-tips">
                <span>Ctrl + Enter 发送</span>
              </div>
              <el-button 
                type="primary" 
                @click="sendMessage"
                :loading="isLoading"
                :disabled="!inputMessage.trim()"
              >
                发送
              </el-button>
            </div>
          </div>
        </div>
      </div>
      

      <!-- 右侧智能体思考流程展示区域 -->
      <div v-if="currentMode === 'agent'" class="agent-panel">
        <div class="agent-header">
          <h3>🤖 智能体思考流程</h3>
          <el-tag :type="getAgentStatusType(currentAgentData?.status || 'idle')" size="small">
            {{ getAgentStatusText(currentAgentData?.status || 'idle') }}
          </el-tag>
        </div>
        
        <div v-if="currentAgentData?.steps?.length > 0" class="agent-content">
          <!-- 智能体思考流程列表 -->
          <div class="thinking-steps">
            <div 
              v-for="(step, index) in getUniqueSteps(currentAgentData.steps)" 
              :key="step.id || index" 
              class="thinking-step"
              :class="`step-${step.type}`"
            >
              <!-- 简化的步骤显示 -->
              <div class="step-header">
                <div class="step-type-info">
                  <span v-if="step.type === 'thinking'" class="type-icon">🤔</span>
                  <span v-else-if="step.type === 'tools_end'" class="type-icon">🔧</span>
                  <span v-else-if="step.type === 'response_start'" class="type-icon">💬</span>
                  <span v-else-if="step.type === 'complete'" class="type-icon">✅</span>
                  <span v-else class="type-icon">📝</span>
                  
                  <span class="type-name">
                    <span v-if="step.type === 'thinking'">思考中</span>
                    <span v-else-if="step.type === 'tools_end'">调用工具</span>
                    <span v-else-if="step.type === 'response_start'">正在输出</span>
                    <span v-else-if="step.type === 'complete'">本次对话过程完成</span>
                    <span v-else>处理中</span>
                  </span>
                  
                  <span v-if="step.type.includes('tool') && step.tool_name" class="tool-info">
                    : {{ step.tool_name }}
                  </span>
                </div>
              </div>
              
              <!-- 内容 -->
               <div v-if="step.content && step.type !== 'response'" class="step-content">
                 {{ step.content }}
               </div>
               
               <!-- 工具输出 -->
               <div v-if="step.type === 'tools_end' && step.tool_output" class="tool-output">
                 <div class="output-label">工具输出:</div>
                 <div class="output-content">{{ step.tool_output }}</div>
               </div>
                
                <!-- 时间戳 -->
                <div class="step-timestamp">
                  <el-icon><Clock /></el-icon>
                  <span>{{ formatTime(step.timestamp) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 空状态已移除 -->
      </div>

    </div> 
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  ChatDotRound, 
  Collection, 
  Service,
  Promotion,
  Setting,
  Check,
  Loading,
  Clock,
  User,
  Close,
  Search,
  Tools,
  Share
} from '@element-plus/icons-vue'
import { useChatStore } from '@/stores/chat'
import { useKnowledgeStore } from '@/stores/knowledge'
import { formatTime } from '@/utils'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'
import type { ThinkingData } from '@/types'

const router = useRouter()
const chatStore = useChatStore()
const knowledgeStore = useKnowledgeStore()

// 配置markdown渲染器
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  highlight: function (str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return hljs.highlight(str, { language: lang }).value
      } catch (__) {}
    }
    return '' // 使用外部默认转义
  }
})

// 渲染markdown内容的方法
const renderMarkdown = (content: string) => {
  if (!content) return ''
  return md.render(content)
}

// 历史对话相关 - 使用chatStore中的真实数据
const conversations = computed(() => chatStore.conversations)
const filteredConversations = computed(() => {
  if (!chatStore.searchQuery.trim()) {
    return conversations.value
  }
  const query = chatStore.searchQuery.toLowerCase()
  return conversations.value.filter(conv => 
    conv.title.toLowerCase().includes(query)
  )
})

// 对话模式相关
const currentMode = ref('free')
const selectedKnowledgeBase = ref('')
const selectedAgent = ref('')

// 基础状态
const inputMessage = ref('')
const isLoading = ref(false)
const messagesContainer = ref<HTMLElement>()
const showHistoryPanel = ref(false)

// 检测是否有空的assistant消息（流式传输占位符）
const hasEmptyAssistantMessage = computed(() => {
  const lastMessage = messages.value[messages.value.length - 1]
  return lastMessage && lastMessage.role === 'assistant' && lastMessage.content === ''
})

// 对话模式配置
const chatModes = [
  {
    key: 'free',
    label: '自由对话',
    description: '自然语言交流',
    icon: ChatDotRound
  },
  {
    key: 'rag',
    label: 'RAG对话',
    description: '知识库问答',
    icon: Collection
  },
  {
    key: 'agent',
    label: '智能体对话',
    description: '智能体协作处理复杂任务',
    icon: Service
  }
]

// 模拟智能体数据
const availableAgents = ref([
  { id: '1', name: '客服助手', description: '专业的客户服务支持' },
  { id: '2', name: '技术顾问', description: '技术问题解答专家' },
  { id: '3', name: '销售助理', description: '产品推荐和销售支持' }
])

// 快速操作按钮
const quickActions = computed(() => {
  switch (currentMode.value) {
    case 'free':
      return [
        { text: '你好，请介绍一下自己' },
        { text: '帮我写一份工作总结' },
        { text: '推荐一些学习资源' }
      ]
    case 'rag':
      return [
        { text: '查询产品功能介绍' },
        { text: '搜索技术文档' },
        { text: '查找常见问题解答' }
      ]

    case 'agent':
      return [
        { text: '杭州和北京现在的天气如何？' },
        { text: '帮我计算 25 * 34 + 67' },
        { text: '搜索最新的AI技术发展' }
      ]
    default:
      return []
  }
})



// 智能体对话相关数据 - 从当前消息的agent_data获取
const currentAgentData = computed(() => {
  const lastMessage = messages.value[messages.value.length - 1]
  if (lastMessage && lastMessage.role === 'assistant' && lastMessage.agent_data) {
    return lastMessage.agent_data
  }
  return {
    status: 'idle',
    steps: [],
    current_tool: null
  }
})

// 获取智能体状态类型
const getAgentStatusType = (status: string) => {
  switch (status) {
    case 'thinking': return 'warning'
    case 'tool_calling': return 'primary'
    case 'responding': return 'success'
    default: return 'info'
  }
}

// 获取智能体状态文本
const getAgentStatusText = (status: string) => {
  switch (status) {
    case 'thinking': return '思考中'
    case 'tool_calling': return '工具调用中'
    case 'responding': return '回复中'
    default: return '空闲'
  }
}

// 获取步骤类型文本
const getStepTypeText = (type) => {
  switch (type) {
    case 'thinking': return '🤔 思考'
    case 'tool_end': return '✅ 工具完成'
    case 'response': return '💬 回复'
    default: return type
  }
}

// 格式化时间
const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// 检查步骤中是否包含response类型
const hasResponseStep = (steps: any[]) => {
  return steps && steps.some(step => step.type === 'response')
}

// 获取最后一个response类型的步骤
const getLastResponseStep = (steps: any[]) => {
  if (!steps) return null
  // 从后往前查找最后一个response类型的步骤
  for (let i = steps.length - 1; i >= 0; i--) {
    if (steps[i].type === 'response') {
      return steps[i]
    }
  }
  return null
}

// 获取所有步骤列表，按时间顺序显示
const getUniqueSteps = (steps: any[]) => {
  if (!steps) return []
  
  // 直接返回所有步骤，按时间顺序排序
  return steps.sort((a, b) => {
    const timeA = new Date(a.timestamp || 0).getTime()
    const timeB = new Date(b.timestamp || 0).getTime()
    return timeA - timeB
  })
}

const messages = computed(() => chatStore.messages)
const knowledgeBases = computed(() => knowledgeStore.knowledgeBases)

onMounted(async () => {
  await Promise.all([
    chatStore.loadConversations(),
    knowledgeStore.loadKnowledgeBases()
  ])
})

// 监听消息变化，自动滚动到底部
watch(messages, () => {
  nextTick(() => {
    scrollToBottom()
  })
}, { deep: true })

// 切换对话模式
const switchMode = (mode: string) => {
  currentMode.value = mode
  
  // 清空当前配置
  if (mode !== 'rag') {
    selectedKnowledgeBase.value = ''
  }
  if (mode !== 'agent') {
    selectedAgent.value = ''
  }
  
  // 强制触发重新渲染
  nextTick(() => {
    // 确保DOM更新
  })
  
  ElMessage.success(`已切换到${chatModes.find(m => m.key === mode)?.label}模式`)
}

const createNewConversation = async () => {
  try {
    const newConversation = await chatStore.createConversation({
      title: '新对话',
      model_name: 'doubao-lite-4k',
      temperature: '0.7',
      max_tokens: 2048
    })
    
    if (newConversation) {
      chatStore.clearMessages()
      ElMessage.success('新对话已创建')
    }
  } catch (error) {
    ElMessage.error('创建对话失败')
  }
}

const sendMessage = async () => {
  if (!inputMessage.value.trim() || isLoading.value) {
    return
  }
  
  const messageContent = inputMessage.value.trim()
  inputMessage.value = ''
  isLoading.value = true
  
  try {
    let conversationId = chatStore.currentConversation?.id
    
    // 如果没有当前对话，创建新对话
    if (!conversationId) {
      const newConversation = await chatStore.createConversation({
        title: messageContent.length > 20 ? messageContent.substring(0, 20) + '...' : messageContent,
        model_name: 'doubao-lite-4k',
        temperature: '0.7',
        max_tokens: 2048
      })
      
      if (!newConversation) {
        throw new Error('创建对话失败')
      }
      
      conversationId = newConversation.id
    }
    
    // 根据当前模式构建消息数据
    const messageData: any = {
      message: messageContent,
      conversation_id: conversationId
    }
    console.log('currentMode.value='+currentMode.value)
    // 如果是智能体模式，添加use_agent参数
    if (currentMode.value === 'agent') {
      messageData.use_langgraph = true
    }
    
    // 如果是RAG模式，添加知识库参数
    if (currentMode.value === 'rag' && selectedKnowledgeBase.value) {
      messageData.use_knowledge_base = true
      messageData.knowledge_base_id = selectedKnowledgeBase.value
    }
    
    // 发送消息
    await chatStore.sendMessageStream(messageData)
    
  } catch (error) {
    console.error('发送消息失败:', error)
    ElMessage.error('发送消息失败，请重试')
  } finally {
    isLoading.value = false
  }
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const toggleHistoryPanel = async () => {
  showHistoryPanel.value = !showHistoryPanel.value
  
  // 当打开历史面板时，加载对话列表
  if (showHistoryPanel.value) {
    await chatStore.loadConversations()
  }
}

const selectConversation = async (conversation: any) => {
  try {
    // 设置当前对话并加载消息
    await chatStore.setCurrentConversation(conversation.id)
    await chatStore.loadMessages(conversation.id, true)
    console.log("conversation::", conversation.id)
    showHistoryPanel.value = false
    ElMessage.success(`已切换到对话: ${conversation.title}`)
  } catch (error) {
    console.error('切换对话失败:', error)
    ElMessage.error('切换对话失败')
  }
}

const handleSearch = (query: string) => {
  chatStore.setSearchQuery(query)
}

const formatConversationTime = (timeStr: string) => {
  const time = new Date(timeStr)
  const now = new Date()
  const diff = now.getTime() - time.getTime()
  
  if (diff < 60000) {
    return '刚刚'
  } else if (diff < 3600000) {
    return `${Math.floor(diff / 60000)}分钟前`
  } else if (diff < 86400000) {
    return `${Math.floor(diff / 3600000)}小时前`
  } else {
    return `${Math.floor(diff / 86400000)}天前`
  }
}
</script>

<style scoped>
.chat-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #0f172a;
  color: #e2e8f0;
  flex: 1;
  min-height: 0;
}

/* 模式选择器样式 */
.mode-selector {
  background: rgba(30, 41, 59, 0.7);
  border-bottom: 1px solid #334155;
  padding: 12px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

.mode-tabs {
  display: flex;
  gap: 8px;
}

.mode-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 20px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid #475569;
  background: #1e293b;
  color: #cbd5e1;
  font-size: 14px;
  font-weight: 500;
  position: relative;
}

.mode-tab:hover {
  background: rgba(99, 102, 241, 0.1);
  border-color: #6366f1;
  color: #e2e8f0;
}

.mode-tab.active {
  background: rgba(99, 102, 241, 0.2);
  border-color: #6366f1;
  color: #e2e8f0;
}

.mode-tab.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  width: 100%;
  height: 3px;
  background: #6366f1;
  border-radius: 3px 3px 0 0;
}

.mode-tab.history-tab {
  border: 1px solid #475569;
}

.mode-tab.history-tab.active {
  background: rgba(99, 102, 241, 0.1);
  color: #e2e8f0;
  border-color: #6366f1;
}

.mode-config {
  display: flex;
  align-items: center;
  gap: 12px;
}

.config-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 主要内容区域 */
.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
  width: 100%;
  height: 100%;
}

/* 左侧对话区域 */
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #1e293b;
  margin: 0;
  width: 100%;
  min-width: 0;
  height: 100%;
}

/* 智能体模式下为右侧面板留出空间 */
.chat-area.with-agent-panel {
  width: calc(100% - 400px);
}

/* 消息容器 */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 25px 30px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  background: #1e293b;
}

/* 欢迎消息样式 */
.welcome-message {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  text-align: center;
}

.welcome-content {
  max-width: 600px;
  padding: 40px;
}

.welcome-content h3 {
  margin: 0 0 12px 0;
  color: #e2e8f0;
  font-size: 24px;
  font-weight: 600;
}

.welcome-content p {
  margin: 0 0 32px 0;
  color: #94a3b8;
  font-size: 16px;
  line-height: 1.6;
}

.quick-actions {
  text-align: left;
}

.quick-action-title {
  margin-bottom: 16px;
  color: #e2e8f0;
  font-size: 16px;
  font-weight: 600;
}

.quick-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
}

/* 消息样式 */
.message-item {
  display: flex;
  margin-bottom: 16px;
}

.message {
  display: flex;
  gap: 12px;
  max-width: 80%;
  align-items: flex-start;
}

.message.user {
  margin-left: auto;
  flex-direction: row-reverse;
}

.message.assistant {
  margin-right: auto;
}

.message-avatar {
  flex-shrink: 0;
}

.message-content {
  flex: 1;
  min-width: 0;
}

.message-text {
  background: #334155;
  padding: 15px 20px;
  border-radius: 12px;
  color: #e2e8f0;
  line-height: 1.5;
  word-wrap: break-word;
  border-top-left-radius: 5px;
}

/* Markdown样式 */
.message-text h1,
.message-text h2,
.message-text h3,
.message-text h4,
.message-text h5,
.message-text h6 {
  margin: 16px 0 8px 0;
  font-weight: 600;
  line-height: 1.4;
}

.message-text h1 { font-size: 1.5em; }
.message-text h2 { font-size: 1.3em; }
.message-text h3 { font-size: 1.1em; }

.message-text p {
  margin: 8px 0;
}

.message-text ul,
.message-text ol {
  margin: 8px 0;
  padding-left: 20px;
}

.message-text li {
  margin: 4px 0;
}

.message-text pre {
  background: #0f172a;
  border: 1px solid #475569;
  border-radius: 6px;
  padding: 12px;
  margin: 12px 0;
  overflow-x: auto;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.4;
  color: #e2e8f0;
}

.message-text code {
  background: #0f172a;
  border: 1px solid #475569;
  border-radius: 3px;
  padding: 2px 4px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 0.9em;
  color: #e2e8f0;
}

.message-text pre code {
  background: none;
  border: none;
  padding: 0;
}

.message-text blockquote {
  border-left: 4px solid #dfe2e5;
  padding-left: 16px;
  margin: 12px 0;
  color: #6a737d;
  font-style: italic;
}

.message-text table {
  border-collapse: collapse;
  margin: 12px 0;
  width: 100%;
}

.message-text th,
.message-text td {
  border: 1px solid #dfe2e5;
  padding: 8px 12px;
  text-align: left;
}

.message-text th {
  background: #f6f8fa;
  font-weight: 600;
}

.message-text a {
  color: #0366d6;
  text-decoration: none;
}

.message-text a:hover {
  text-decoration: underline;
}

.message.user .message-text {
  background: #6366f1;
  color: white;
  border-top-right-radius: 5px;
  border-top-left-radius: 12px;
}

.message-time {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 8px;
  text-align: right;
  opacity: 0.7;
}

.message.user .message-time {
  text-align: left;
}

/* 消息状态显示 */
.message-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #e6f7ff;
  border: 1px solid #91d5ff;
  border-radius: 8px;
  color: #1890ff;
  font-size: 14px;
  margin-bottom: 8px;
}

.status-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 打字指示器 */
.typing-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 15px 20px;
  background: #334155;
  border-radius: 12px;
  border-top-left-radius: 5px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #94a3b8;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) {
  animation-delay: -0.32s;
}

.typing-indicator span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes typing {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

/* 智能体状态显示样式 */
.agent-status-simple {
  margin-bottom: 8px;
}

.agent-current-status {
  display: flex;
  align-items: center;
}

.current-step-display {
  display: flex;
  align-items: center;
}

.step-status {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 12px;
  font-size: 12px;
  color: #6366f1;
}

.step-status .type-icon {
  font-size: 14px;
}

.step-status .status-text {
  font-weight: 500;
}

.agent-status-inline {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
  padding: 8px 0;
}

.agent-status-tag {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
}

.agent-status-tag .el-icon {
  font-size: 12px;
}

.current-tool {
  font-size: 12px;
  color: #94a3b8;
  background: rgba(148, 163, 184, 0.1);
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid rgba(148, 163, 184, 0.2);
}



/* 输入区域样式 */
.input-area {
  border-top: 1px solid #334155;
  padding: 20px 30px;
  background: rgba(30, 41, 59, 0.7);
  flex-shrink: 0;
}

.input-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.input-tips {
  font-size: 12px;
  color: #94a3b8;
}

/* 自定义按钮样式 */
:deep(.el-button--primary) {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border: none;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
}

:deep(.el-button--primary:hover) {
  background: linear-gradient(135deg, #5855eb 0%, #7c3aed 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
}

:deep(.el-button--primary:active) {
  transform: translateY(0);
  box-shadow: 0 2px 6px rgba(99, 102, 241, 0.3);
}

:deep(.el-button--primary.is-loading) {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
}

/* 新对话按钮特殊样式 */
.chat-header :deep(.el-button--primary) {
  background: rgba(99, 102, 241, 0.1);
  color: #6366f1;
  border: 1px solid rgba(99, 102, 241, 0.3);
  font-size: 13px;
  padding: 6px 12px;
}

.chat-header :deep(.el-button--primary:hover) {
  background: rgba(99, 102, 241, 0.2);
  border-color: #6366f1;
  transform: none;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.2);
}

/* 知识库选择器样式 */
.mode-config :deep(.el-select) {
  --el-select-border-color-hover: #6366f1;
  --el-select-input-focus-border-color: #6366f1;
}

.mode-config :deep(.el-select .el-input__wrapper) {
  background-color: #1e293b !important;
  border: 1px solid #475569 !important;
  border-radius: 8px !important;
  box-shadow: none !important;
  transition: all 0.3s ease;
}

.mode-config :deep(.el-select .el-input__wrapper:hover) {
  border-color: #6366f1 !important;
  box-shadow: 0 0 0 1px rgba(99, 102, 241, 0.2) !important;
}

.mode-config :deep(.el-select .el-input__wrapper.is-focus) {
  border-color: #6366f1 !important;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2) !important;
}

.mode-config :deep(.el-select .el-input__inner) {
  color: #e2e8f0 !important;
  background-color: transparent !important;
}

.mode-config :deep(.el-select .el-input__inner::placeholder) {
  color: #94a3b8 !important;
}

.mode-config :deep(.el-select .el-select__caret) {
  color: #94a3b8 !important;
}

.mode-config :deep(.el-select .el-select__caret:hover) {
  color: #6366f1 !important;
}

.mode-config :deep(.el-select .el-select__suffix) {
  color: #94a3b8 !important;
}

.mode-config :deep(.el-select .el-select__suffix:hover) {
  color: #6366f1 !important;
}

/* 下拉菜单样式 */
:deep(.el-select-dropdown) {
  background-color: #1e293b !important;
  border: 1px solid #475569 !important;
  border-radius: 8px !important;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3) !important;
}

:deep(.el-select-dropdown .el-select-dropdown__item) {
  color: #e2e8f0 !important;
  background-color: transparent !important;
  transition: all 0.2s ease;
}

:deep(.el-select-dropdown .el-select-dropdown__item:hover) {
  background-color: rgba(99, 102, 241, 0.1) !important;
  color: #e2e8f0 !important;
}

:deep(.el-select-dropdown .el-select-dropdown__item.selected) {
  background-color: rgba(99, 102, 241, 0.2) !important;
  color: #6366f1 !important;
  font-weight: 500;
}

:deep(.el-select-dropdown .el-popper__arrow::before) {
  background-color: #1e293b !important;
  border: 1px solid #475569 !important;
}

/* 全局 Element Plus 选择器样式覆盖 */
:deep(.el-popper.is-light .el-popper__arrow::before) {
  background-color: #1e293b !important;
  border: 1px solid #475569 !important;
}

/* 快速开始按钮特殊样式优化 */
.quick-buttons :deep(.el-button--primary.is-plain) {
  background: rgba(99, 102, 241, 0.08) !important;
  border: 1px solid rgba(99, 102, 241, 0.25) !important;
  color: #8b5cf6 !important;
  border-radius: 20px !important;
  padding: 8px 16px !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  box-shadow: 0 1px 3px rgba(99, 102, 241, 0.1) !important;
  backdrop-filter: blur(8px) !important;
}

.quick-buttons :deep(.el-button--primary.is-plain:hover) {
  background: rgba(99, 102, 241, 0.15) !important;
  border-color: rgba(139, 92, 246, 0.4) !important;
  color: #a855f7 !important;
  transform: translateY(-2px) scale(1.02) !important;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.25), 0 2px 6px rgba(139, 92, 246, 0.15) !important;
}

.quick-buttons :deep(.el-button--primary.is-plain:active) {
  transform: translateY(-1px) scale(1.01) !important;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.2) !important;
}

.quick-buttons :deep(.el-button--primary.is-plain:focus) {
  outline: none !important;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.12) !important;
}

/* 快速按钮容器优化 */
.quick-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
  margin-top: 8px;
}

/* 快速按钮动画效果 */
.quick-buttons :deep(.el-button--primary.is-plain) {
  position: relative;
  overflow: hidden;
}

.quick-buttons :deep(.el-button--primary.is-plain::before) {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
  transition: left 0.6s ease;
}

.quick-buttons :deep(.el-button--primary.is-plain:hover::before) {
  left: 100%;
}

:deep(.el-popper.is-light) {
  background-color: #1e293b !important;
  border: 1px solid #475569 !important;
}

/* 历史对话面板样式 */
.history-panel {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding-top: 10vh;
  z-index: 1000;
}

.history-content {
  background: #1e293b;
  border-radius: 16px;
  width: 500px;
  max-height: 70vh;
  overflow: hidden;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
  border: 1px solid #334155;
}

.history-header {
  padding: 20px;
  border-bottom: 1px solid #334155;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.history-header h3 {
  margin: 0;
  font-size: 18px;
  color: #e2e8f0;
  font-weight: 600;
}

.history-list {
  max-height: 50vh;
  overflow-y: auto;
  padding: 8px 0;
}

.history-item {
  padding: 12px 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  border-bottom: 1px solid #334155;
}

.history-item:hover {
  background: rgba(99, 102, 241, 0.1);
}

.history-item:last-child {
  border-bottom: none;
}

.history-item.active {
  background: rgba(99, 102, 241, 0.2);
}

.conversation-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.conversation-title {
  font-size: 14px;
  color: #e2e8f0;
  font-weight: 500;
}

.conversation-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #94a3b8;
}

.conversation-time {
  color: #6366f1;
}

.conversation-count {
  color: #67c23a;
}



.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 右侧智能体思考流程面板样式 */
.agent-panel {
  width: 400px;
  background: #1e293b;
  border-left: 1px solid #334155;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.agent-header {
  padding: 16px;
  border-bottom: 1px solid #334155;
  background: #0f172a;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.agent-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #e2e8f0;
}

.agent-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.thinking-steps {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.thinking-step {
  background: #334155;
  border: 1px solid #475569;
  border-radius: 12px;
  padding: 16px;
  transition: all 0.3s ease;
  position: relative;
}

.thinking-step:hover {
  background: #3f4a5f;
  border-color: #64748b;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.thinking-step.step-thinking {
  border-left: 4px solid #3b82f6;
}

.thinking-step.step-tool_end {
  border-left: 4px solid #10b981;
}

.thinking-step.step-response {
  border-left: 4px solid #8b5cf6;
}

.step-header {
  margin-bottom: 8px;
}

.step-type-info {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: #475569;
  border-radius: 6px;
}

.step-type-info .type-icon {
  font-size: 16px;
}

.step-type-info .type-name {
  font-weight: 600;
  color: #e2e8f0;
  font-size: 13px;
}

.step-type-info .tool-info {
  color: #fbbf24;
  font-weight: 500;
  font-size: 13px;
}

.step-content {
  color: #e2e8f0;
  background: #1e293b;
  padding: 10px;
  border-radius: 6px;
  border-left: 3px solid #6366f1;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.tool-output {
  margin-top: 8px;
}

.output-label {
  font-size: 12px;
  font-weight: 600;
  color: #fbbf24;
  margin-bottom: 4px;
}

.output-content {
  color: #6ee7b7;
  background: #0f172a;
  padding: 8px 10px;
  border-radius: 6px;
  border-left: 3px solid #10b981;
  font-size: 12px;
  line-height: 1.4;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: 'Courier New', monospace;
  max-height: 200px;
  overflow-y: auto;
}

.step-timestamp {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #475569;
  font-size: 11px;
  color: #94a3b8;
}

.agent-empty {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 200px;
  color: #6b7280;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.empty-text {
  font-size: 14px;
}


</style>