<template>
  <div class="agent-management">
    <div class="agent-header">
      <h2>智能体管理</h2>
      <div class="header-actions">
        <el-button @click="importAgent">
          <el-icon><Upload /></el-icon>
          导入智能体
        </el-button>
        <el-button type="primary" @click="createAgent">
          <el-icon><Plus /></el-icon>
          创建智能体
        </el-button>
      </div>
    </div>
    
    <div class="agent-content">
      <!-- 智能体列表 -->
      <div class="agent-list-section">
        <div class="list-header">
          <div class="search-filters">
            <el-input
              v-model="searchQuery"
              placeholder="搜索智能体..."
              size="small"
              clearable
              style="width: 200px;"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            
            <el-select v-model="filterCategory" placeholder="分类" size="small" style="width: 120px;">
              <el-option label="全部" value="" />
              <el-option label="客服" value="customer_service" />
              <el-option label="销售" value="sales" />
              <el-option label="技术" value="technical" />
              <el-option label="创意" value="creative" />
            </el-select>
            
            <el-select v-model="filterStatus" placeholder="状态" size="small" style="width: 100px;">
              <el-option label="全部" value="" />
              <el-option label="活跃" value="active" />
              <el-option label="停用" value="inactive" />
              <el-option label="训练中" value="training" />
            </el-select>
          </div>
          
          <div class="view-toggle">
            <el-radio-group v-model="viewMode" size="small">
              <el-radio-button label="grid">卡片</el-radio-button>
              <el-radio-button label="list">列表</el-radio-button>
            </el-radio-group>
          </div>
        </div>
        
        <!-- 卡片视图 -->
        <div v-if="viewMode === 'grid'" class="agent-grid">
          <div 
            v-for="agent in filteredAgents" 
            :key="agent.id"
            :class="['agent-card', { selected: selectedAgent?.id === agent.id }]"
            @click="selectAgent(agent)"
          >
            <div class="card-header">
              <div class="agent-avatar">
                <img v-if="agent.avatar" :src="agent.avatar" :alt="agent.name" />
                <el-icon v-else class="default-avatar"><Avatar /></el-icon>
              </div>
              <div class="agent-info">
                <h3 class="agent-name">{{ agent.name }}</h3>
                <span class="agent-category">{{ getCategoryText(agent.category) }}</span>
              </div>
              <div class="agent-status">
                <el-tag :type="getStatusType(agent.status)" size="small">
                  {{ getStatusText(agent.status) }}
                </el-tag>
              </div>
            </div>
            
            <div class="card-content">
              <p class="agent-description">{{ agent.description }}</p>
              <div class="agent-stats">
                <div class="stat-item">
                  <span class="stat-label">对话数</span>
                  <span class="stat-value">{{ agent.conversation_count }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">满意度</span>
                  <span class="stat-value">{{ agent.satisfaction_rate }}%</span>
                </div>
              </div>
            </div>
            
            <div class="card-actions">
              <el-button size="small" @click.stop="testAgent(agent)">
                <el-icon><ChatDotRound /></el-icon>
                测试
              </el-button>
              <el-button size="small" @click.stop="editAgent(agent)">
                <el-icon><Edit /></el-icon>
                编辑
              </el-button>
              <el-dropdown @command="handleAgentAction" trigger="click">
                <el-button size="small">
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item :command="{ action: 'duplicate', agent }">
                      <el-icon><CopyDocument /></el-icon>
                      复制
                    </el-dropdown-item>
                    <el-dropdown-item :command="{ action: 'export', agent }">
                      <el-icon><Download /></el-icon>
                      导出
                    </el-dropdown-item>
                    <el-dropdown-item :command="{ action: 'delete', agent }" divided>
                      <el-icon><Delete /></el-icon>
                      删除
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </div>
        
        <!-- 列表视图 -->
        <div v-else class="agent-table">
          <el-table :data="filteredAgents" @row-click="selectAgent">
            <el-table-column width="60">
              <template #default="{ row }">
                <div class="table-avatar">
                  <img v-if="row.avatar" :src="row.avatar" :alt="row.name" />
                  <el-icon v-else><Avatar /></el-icon>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="name" label="名称" width="150" />
            <el-table-column prop="category" label="分类" width="100">
              <template #default="{ row }">
                {{ getCategoryText(row.category) }}
              </template>
            </el-table-column>
            <el-table-column prop="description" label="描述" show-overflow-tooltip />
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)" size="small">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="conversation_count" label="对话数" width="80" />
            <el-table-column prop="satisfaction_rate" label="满意度" width="80">
              <template #default="{ row }">
                {{ row.satisfaction_rate }}%
              </template>
            </el-table-column>
            <el-table-column prop="updated_at" label="更新时间" width="120">
              <template #default="{ row }">
                {{ formatTime(row.updated_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150">
              <template #default="{ row }">
                <el-button size="small" @click.stop="testAgent(row)">
                  测试
                </el-button>
                <el-button size="small" @click.stop="editAgent(row)">
                  编辑
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
      
      <!-- 智能体详情/编辑面板 -->
      <div v-if="selectedAgent" class="agent-detail">
        <div class="detail-header">
          <h3>{{ isEditing ? '编辑智能体' : '智能体详情' }}</h3>
          <div class="detail-actions">
            <el-button v-if="!isEditing" @click="startEdit">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <template v-else>
              <el-button @click="cancelEdit">取消</el-button>
              <el-button type="primary" @click="saveAgent">保存</el-button>
            </template>
          </div>
        </div>
        
        <div class="detail-content">
          <el-tabs v-model="activeTab">
            <!-- 基本信息 -->
            <el-tab-pane label="基本信息" name="basic">
              <el-form :model="editingAgent" label-width="80px">
                <el-form-item label="头像">
                  <div class="avatar-upload">
                    <div class="avatar-preview">
                      <img v-if="editingAgent.avatar" :src="editingAgent.avatar" alt="头像" />
                      <el-icon v-else class="default-avatar"><Avatar /></el-icon>
                    </div>
                    <el-button v-if="isEditing" size="small" @click="uploadAvatar">
                      上传头像
                    </el-button>
                  </div>
                </el-form-item>
                
                <el-form-item label="名称">
                  <el-input v-model="editingAgent.name" :disabled="!isEditing" />
                </el-form-item>
                
                <el-form-item label="分类">
                  <el-select v-model="editingAgent.category" :disabled="!isEditing">
                    <el-option label="客服" value="customer_service" />
                    <el-option label="销售" value="sales" />
                    <el-option label="技术" value="technical" />
                    <el-option label="创意" value="creative" />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="状态">
                  <el-select v-model="editingAgent.status" :disabled="!isEditing">
                    <el-option label="活跃" value="active" />
                    <el-option label="停用" value="inactive" />
                    <el-option label="训练中" value="training" />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="描述">
                  <el-input 
                    v-model="editingAgent.description" 
                    type="textarea" 
                    :rows="3" 
                    :disabled="!isEditing" 
                  />
                </el-form-item>
              </el-form>
            </el-tab-pane>
            
            <!-- 提示词配置 -->
            <el-tab-pane label="提示词" name="prompt">
              <div class="prompt-section">
                <el-form :model="editingAgent" label-width="80px">
                  <el-form-item label="系统提示">
                    <el-input 
                      v-model="editingAgent.system_prompt" 
                      type="textarea" 
                      :rows="6" 
                      :disabled="!isEditing"
                      placeholder="请输入系统提示词，定义智能体的角色和行为..."
                    />
                  </el-form-item>
                  
                  <el-form-item label="用户提示">
                    <el-input 
                      v-model="editingAgent.user_prompt" 
                      type="textarea" 
                      :rows="4" 
                      :disabled="!isEditing"
                      placeholder="请输入用户提示词模板..."
                    />
                  </el-form-item>
                  
                  <el-form-item label="温度">
                    <el-slider 
                      v-model="editingAgent.temperature" 
                      :min="0" 
                      :max="2" 
                      :step="0.1" 
                      :disabled="!isEditing"
                      show-input
                    />
                  </el-form-item>
                  
                  <el-form-item label="最大长度">
                    <el-input-number 
                      v-model="editingAgent.max_tokens" 
                      :min="1" 
                      :max="4096" 
                      :disabled="!isEditing"
                    />
                  </el-form-item>
                </el-form>
              </div>
            </el-tab-pane>
            
            <!-- 知识库 -->
            <el-tab-pane label="知识库" name="knowledge">
              <div class="knowledge-section">
                <div class="section-header">
                  <h4>关联知识库</h4>
                  <el-button v-if="isEditing" size="small" @click="addKnowledge">
                    <el-icon><Plus /></el-icon>
                    添加知识库
                  </el-button>
                </div>
                
                <div class="knowledge-list">
                  <div 
                    v-for="kb in editingAgent.knowledge_bases" 
                    :key="kb.id"
                    class="knowledge-item"
                  >
                    <div class="knowledge-info">
                      <span class="knowledge-name">{{ kb.name }}</span>
                      <span class="knowledge-desc">{{ kb.description }}</span>
                    </div>
                    <div class="knowledge-actions">
                      <el-button v-if="isEditing" size="small" text type="danger" @click="removeKnowledge(kb.id)">
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </div>
                  </div>
                </div>
              </div>
            </el-tab-pane>
            
            <!-- 统计数据 -->
            <el-tab-pane label="统计" name="stats">
              <div class="stats-section">
                <div class="stats-grid">
                  <div class="stat-card">
                    <div class="stat-icon">
                      <el-icon><ChatDotRound /></el-icon>
                    </div>
                    <div class="stat-content">
                      <div class="stat-number">{{ selectedAgent.conversation_count }}</div>
                      <div class="stat-label">总对话数</div>
                    </div>
                  </div>
                  
                  <div class="stat-card">
                    <div class="stat-icon">
                      <el-icon><Star /></el-icon>
                    </div>
                    <div class="stat-content">
                      <div class="stat-number">{{ selectedAgent.satisfaction_rate }}%</div>
                      <div class="stat-label">满意度</div>
                    </div>
                  </div>
                  
                  <div class="stat-card">
                    <div class="stat-icon">
                      <el-icon><Timer /></el-icon>
                    </div>
                    <div class="stat-content">
                      <div class="stat-number">{{ selectedAgent.avg_response_time }}s</div>
                      <div class="stat-label">平均响应时间</div>
                    </div>
                  </div>
                  
                  <div class="stat-card">
                    <div class="stat-icon">
                      <el-icon><User /></el-icon>
                    </div>
                    <div class="stat-content">
                      <div class="stat-number">{{ selectedAgent.active_users }}</div>
                      <div class="stat-label">活跃用户</div>
                    </div>
                  </div>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Search,
  Upload,
  Avatar,
  ChatDotRound,
  Edit,
  MoreFilled,
  CopyDocument,
  Download,
  Delete,
  Star,
  Timer,
  User
} from '@element-plus/icons-vue'

// 类型定义
interface KnowledgeBase {
  id: string
  name: string
  description: string
}

interface Agent {
  id: string
  name: string
  description: string
  category: 'customer_service' | 'sales' | 'technical' | 'creative'
  status: 'active' | 'inactive' | 'training'
  avatar?: string
  system_prompt: string
  user_prompt: string
  temperature: number
  max_tokens: number
  knowledge_bases: KnowledgeBase[]
  conversation_count: number
  satisfaction_rate: number
  avg_response_time: number
  active_users: number
  created_at: string
  updated_at: string
}

// 响应式数据
const searchQuery = ref('')
const filterCategory = ref('')
const filterStatus = ref('')
const viewMode = ref<'grid' | 'list'>('grid')
const selectedAgent = ref<Agent | null>(null)
const editingAgent = ref<Agent | null>(null)
const isEditing = ref(false)
const activeTab = ref('basic')

// 模拟数据
const agents = ref<Agent[]>([
  {
    id: '1',
    name: '客服小助手',
    description: '专业的客户服务智能体，能够处理常见问题和投诉',
    category: 'customer_service',
    status: 'active',
    avatar: '',
    system_prompt: '你是一个专业的客服代表，请友好、耐心地帮助用户解决问题。',
    user_prompt: '用户问题：{question}',
    temperature: 0.7,
    max_tokens: 1000,
    knowledge_bases: [
      { id: '1', name: '产品手册', description: '产品功能和使用说明' },
      { id: '2', name: 'FAQ', description: '常见问题解答' }
    ],
    conversation_count: 1250,
    satisfaction_rate: 92,
    avg_response_time: 2.3,
    active_users: 156,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },
  {
    id: '2',
    name: '销售顾问',
    description: '专业的销售智能体，帮助客户了解产品并促成交易',
    category: 'sales',
    status: 'active',
    avatar: '',
    system_prompt: '你是一个专业的销售顾问，请帮助客户了解产品价值并促成购买。',
    user_prompt: '客户咨询：{inquiry}',
    temperature: 0.8,
    max_tokens: 1200,
    knowledge_bases: [
      { id: '3', name: '产品目录', description: '产品详细信息和价格' },
      { id: '4', name: '销售话术', description: '销售技巧和话术模板' }
    ],
    conversation_count: 890,
    satisfaction_rate: 88,
    avg_response_time: 3.1,
    active_users: 89,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  },
  {
    id: '3',
    name: '技术专家',
    description: '技术支持智能体，解决技术问题和提供解决方案',
    category: 'technical',
    status: 'training',
    avatar: '',
    system_prompt: '你是一个技术专家，请提供准确的技术支持和解决方案。',
    user_prompt: '技术问题：{problem}',
    temperature: 0.5,
    max_tokens: 1500,
    knowledge_bases: [
      { id: '5', name: '技术文档', description: '技术规范和API文档' },
      { id: '6', name: '故障排除', description: '常见故障和解决方案' }
    ],
    conversation_count: 456,
    satisfaction_rate: 95,
    avg_response_time: 4.2,
    active_users: 34,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  }
])

// 计算属性
const filteredAgents = computed(() => {
  let filtered = agents.value
  
  // 搜索过滤
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(agent => 
      agent.name.toLowerCase().includes(query) ||
      agent.description.toLowerCase().includes(query)
    )
  }
  
  // 分类过滤
  if (filterCategory.value) {
    filtered = filtered.filter(agent => agent.category === filterCategory.value)
  }
  
  // 状态过滤
  if (filterStatus.value) {
    filtered = filtered.filter(agent => agent.status === filterStatus.value)
  }
  
  return filtered
})

// 方法
const selectAgent = (agent: Agent) => {
  selectedAgent.value = agent
  editingAgent.value = { ...agent }
  isEditing.value = false
  activeTab.value = 'basic'
}

const createAgent = () => {
  const newAgent: Agent = {
    id: Date.now().toString(),
    name: '新智能体',
    description: '请输入智能体描述',
    category: 'customer_service',
    status: 'inactive',
    avatar: '',
    system_prompt: '',
    user_prompt: '',
    temperature: 0.7,
    max_tokens: 1000,
    knowledge_bases: [],
    conversation_count: 0,
    satisfaction_rate: 0,
    avg_response_time: 0,
    active_users: 0,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  }
  
  agents.value.push(newAgent)
  selectedAgent.value = newAgent
  editingAgent.value = { ...newAgent }
  isEditing.value = true
}

const startEdit = () => {
  isEditing.value = true
}

const cancelEdit = () => {
  if (selectedAgent.value) {
    editingAgent.value = { ...selectedAgent.value }
  }
  isEditing.value = false
}

const saveAgent = () => {
  if (!editingAgent.value) return
  
  const index = agents.value.findIndex(a => a.id === editingAgent.value!.id)
  if (index > -1) {
    editingAgent.value.updated_at = new Date().toISOString()
    agents.value[index] = { ...editingAgent.value }
    selectedAgent.value = { ...editingAgent.value }
  }
  
  isEditing.value = false
  ElMessage.success('智能体保存成功')
}

const editAgent = (agent: Agent) => {
  selectAgent(agent)
  startEdit()
}

const testAgent = (agent: Agent) => {
  ElMessage.info(`正在启动 ${agent.name} 的测试对话...`)
  // 这里可以打开测试对话窗口
}

const handleAgentAction = ({ action, agent }: { action: string, agent: Agent }) => {
  switch (action) {
    case 'duplicate':
      duplicateAgent(agent)
      break
    case 'export':
      exportAgent(agent)
      break
    case 'delete':
      deleteAgent(agent)
      break
  }
}

const duplicateAgent = (agent: Agent) => {
  const newAgent: Agent = {
    ...agent,
    id: Date.now().toString(),
    name: agent.name + ' (副本)',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  }
  
  agents.value.push(newAgent)
  ElMessage.success('智能体复制成功')
}

const exportAgent = (agent: Agent) => {
  // 模拟导出功能
  const dataStr = JSON.stringify(agent, null, 2)
  const dataBlob = new Blob([dataStr], { type: 'application/json' })
  const url = URL.createObjectURL(dataBlob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${agent.name}.json`
  link.click()
  URL.revokeObjectURL(url)
  
  ElMessage.success('智能体导出成功')
}

const deleteAgent = async (agent: Agent) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除智能体 "${agent.name}" 吗？`,
      '删除确认',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const index = agents.value.findIndex(a => a.id === agent.id)
    if (index > -1) {
      agents.value.splice(index, 1)
      if (selectedAgent.value?.id === agent.id) {
        selectedAgent.value = null
        editingAgent.value = null
      }
      ElMessage.success('智能体删除成功')
    }
  } catch (error) {
    // 用户取消
  }
}

const importAgent = () => {
  // 模拟导入功能
  const input = document.createElement('input')
  input.type = 'file'
  input.accept = '.json'
  input.onchange = (e) => {
    const file = (e.target as HTMLInputElement).files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (e) => {
        try {
          const agentData = JSON.parse(e.target?.result as string)
          agentData.id = Date.now().toString()
          agentData.created_at = new Date().toISOString()
          agentData.updated_at = new Date().toISOString()
          agents.value.push(agentData)
          ElMessage.success('智能体导入成功')
        } catch (error) {
          ElMessage.error('文件格式错误')
        }
      }
      reader.readAsText(file)
    }
  }
  input.click()
}

