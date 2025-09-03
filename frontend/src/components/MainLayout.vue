<template>
  <div class="main-layout">
    <div class="layout-container">
      <!-- 左侧导航栏 -->
      <div :class="['sidebar', { collapsed: isCollapsed }]">
        <!-- 主导航 -->
        <div class="main-nav">
          <div class="nav-header">
            <div class="logo-section">
              <h1 class="app-title">智能对话平台</h1>
            </div>
            <div v-if="!isCollapsed" class="user-actions">
            <span class="username">{{ userStore.user?.username }}</span>
            <a href="#" @click.prevent="logout" class="logout-link">
              <el-icon><SwitchButton /></el-icon>
              注销
            </a>
          </div>
          </div>
          
          <nav class="nav-menu">
            <!-- 上部分导航 -->
            <div class="nav-group">
              <div class="nav-group-header">
                <div v-if="!isCollapsed" class="nav-group-title">核心功能</div>
                <el-button 
                  class="collapse-btn" 
                  @click="toggleSidebar" 
                  text 
                  size="small"
                >
                  <el-icon><Expand v-if="isCollapsed" /><Fold v-else /></el-icon>
                </el-button>
              </div>
              <div 
                v-for="item in upperNavItems" 
                :key="item.key"
                :class="['nav-item', { active: activeModule === item.key }]"
                @click="setActiveModule(item.key)"
              >
                <el-icon class="nav-icon">
                  <component :is="item.icon" />
                </el-icon>
                <span v-if="!isCollapsed" class="nav-label">{{ item.label }}</span>
              </div>
            </div>
            
            <!-- 下部分导航 -->
            <div class="nav-group">
              <div class="nav-group-header">
                <div v-if="!isCollapsed" class="nav-group-title">管理功能</div>
              </div>
              <div 
                v-for="item in lowerNavItems" 
                :key="item.key"
                :class="['nav-item', { active: activeModule === item.key }]"
                @click="setActiveModule(item.key)"
              >
                <el-icon class="nav-icon">
                  <component :is="item.icon" />
                </el-icon>
                <span class="nav-label">{{ item.label }}</span>
              </div>
            </div>
          </nav>
        </div>
        
        <!-- 历史对话面板（浮动显示） -->
        <div v-if="showHistoryPanel" class="history-panel">
          <div class="history-header">
            <h3>{{ showArchivedConversations ? '已归档对话' : '历史对话' }}</h3>
            <div class="header-actions">
              <el-button size="small" text @click="toggleArchivedView">
                {{ showArchivedConversations ? '查看活跃' : '查看归档' }}
              </el-button>
              <el-button size="small" text @click="toggleHistoryPanel">
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
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
          
          <!-- 对话列表 -->
          <div class="history-list" v-loading="isLoading">
            <div 
              v-for="conversation in filteredConversations" 
              :key="conversation.id"
              :class="['history-item', { active: currentConversation?.id === conversation.id }]"
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
                <el-button 
                  v-if="!showArchivedConversations" 
                  size="small" 
                  text 
                  @click.stop="archiveConversation(conversation)"
                  title="归档对话"
                >
                  <el-icon><Connection /></el-icon>
                </el-button>
                <el-button 
                  v-else 
                  size="small" 
                  text 
                  @click.stop="unarchiveConversation(conversation)"
                  title="取消归档"
                >
                  <el-icon><SwitchButton /></el-icon>
                </el-button>
                <el-button size="small" text type="danger" @click.stop="deleteConversationConfirm(conversation)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
            
            <!-- 空状态 -->
            <div v-if="!isLoading && filteredConversations.length === 0" class="empty-state">
              <p>{{ showArchivedConversations ? '暂无归档对话' : '暂无对话记录' }}</p>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 主内容区域 -->
      <div class="main-area">
        <!-- 路由视图 -->
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ChatDotRound,
  Collection,
  Connection,
  User,
  Plus,
  Search,
  Edit,
  Delete,
  SwitchButton,
  DataAnalysis,
  EditPen,
  Shop,
  Setting,
  Close,
  Expand,
  Fold
} from '@element-plus/icons-vue'
import AgentWorkflow from './AgentWorkflow.vue'
import { useChatStore } from '@/stores/chat'
import { useUserStore } from '@/stores/user'

