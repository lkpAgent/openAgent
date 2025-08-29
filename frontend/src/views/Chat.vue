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
        
        <!-- 智能体模式配置 -->
        <div v-if="currentMode === 'agent'" class="config-item">
          <el-select 
            v-model="selectedAgent" 
            placeholder="选择智能体"
            size="small"
            style="width: 200px;"
          >
            <el-option
              v-for="agent in availableAgents"
              :key="agent.id"
              :label="agent.name"
              :value="agent.id"
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

    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 左侧对话区域 -->
      <div class="chat-area">
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
                <div class="message-text">{{ message.content }}</div>
                <div class="message-time">{{ formatTime(message.created_at) }}</div>
              </div>
            </div>
          </div>
          
          <!-- 加载中状态 -->
          <div v-if="isLoading" class="message-item">
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
      
      <!-- 右侧智能体工作流展示区域 -->
      <div class="workflow-panel" v-if="currentMode === 'agent'">
        <div class="workflow-header">
          <div class="workflow-title">
            <el-icon><Setting /></el-icon>
            <span>智能体工作流</span>
          </div>
          <div class="workflow-status">
            <el-tag :type="workflowStatus === 'running' ? 'warning' : workflowStatus === 'completed' ? 'success' : 'info'" size="small">
              {{ workflowStatusText }}
            </el-tag>
          </div>
        </div>
        
        <div class="workflow-content">
          <div class="workflow-steps">
            <div class="current-workflow" v-if="currentWorkflow">
              <h4>当前工作流执行过程</h4>
              <div class="workflow-step" 
                   v-for="(step, index) in workflowSteps" 
                   :key="index"
                   :class="{ 
                     'active': step.status === 'running',
                     'completed': step.status === 'completed',
                     'pending': step.status === 'pending'
                   }">
                <div class="step-icon">
                  <el-icon v-if="step.status === 'completed'"><Check /></el-icon>
                  <el-icon v-else-if="step.status === 'running'" class="rotating"><Loading /></el-icon>
                  <el-icon v-else><Clock /></el-icon>
                </div>
                <div class="step-content">
                  <div class="step-title">{{ step.title }}</div>
                  <div class="step-description">{{ step.description }}</div>
                  <div class="step-status" v-if="step.status === 'completed'">
                    <el-tag type="success" size="small">已完成</el-tag>
                  </div>
                  <div class="step-status" v-else-if="step.status === 'running'">
                    <el-tag type="warning" size="small">进行中</el-tag>
                  </div>
                  <div class="step-status" v-else>
                    <el-tag type="info" size="small">等待中</el-tag>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="workflow-placeholder" v-else>
              <el-empty description="暂无工作流执行">
                <template #image>
                  <el-icon size="60" color="#ccc"><Setting /></el-icon>
                </template>
              </el-empty>
            </div>
          </div>
        </div>
      </div>
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
  User
} from '@element-plus/icons-vue'
import { useChatStore } from '@/stores/chat'
import { useKnowledgeStore } from '@/stores/knowledge'
import { formatTime } from '@/utils'

const router = useRouter()
const chatStore = useChatStore()
const knowledgeStore = useKnowledgeStore()

// 对话模式相关
const currentMode = ref('free')
const selectedKnowledgeBase = ref('')
const selectedAgent = ref('')

// 基础状态
const inputMessage = ref('')
const isLoading = ref(false)
const messagesContainer = ref<HTMLElement>()

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
    description: '任务自动化',
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
        { text: '开始工作流程' },
        { text: '查看任务状态' },
        { text: '生成报告' }
      ]
    default:
      return []
  }
})

// 工作流相关数据
const currentWorkflow = ref(null)
const workflowStatus = ref('idle') // idle, running, completed, error
const workflowStatusText = computed(() => {
  switch (workflowStatus.value) {
    case 'running': return '执行中'
    case 'completed': return '已完成'
    case 'error': return '执行失败'
    default: return '待执行'
  }
})

const workflowSteps = ref([
  {
    title: '自然语言理解',
    description: '解析用户查询意图，识别实体和关键信息',
    status: 'completed'
  },
  {
    title: '知识检索',
    description: '从知识库中检索与推荐系统设计相关的文档',
    status: 'running'
  },
  {
    title: '智能体协作',
    description: '协调推荐系统专家、算法工程师和架构师智能体',
    status: 'pending'
  }
])

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
    
    // 发送消息
    await chatStore.sendMessageStream({
      message: messageContent,
      conversation_id: conversationId
    })
    
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
</script>

<style scoped>
.chat-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

/* 模式选择器样式 */
.mode-selector {
  background: white;
  border-bottom: 1px solid #e4e7ed;
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
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid #e4e7ed;
  background: #fafbfc;
  color: #606266;
  font-size: 14px;
}

.mode-tab:hover {
  background: #ecf5ff;
  border-color: #b3d8ff;
  color: #409eff;
}

.mode-tab.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-color: #667eea;
  color: white;
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
}

/* 左侧对话区域 */
.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  margin: 0;
}

/* 消息容器 */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
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
  color: #303133;
  font-size: 24px;
  font-weight: 600;
}

.welcome-content p {
  margin: 0 0 32px 0;
  color: #606266;
  font-size: 16px;
  line-height: 1.6;
}

.quick-actions {
  text-align: left;
}

.quick-action-title {
  margin-bottom: 16px;
  color: #303133;
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
  background: #f0f2f5;
  padding: 12px 16px;
  border-radius: 12px;
  color: #303133;
  line-height: 1.6;
  word-wrap: break-word;
}

.message.user .message-text {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.message-time {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  text-align: right;
}

.message.user .message-time {
  text-align: left;
}

/* 打字指示器 */
.typing-indicator {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 12px 16px;
  background: #f0f2f5;
  border-radius: 12px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #909399;
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

/* 输入区域样式 */
.input-area {
  border-top: 1px solid #e4e7ed;
  padding: 16px 20px;
  background: white;
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
  color: #909399;
}

/* 右侧工作流面板样式 */
.workflow-panel {
  width: 350px;
  background: white;
  border-left: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.workflow-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e4e7ed;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.workflow-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
}

.workflow-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.current-workflow h4 {
  margin: 0 0 16px 0;
  color: #303133;
  font-size: 14px;
  font-weight: 600;
}

.workflow-step {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  margin-bottom: 12px;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  background: #fafbfc;
  transition: all 0.3s ease;
}

.workflow-step.active {
  background: #fff7e6;
  border-color: #ffc53d;
  box-shadow: 0 2px 8px rgba(255, 197, 61, 0.2);
}

.workflow-step.completed {
  background: #f6ffed;
  border-color: #b7eb8f;
}

.workflow-step.pending {
  background: #f0f2f5;
  border-color: #d9d9d9;
}

.step-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 2px;
}

.workflow-step.completed .step-icon {
  background: #52c41a;
  color: white;
}

.workflow-step.active .step-icon {
  background: #faad14;
  color: white;
}

.workflow-step.pending .step-icon {
  background: #d9d9d9;
  color: #8c8c8c;
}

.step-content {
  flex: 1;
  min-width: 0;
}

.step-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.step-description {
  font-size: 12px;
  color: #606266;
  line-height: 1.4;
  margin-bottom: 8px;
}

.step-status {
  display: flex;
  justify-content: flex-start;
}

.workflow-placeholder {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
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
</style>