const uploadAvatar = () => {
  // 模拟头像上传
  ElMessage.info('头像上传功能开发中...')
}

const addKnowledge = () => {
  // 模拟添加知识库
  ElMessage.info('添加知识库功能开发中...')
}

const removeKnowledge = (kbId: string) => {
  if (editingAgent.value) {
    editingAgent.value.knowledge_bases = editingAgent.value.knowledge_bases.filter(kb => kb.id !== kbId)
  }
}

const getCategoryText = (category: string) => {
  const categoryMap = {
    customer_service: '客服',
    sales: '销售',
    technical: '技术',
    creative: '创意'
  }
  return categoryMap[category] || category
}

const getStatusText = (status: string) => {
  const statusMap = {
    active: '活跃',
    inactive: '停用',
    training: '训练中'
  }
  return statusMap[status] || status
}

const getStatusType = (status: string) => {
  const typeMap = {
    active: 'success',
    inactive: 'info',
    training: 'warning'
  }
  return typeMap[status] || 'info'
}

const formatTime = (timestamp: string) => {
  return new Date(timestamp).toLocaleDateString('zh-CN')
}

// 监听选中智能体变化
watch(selectedAgent, (newAgent) => {
  if (newAgent) {
    editingAgent.value = { ...newAgent }
  }
})
</script>

