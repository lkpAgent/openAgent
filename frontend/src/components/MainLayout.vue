<template>
  <div class="main-layout">
    <div class="layout-container">
      <!-- 左侧导航栏 -->
      <div class="sidebar">
        <!-- 主导航 -->
        <div class="main-nav">
          <div class="nav-header">
            <h1 class="app-title">智能对话平台</h1>
            <p class="app-subtitle">多模态对话与工作流平台</p>
          </div>
          
          <nav class="nav-menu">
            <div 
              v-for="item in navItems" 
              :key="item.key"
              :class="['nav-item', { active: activeModule === item.key }]"
              @click="setActiveModule(item.key)"
            >
              <el-icon class="nav-icon">
                <component :is="item.icon" />
              </el-icon>
              <span class="nav-label">{{ item.label }}</span>
            </div>
          </nav>
        </div>
        
        <!-- 历史对话列表 -->
        <div class="history-section">
          <div class="history-header">
            <h3>历史对话</h3>
            <el-button size="small" text @click="toggleHistoryPanel">
              <el-icon><Plus /></el-icon>
            </el-button>
          </div>
          
          <!-- 搜索框 -->
          <div class="history-search">
            <el-input
              v-model="historySearchQuery"
              placeholder="搜索对话..."
              size="small"
              clearable
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>
          
          <!-- 对话列表 -->
          <div class="history-list">
            <div 
              v-for="conversation in filteredConversations" 
              :key="conversation.id"
              :class="['history-item', { active: selectedConversation?.id === conversation.id }]"
              @click="selectConversation(conversation)"
            >
              <div class="conversation-info">
                <div class="conversation-title">{{ conversation.title }}</div>
                <div class="conversation-time">{{ formatConversationTime(conversation.updated_at) }}</div>
              </div>
              <div class="conversation-actions">
                <el-button size="small" text @click.stop="editConversationTitle(conversation)">
                  <el-icon><Edit /></el-icon>
                </el-button>
                <el-button size="small" text type="danger" @click.stop="deleteConversationConfirm(conversation)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 主内容区域 -->
      <div class="main-area">
        <!-- 中间内容区域 -->
        <div class="main-content">
          <!-- 路由视图 -->
          <router-view />
        </div>
        
        <!-- 右侧智能体工作流面板 -->
        <div v-if="showWorkflowPanel" class="workflow-panel">
          <AgentWorkflow 
            :agent-name="currentAgentName" 
            :is-active="activeModule === 'chat' && chatMode === 'agent'"
            ref="agentWorkflowRef"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ChatDotRound,
  Collection,
  Connection,
  User,
  Plus,
  Search,
  Edit,
  Delete
} from '@element-plus/icons-vue'
import AgentWorkflow from './AgentWorkflow.vue'

// 路由
const router = useRouter()
const route = useRoute()

// 响应式数据
const activeModule = ref('chat')
const chatMode = ref('free')
const currentAgentName = ref('客服小助手')
const selectedConversation = ref(null)
const historySearchQuery = ref('')
const agentWorkflowRef = ref()

// 导航项配置
const navItems = [
  {
    key: 'chat',
    label: '智能问答',
    icon: 'ChatDotRound',
    route: '/chat'
  },
  {
    key: 'knowledge',
    label: '知识库管理',
    icon: 'Collection',
    route: '/knowledge'
  },
  {
    key: 'workflow',
    label: '工作流编排',
    icon: 'Connection',
    route: '/workflow'
  },
  {
    key: 'agent',
    label: '智能体管理',
    icon: 'User',
    route: '/agent'
  }
]

// 模拟历史对话数据
const conversations = ref([
  {
    id: '1',
    title: '产品咨询对话',
    updated_at: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
    message_count: 15
  },
  {
    id: '2',
    title: '技术支持对话',
    updated_at: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
    message_count: 8
  },
  {
    id: '3',
    title: '售后服务咨询',
    updated_at: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
    message_count: 12
  }
])

// 计算属性
const showWorkflowPanel = computed(() => {
  return activeModule.value === 'chat' && chatMode.value === 'agent'
})

const filteredConversations = computed(() => {
  if (!historySearchQuery.value.trim()) {
    return conversations.value
  }
  const query = historySearchQuery.value.toLowerCase()
  return conversations.value.filter(conv => 
    conv.title.toLowerCase().includes(query)
  )
})