// 路由
const router = useRouter()
const route = useRoute()

// Stores
const chatStore = useChatStore()
const userStore = useUserStore()

// 响应式数据
const activeModule = ref('chat')
const chatMode = ref('free')
const currentAgentName = ref('客服小助手')
const agentWorkflowRef = ref()
const showHistoryPanel = ref(false)
const showArchivedConversations = ref(false)
const isCollapsed = ref(false)

// 上部分导航项配置
const upperNavItems = [
  {
    key: 'chat',
    label: '智能问答',
    icon: 'ChatDotRound',
    route: '/chat'
  },
  {
    key: 'smart-query',
    label: '智能问数',
    icon: 'DataAnalysis',
    route: '/smart-query'
  },
  {
    key: 'creation',
    label: '智能创作',
    icon: 'EditPen',
    route: '/creation'
  },
  {
    key: 'market',
    label: '智能体市场',
    icon: 'Shop',
    route: '/market'
  }
]

// 下部分导航项配置
const lowerNavItems = [
  {
    key: 'knowledge',
    label: '知识库',
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
  },
  {
    key: 'system',
    label: '系统管理',
    icon: 'Setting',
    route: '/system'
  }
]

// 计算属性 - 使用chat store的数据
const conversations = computed(() => {
  return showArchivedConversations.value 
    ? chatStore.archivedConversations 
    : chatStore.activeConversations
})

const currentConversation = computed(() => chatStore.currentConversation)
const isLoading = computed(() => chatStore.isLoading)

// 计算属性
const showWorkflowPanel = computed(() => {
  return activeModule.value === 'chat' && chatMode.value === 'agent'
})

const filteredConversations = computed(() => {
  if (!chatStore.searchQuery.trim()) {
    return conversations.value
  }
  const query = chatStore.searchQuery.toLowerCase()
  return conversations.value.filter(conv => 
    conv.title.toLowerCase().includes(query)
  )
})

// 方法
const setActiveModule = (moduleKey: string) => {
  activeModule.value = moduleKey
  const allNavItems = [...upperNavItems, ...lowerNavItems]
  const navItem = allNavItems.find(item => item.key === moduleKey)
  if (navItem && navItem.route) {
    // 切换到智能问答时清空当前会话
    if (moduleKey === 'chat') {
      chatStore.clearCurrentConversation()
    }
    router.push(navItem.route)
  }
}

// 注销方法
const logout = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要退出登录吗？',
      '确认退出',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    await userStore.logout()
    router.push('/login')
  } catch (error) {
    // 用户取消操作
  }
}

const toggleHistoryPanel = async () => {
  showHistoryPanel.value = !showHistoryPanel.value
  
  // 当打开历史面板时，加载对话列表
  if (showHistoryPanel.value) {
    await loadConversations()
  }
}

const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value
  // 收起时自动关闭历史面板
  if (isCollapsed.value) {
    showHistoryPanel.value = false
  }
}

const selectConversation = async (conversation: any) => {
  try {
    // 设置当前对话
    await chatStore.setCurrentConversation(conversation.id)
    
    // 加载对话消息
    await chatStore.loadMessages(conversation.id)
    
    // 关闭历史面板（可选）
    showHistoryPanel.value = false
    
    ElMessage.success(`已切换到对话: ${conversation.title}`)
  } catch (error) {
    console.error('Switch conversation failed:', error)
    ElMessage.error('切换对话失败')
  }
}

const editConversationTitle = (conversation: any) => {
  ElMessage.info('编辑对话标题功能开发中...')
}

