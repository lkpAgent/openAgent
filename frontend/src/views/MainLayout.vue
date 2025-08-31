<template>
  <div class="main-layout">
    <!-- 左侧导航栏 -->
    <div class="sidebar">
      <!-- 顶部标题 -->
      <div class="sidebar-header">
        <h1 class="main-title">智能对话平台</h1>
        <p class="subtitle">多模态对话与工作流编排</p>
      </div>
      
      <!-- 主导航菜单 -->
      <div class="nav-menu">
        <div 
          class="nav-item"
          :class="{ active: activeModule === 'chat' }"
          @click="setActiveModule('chat')"
        >
          <el-icon class="nav-icon"><ChatDotRound /></el-icon>
          <span>对话中心</span>
        </div>
        
        <div 
          class="nav-item"
          :class="{ active: activeModule === 'knowledge' }"
          @click="setActiveModule('knowledge')"
        >
          <el-icon class="nav-icon"><FolderOpened /></el-icon>
          <span>知识库管理</span>
        </div>
        
        <div 
          class="nav-item"
          :class="{ active: activeModule === 'workflow' }"
          @click="setActiveModule('workflow')"
        >
          <el-icon class="nav-icon"><Connection /></el-icon>
          <span>工作流编排</span>
        </div>
        
        <div 
          class="nav-item"
          :class="{ active: activeModule === 'agent' }"
          @click="setActiveModule('agent')"
        >
          <el-icon class="nav-icon"><Robot /></el-icon>
          <span>智能体管理</span>
        </div>
      </div>
      
      <!-- 历史对话列表 -->
      <div class="history-section">
        <div class="history-header">
          <h3>历史对话</h3>
          <el-button size="small" text @click="createNewConversation">
            <el-icon><Plus /></el-icon>
          </el-button>
        </div>
        
        <div class="history-list">
          <div class="history-search">
            <el-input
              v-model="searchQuery"
              placeholder="搜索对话..."
              size="small"
              clearable
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>
          
          <div class="conversation-items">
            <div 
              v-for="conversation in filteredConversations" 
              :key="conversation.id"
              :class="['conversation-item', { active: currentConversation?.id === conversation.id }]"
              @click="selectConversation(conversation)"
            >
              <div class="conversation-title">{{ conversation.title }}</div>
              <div class="conversation-time">{{ formatConversationTime(conversation.updated_at) }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 中间内容区域 -->
    <div class="main-content">
      <!-- 模块内容区域 -->
      <div class="module-content">
        <!-- 智能问答模块使用router-view -->
        <div v-if="activeModule === 'chat'" style="flex: 1; display: flex; flex-direction: column; height: 100%;">
          <router-view />
        </div>
        
        <!-- 知识库管理模块 -->
        <div v-else-if="activeModule === 'knowledge'" style="flex: 1; display: flex; flex-direction: column; height: 100%; width: 100%;">
          <KnowledgeManagement />
        </div>
        
        <!-- 其他模块的占位内容 -->
        <div v-else class="module-placeholder">
          <div class="placeholder-content">
            <h2>{{ getModuleTitle(activeModule) }}</h2>
            <p>{{ getModuleDescription(activeModule) }}</p>
            <el-button type="primary" @click="handleModuleAction(activeModule)">
              开始使用
            </el-button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 右侧智能体工作流展示 -->
    <div v-if="activeModule === 'chat' && chatMode === 'agent'" class="workflow-panel">
      <div class="workflow-header">
        <h3>智能体工作流</h3>
        <el-icon><InfoFilled /></el-icon>
      </div>
      
      <div class="workflow-content">
        <!-- 工作流步骤 -->
        <div class="workflow-steps">
          <div class="step-item" v-for="(step, index) in workflowSteps" :key="index">
            <div class="step-number">{{ index + 1 }}</div>
            <div class="step-content">
              <div class="step-title">{{ step.title }}</div>
              <div class="step-status" :class="step.status">{{ step.statusText }}</div>
            </div>
          </div>
        </div>
        
        <!-- 相关知识库 -->
        <div class="related-knowledge">
          <h4>相关知识库</h4>
          <div class="knowledge-item" v-for="kb in relatedKnowledgeBases" :key="kb.id">
            <el-icon><Document /></el-icon>
            <span>{{ kb.name }}</span>
          </div>
        </div>
        
        <!-- 执行历史 -->
        <div class="execution-history">
          <h4>执行历史</h4>
          <div class="history-item" v-for="item in executionHistory" :key="item.id">
            <div class="history-time">{{ formatTime(item.timestamp) }}</div>
            <div class="history-action">{{ item.action }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ChatDotRound,
  FolderOpened,
  Connection,
  Robot,
  Plus,
  Search,
  User,
  InfoFilled,
  Document
} from '@element-plus/icons-vue'
import { useChatStore } from '@/stores/chat'
import { useKnowledgeStore } from '@/stores/knowledge'
import type { Conversation, Message } from '@/types/chat'
import type { KnowledgeBase } from '@/types/knowledge'
import KnowledgeManagement from '@/components/KnowledgeManagement.vue'
import WorkflowEditor from '@/components/WorkflowEditor.vue'
import AgentManagement from '@/components/AgentManagement.vue'

// Store
const chatStore = useChatStore()
const knowledgeStore = useKnowledgeStore()

// 响应式数据
const activeModule = ref('chat') // 当前激活的模块
const chatMode = ref('free') // 对话模式：free, rag, agent
const inputMessage = ref('')
const isLoading = ref(false)
const searchQuery = ref('')
const selectedKnowledgeBaseId = ref<string | null>(null)
const selectedAgentId = ref<string | null>(null)
const messagesContainer = ref<HTMLElement>()

// 计算属性
const messages = computed(() => chatStore.messages)
const conversations = computed(() => chatStore.conversations)
const currentConversation = computed(() => chatStore.currentConversation)
const knowledgeBases = computed(() => knowledgeStore.knowledgeBases)
const selectedKnowledgeBase = computed(() => 
  knowledgeBases.value.find(kb => kb.id === selectedKnowledgeBaseId.value)
)

// 模拟数据
const agents = ref([
  { id: '1', name: '数据分析师' },
  { id: '2', name: '代码助手' },
  { id: '3', name: '文档编写' }
])

const selectedAgent = computed(() => 
  agents.value.find(agent => agent.id === selectedAgentId.value)
)

const workflowSteps = ref([
  { title: '初始检索', status: 'completed', statusText: '已完成' },
  { title: '智能分析', status: 'running', statusText: '执行中' },
  { title: '结果生成', status: 'pending', statusText: '等待中' }
])

const relatedKnowledgeBases = ref([
  { id: '1', name: '技术文档库' },
  { id: '2', name: '产品手册' }
])

const executionHistory = ref([
  { id: '1', timestamp: new Date().toISOString(), action: '开始执行工作流' },
  { id: '2', timestamp: new Date().toISOString(), action: '检索相关文档' }
])

// 过滤对话
const filteredConversations = computed(() => {
  if (!searchQuery.value.trim()) {
    return conversations.value
  }
  const query = searchQuery.value.toLowerCase()
  return conversations.value.filter(conv => 
    conv.title.toLowerCase().includes(query)
  )
})

// 方法
const setActiveModule = (module: string) => {
  activeModule.value = module
}

const setChatMode = (mode: string) => {
  chatMode.value = mode
}

const createNewConversation = async () => {
  try {
    const newConversation = await chatStore.createConversation({
      title: '新对话',
      model_name: 'deepseek-chat',
      temperature: '0.7',
      max_tokens: 2048
    })
    
    if (newConversation) {
      chatStore.setCurrentConversation(newConversation.id.toString())
      ElMessage.success('新对话已创建')
    }
  } catch (error) {
    ElMessage.error('创建对话失败')
  }
}

const selectConversation = async (conversation: Conversation) => {
  if (currentConversation.value?.id === conversation.id) {
    return
  }
  
  try {
    await chatStore.setCurrentConversation(conversation.id.toString())
  } catch (error) {
    console.error('切换对话失败:', error)
    ElMessage.error('切换对话失败')
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
    let conversationId = currentConversation.value?.id
    
    // 如果没有当前对话，创建新对话
    if (!conversationId) {
      const newConversation = await chatStore.createConversation({
        title: messageContent.length > 20 ? messageContent.substring(0, 20) + '...' : messageContent,
        model_name: 'deepseek-chat',
        temperature: '0.7',
        max_tokens: 2048
      })
      
      if (newConversation) {
        conversationId = newConversation.id
        await chatStore.setCurrentConversation(conversationId.toString())
      } else {
        throw new Error('创建对话失败')
      }
    }
    
    // 根据对话模式发送消息
    const messageData: any = {
      message: messageContent,
      conversation_id: conversationId,
      stream: true
    }
    
    if (chatMode.value === 'rag' && selectedKnowledgeBaseId.value) {
      messageData.knowledge_base_id = selectedKnowledgeBaseId.value
    }
    
    if (chatMode.value === 'agent' && selectedAgentId.value) {
      messageData.agent_id = selectedAgentId.value
    }
    
    await chatStore.sendMessageStream(messageData, (chunk: string) => {
      nextTick(() => {
        scrollToBottom()
      })
    })
    
    nextTick(() => {
      scrollToBottom()
    })
  } catch (error) {
    console.error('发送消息失败:', error)
    ElMessage.error('发送消息失败')
  } finally {
    isLoading.value = false
  }
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const formatMessageContent = (content: string) => {
  if (!content) return ''
  return content.replace(/\n/g, '<br>')
}

const formatTime = (timestamp: string) => {
  if (!timestamp) return ''
  return new Date(timestamp).toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatConversationTime = (timestamp: string) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const now = new Date()
  const diffTime = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))
  
  if (diffDays === 0) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  } else if (diffDays === 1) {
    return '昨天'
  } else if (diffDays < 7) {
    return `${diffDays}天前`
  } else {
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  }
}