<style scoped>
.agent-management {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.agent-header {
  padding: 20px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fafbfc;
}

.agent-header h2 {
  margin: 0;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.agent-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* 智能体列表区域 */
.agent-list-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
}

.list-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fafbfc;
}

.search-filters {
  display: flex;
  gap: 12px;
  align-items: center;
}

.view-toggle {
  display: flex;
  align-items: center;
}

/* 卡片视图 */
.agent-grid {
  flex: 1;
  padding: 20px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
  overflow-y: auto;
}

.agent-card {
  border: 1px solid #e4e7ed;
  border-radius: 12px;
  background: white;
  transition: all 0.3s ease;
  cursor: pointer;
  overflow: hidden;
}

.agent-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.agent-card.selected {
  border-color: #409eff;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

.card-header {
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.agent-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  overflow: hidden;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.agent-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.default-avatar {
  font-size: 20px;
  color: #c0c4cc;
}

.agent-info {
  flex: 1;
}

.agent-name {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.agent-category {
  font-size: 12px;
  color: #909399;
}

.card-content {
  padding: 16px;
}

.agent-description {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #606266;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.agent-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.stat-item {
  text-align: center;
}

.stat-label {
  display: block;
  font-size: 11px;
  color: #909399;
  margin-bottom: 2px;
}

.stat-value {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.card-actions {
  padding: 12px 16px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  gap: 8px;
  background: #fafbfc;
}

/* 列表视图 */
.agent-table {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.table-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  overflow: hidden;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.table-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 智能体详情面板 */
.agent-detail {
  width: 400px;
  border-left: 1px solid #e4e7ed;
  background: #fafbfc;
  display: flex;
  flex-direction: column;
}

.detail-header {
  padding: 20px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
}

.detail-header h3 {
  margin: 0;
  font-size: 18px;
  color: #303133;
}

.detail-actions {
  display: flex;
  gap: 8px;
}

.detail-content {
  flex: 1;
  overflow: hidden;
}

.avatar-upload {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar-preview {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  overflow: hidden;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #e4e7ed;
}

.avatar-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.prompt-section {
  padding: 20px;
}

.knowledge-section {
  padding: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h4 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.knowledge-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.knowledge-item {
  padding: 12px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.knowledge-info {
  flex: 1;
}

.knowledge-name {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.knowledge-desc {
  display: block;
  font-size: 12px;
  color: #606266;
}

.stats-section {
  padding: 20px;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.stat-card {
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: white;
  display: flex;
  align-items: center;
  gap: 12px;
}

.stat-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #f0f2f5;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: #409eff;
}

.stat-content {
  flex: 1;
}

.stat-number {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: #606266;
}
</style>