const deleteConversationConfirm = async (conversation: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除对话 "${conversation.title}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await chatStore.deleteConversation(conversation.id)
    await loadConversations()
  } catch (error) {
    // 用户取消删除
  }
}

const archiveConversation = async (conversation: any) => {
  await chatStore.archiveConversation(conversation.id)
  await loadConversations()
}

const unarchiveConversation = async (conversation: any) => {
  await chatStore.unarchiveConversation(conversation.id)
  await loadConversations()
}

const toggleArchivedView = () => {
  showArchivedConversations.value = !showArchivedConversations.value
  loadConversations()
}

const handleSearch = (query: string) => {
  chatStore.setSearchQuery(query)
  loadConversations()
}

const loadConversations = async () => {
  await chatStore.loadConversations({
    include_archived: showArchivedConversations.value
  })
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
  } else if (path.includes('/smart-query')) {
    activeModule.value = 'smart-query'
  } else if (path.includes('/creation')) {
    activeModule.value = 'creation'
  } else if (path.includes('/knowledge')) {
    activeModule.value = 'knowledge'
  } else if (path.includes('/workflow')) {
    activeModule.value = 'workflow'
  } else if (path.includes('/agent')) {
    activeModule.value = 'agent'
  } else if (path.includes('/market')) {
    activeModule.value = 'market'
  } else if (path.includes('/system')) {
    activeModule.value = 'system'
  }
}// 生命周期
onMounted(async () => {
  updateActiveModuleFromRoute()
  
  // 初始化用户信息
  if (!userStore.user && localStorage.getItem('access_token')) {
    try {
      await userStore.initializeUser()
    } catch (error) {
      console.log('Failed to initialize user')
    }
  }
  
  await loadConversations()
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
  transition: width 0.3s ease;
}

.sidebar.collapsed {
  width: 60px;
}

/* 主导航 */
.main-nav {
  flex-shrink: 0;
}

.nav-header {
  padding: 20px;
  border-bottom: 1px solid #34495e;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.nav-group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 20px;
}

.nav-group-title {
  font-size: 12px;
  color: #95a5a6;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0;
}

.collapse-btn {
  color: #95a5a6 !important;
  padding: 4px !important;
  min-width: auto !important;
}

.collapse-btn:hover {
  color: #3498db !important;
  background: rgba(52, 73, 94, 0.5) !important;
}

.header-content {
  flex: 1;
}

.app-title {
  margin: 0 0 4px 0;
  font-size: 18px;
  font-weight: 600;
  color: #ecf0f1;
}

.app-subtitle {
  margin: 0;
  font-size: 11px;
  color: #95a5a6;
  opacity: 0.8;
}

.user-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.username {
  font-size: 14px;
  font-weight: 500;
  color: #ecf0f1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 120px;
}

.logout-link {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #bdc3c7;
  text-decoration: none;
  cursor: pointer;
  transition: color 0.2s;
}

.logout-link:hover {
  color: #409eff;
}

.nav-menu {
  padding: 16px 0;
}

.nav-group {
  margin-bottom: 24px;
}

.nav-group:last-child {
  margin-bottom: 0;
}



.nav-item {
  display: flex;
  align-items: center;
  padding: 12px 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  border-left: 3px solid transparent;
  justify-content: flex-start;
}

.sidebar.collapsed .nav-item {
  padding: 12px;
  justify-content: center;
}

.sidebar.collapsed .nav-item .nav-icon {
  margin-right: 0;
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

/* 历史对话面板（浮动显示） */
.history-panel {
  position: fixed;
  top: 80px;
  left: 300px;
  width: 350px;
  max-height: 70vh;
  background: #2c3e50;
  color: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  z-index: 1000;
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

.header-actions {
  display: flex;
  gap: 8px;
  align-items: center;
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

.empty-state {
  padding: 40px 20px;
  text-align: center;
  color: #95a5a6;
  font-size: 14px;
}

.empty-state p {
  margin: 0;
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