// 方法
const setActiveModule = (moduleKey: string) => {
  activeModule.value = moduleKey
  const navItem = navItems.find(item => item.key === moduleKey)
  if (navItem && navItem.route) {
    router.push(navItem.route)
  }
}

const toggleHistoryPanel = () => {
  ElMessage.info('新建对话功能开发中...')
}

const selectConversation = (conversation: any) => {
  selectedConversation.value = conversation
  ElMessage.success(`已选择对话: ${conversation.title}`)
}

const editConversationTitle = (conversation: any) => {
  ElMessage.info('编辑对话标题功能开发中...')
}

const deleteConversationConfirm = (conversation: any) => {
  ElMessage.info('删除对话功能开发中...')
}

const formatConversationTime = (timestamp: string) => {
  const now = new Date()
  const time = new Date(timestamp)
  const diffMs = now.getTime() - time.getTime()
  const diffMins = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  
  if (diffMins < 60) {
    return `${diffMins}分钟前`
  } else if (diffHours < 24) {
    return `${diffHours}小时前`
  } else if (diffDays < 7) {
    return `${diffDays}天前`
  } else {
    return time.toLocaleDateString('zh-CN')
  }
}

// 监听路由变化
const updateActiveModuleFromRoute = () => {
  const path = route.path
  if (path.includes('/chat')) {
    activeModule.value = 'chat'
  } else if (path.includes('/knowledge')) {
    activeModule.value = 'knowledge'
  } else if (path.includes('/workflow')) {
    activeModule.value = 'workflow'
  } else if (path.includes('/agent')) {
    activeModule.value = 'agent'
  }
}

onMounted(() => {
  updateActiveModuleFromRoute()
})
</script>

<style scoped>
.main-layout {
  height: 100vh;
  background: #f5f7fa;
  overflow: hidden;
}

.layout-container {
  height: 100%;
  display: flex;
}

/* 左侧边栏 */
.sidebar {
  width: 280px;
  background: #2c3e50;
  color: white;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 主导航 */
.main-nav {
  flex-shrink: 0;
}

.nav-header {
  padding: 24px 20px;
  border-bottom: 1px solid #34495e;
  text-align: center;
}

.app-title {
  margin: 0 0 8px 0;
  font-size: 20px;
  font-weight: 600;
  color: #ecf0f1;
}

.app-subtitle {
  margin: 0;
  font-size: 12px;
  color: #95a5a6;
  opacity: 0.8;
}

.nav-menu {
  padding: 16px 0;
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
  background: #34495e;
  border-left-color: #3498db;
}

.nav-item.active {
  background: #34495e;
  border-left-color: #3498db;
  color: #3498db;
}

.nav-icon {
  font-size: 18px;
  margin-right: 12px;
}

.nav-label {
  font-size: 14px;
  font-weight: 500;
}

/* 历史对话区域 */
.history-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-top: 1px solid #34495e;
  overflow: hidden;
}

.history-header {
  padding: 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #34495e;
}

.history-header h3 {
  margin: 0;
  font-size: 14px;
  color: #ecf0f1;
}

.history-search {
  padding: 12px 16px;
  border-bottom: 1px solid #34495e;
}

.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.history-item {
  padding: 12px 16px;
  margin: 4px 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.history-item:hover {
  background: #34495e;
}

.history-item.active {
  background: #3498db;
}

.conversation-info {
  flex: 1;
  min-width: 0;
}

.conversation-title {
  font-size: 13px;
  color: #ecf0f1;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.conversation-time {
  font-size: 11px;
  color: #95a5a6;
}

.conversation-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.history-item:hover .conversation-actions {
  opacity: 1;
}

/* 主内容区域 */
.main-area {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.main-content {
  flex: 1;
  background: white;
  overflow: hidden;
}

/* 右侧工作流面板 */
.workflow-panel {
  width: 350px;
  border-left: 1px solid #e4e7ed;
  background: #fafbfc;
}

/* 滚动条样式 */
.history-list::-webkit-scrollbar {
  width: 4px;
}

.history-list::-webkit-scrollbar-track {
  background: #2c3e50;
}

.history-list::-webkit-scrollbar-thumb {
  background: #34495e;
  border-radius: 2px;
}

.history-list::-webkit-scrollbar-thumb:hover {
  background: #4a5f7a;
}
</style>