const exportConversation = () => {
  ElMessage.info('导出功能开发中')
}

// 生命周期
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
</script>

<style scoped>
.main-layout {
  display: flex;
  height: 100vh;
  background: #f5f7fa;
}

/* 左侧导航栏 */
.sidebar {
  width: 280px;
  background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  flex-direction: column;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
}

.sidebar-header {
  padding: 24px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.main-title {
  font-size: 20px;
  font-weight: 600;
  margin: 0 0 8px 0;
}

.subtitle {
  font-size: 14px;
  opacity: 0.8;
  margin: 0;
}

.nav-menu {
  padding: 20px 0;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  border-left: 3px solid transparent;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
}

.nav-item.active {
  background: rgba(255, 255, 255, 0.15);
  border-left-color: #fff;
}

.nav-icon {
  margin-right: 12px;
  font-size: 18px;
}

/* 历史对话区域 */
.history-section {
  flex: 1;
  padding: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.history-header h3 {
  margin: 0;
  font-size: 16px;
}

.history-list {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.history-search {
  margin-bottom: 12px;
}

.conversation-items {
  flex: 1;
  overflow-y: auto;
}

.conversation-item {
  padding: 12px;
  margin-bottom: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.conversation-item:hover {
  background: rgba(255, 255, 255, 0.2);
}

.conversation-item.active {
  background: rgba(255, 255, 255, 0.25);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.conversation-title {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conversation-time {
  font-size: 12px;
  opacity: 0.7;
}

/* 中间内容区域 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
}

.module-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
}

.chat-module {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-header {
  padding: 16px 24px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fafbfc;
}

.chat-tabs {
  display: flex;
  gap: 8px;
}

.chat-tab {
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 14px;
  color: #606266;
}

.chat-tab:hover {
  background: #e6f7ff;
  color: #409eff;
}

.chat-tab.active {
  background: #409eff;
  color: white;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.welcome-message {
  text-align: center;
  padding: 60px 20px;
  color: #606266;
}

.welcome-content h3 {
  margin-bottom: 16px;
  color: #303133;
}

.message-item {
  margin-bottom: 20px;
}

.message {
  display: flex;
  gap: 12px;
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
}

.ai-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.message-content {
  max-width: 70%;
}

.message-text {
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
}

.message.user .message-text {
  background: #409eff;
  color: white;
}

.message.assistant .message-text {
  background: #f5f7fa;
  color: #303133;
}

.message-time {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  text-align: center;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #409eff;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-10px);
  }
}

.input-area {
  padding: 20px;
  border-top: 1px solid #e4e7ed;
  background: #fafbfc;
}

.mode-config {
  margin-bottom: 12px;
}

.input-container {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.input-container .el-textarea {
  flex: 1;
}

/* 右侧工作流面板 */
.workflow-panel {
  width: 320px;
  background: white;
  border-left: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
}

.workflow-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fafbfc;
}

.workflow-header h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.workflow-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.workflow-steps {
  margin-bottom: 24px;
}

.step-item {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.step-number {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #409eff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  flex-shrink: 0;
}

.step-content {
  flex: 1;
}

.step-title {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 4px;
}

.step-status {
  font-size: 12px;
  color: #909399;
}

.step-status.completed {
  color: #67c23a;
}

.step-status.running {
  color: #409eff;
}

.related-knowledge,
.execution-history {
  margin-bottom: 24px;
}

.related-knowledge h4,
.execution-history h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #303133;
}

.knowledge-item,
.history-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  font-size: 13px;
  color: #606266;
}

.history-time {
  font-size: 12px;
  color: #909399;
}

.history-action {
  font-size: 13px;
  color: #606266;
}
</style>