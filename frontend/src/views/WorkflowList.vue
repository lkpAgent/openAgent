<template>
  <div class="workflow-list-container">
    <div class="header">
      <h1>工作流编排</h1>
      <el-button type="primary" @click="createWorkflow">
        <el-icon><Plus /></el-icon>
        创建工作流
      </el-button>
    </div>

    <div class="search-bar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索工作流..."
        clearable
        @input="handleSearch"
        style="width: 300px"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      
      <el-select v-model="statusFilter" placeholder="状态筛选" style="width: 120px; margin-left: 10px">
        <el-option label="全部" value="" />
        <el-option label="草稿" value="DRAFT" />
        <el-option label="已发布" value="PUBLISHED" />
        <el-option label="已归档" value="ARCHIVED" />
      </el-select>
    </div>

    <div class="workflow-grid" v-loading="loading">
      <div 
        v-for="workflow in filteredWorkflows" 
        :key="workflow.id"
        class="workflow-card"
        @click="editWorkflow(workflow.id)"
      >
        <div class="card-header">
          <h3>{{ workflow.name }}</h3>
          <el-dropdown @command="handleCommand" trigger="click">
            <el-button type="text" size="small" @click.stop>
              <el-icon><MoreFilled /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item :command="`edit-${workflow.id}`">编辑</el-dropdown-item>
                <el-dropdown-item :command="`copy-${workflow.id}`">复制</el-dropdown-item>
                <el-dropdown-item :command="`export-${workflow.id}`">导出</el-dropdown-item>
                <el-dropdown-item :command="`delete-${workflow.id}`" divided>删除</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>

        <div class="card-content">
          <p class="description">{{ workflow.description || '暂无描述' }}</p>
          
          <div class="workflow-stats">
            <div class="stat-item">
              <el-icon><Connection /></el-icon>
              <span>{{ getNodeCount(workflow) }} 个节点</span>
            </div>
            <div class="stat-item">
              <el-icon><Clock /></el-icon>
              <span>{{ formatDate(workflow.updated_at) }}</span>
            </div>
          </div>

          <div class="workflow-status">
            <el-tag 
              :type="getStatusType(workflow.status)"
              size="small"
            >
              {{ getStatusText(workflow.status) }}
            </el-tag>
            <span class="version">v{{ workflow.version }}</span>
          </div>
        </div>

        <div class="card-footer">
          <el-button 
            type="primary" 
            size="small" 
            @click.stop="runWorkflow(workflow.id)"
            :disabled="workflow.status !== 'PUBLISHED'"
          >
            <el-icon><VideoPlay /></el-icon>
            运行
          </el-button>
          <el-button 
            type="default" 
            size="small" 
            @click.stop="editWorkflow(workflow.id)"
          >
            <el-icon><Edit /></el-icon>
            编辑
          </el-button>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="!loading && filteredWorkflows.length === 0" class="empty-state">
        <el-empty description="暂无工作流">
          <el-button type="primary" @click="createWorkflow">创建第一个工作流</el-button>
        </el-empty>
      </div>
    </div>


  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, MoreFilled, Connection, Clock, VideoPlay, Edit } from '@element-plus/icons-vue'
import { workflowApi, type Workflow } from '@/api/workflow'

const router = useRouter()

// 响应式数据
const workflows = ref<Workflow[]>([])
const loading = ref(false)
const searchQuery = ref('')
const statusFilter = ref('')

// 计算属性
const filteredWorkflows = computed(() => {
  let result = workflows.value

  // 搜索过滤
  if (searchQuery.value) {
    result = result.filter(workflow => 
      workflow.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      (workflow.description && workflow.description.toLowerCase().includes(searchQuery.value.toLowerCase()))
    )
  }

  // 状态过滤
  if (statusFilter.value) {
    result = result.filter(workflow => workflow.status === statusFilter.value)
  }

  return result
})

// 方法
const loadWorkflows = async () => {
  loading.value = true
  try {
    const response = await workflowApi.getWorkflows({
      search: searchQuery.value,
      status: statusFilter.value || undefined
    })
    
    // 处理响应数据结构
    const data = response.data
    workflows.value = data.workflows || []
    
  } catch (error) {
    console.error('加载工作流失败:', error)
    ElMessage.error('加载工作流失败')
    workflows.value = []
  } finally {
    loading.value = false
  }
}

const createWorkflow = () => {
  router.push('/workflow/editor/new')
}

const editWorkflow = (workflowId: number) => {
  router.push(`/workflow/editor/${workflowId}`)
}

const runWorkflow = async (workflowId: number) => {
  try {
    await workflowApi.executeWorkflow(workflowId, {})
    ElMessage.success('工作流开始执行')
  } catch (error) {
    console.error('执行工作流失败:', error)
    ElMessage.error('执行工作流失败')
  }
}

const handleCommand = async (command: string) => {
  const [action, id] = command.split('-')
  const workflowId = parseInt(id)

  switch (action) {
    case 'edit':
      editWorkflow(workflowId)
      break
    case 'copy':
      await copyWorkflow(workflowId)
      break
    case 'export':
      await exportWorkflow(workflowId)
      break
    case 'delete':
      await deleteWorkflow(workflowId)
      break
  }
}

const copyWorkflow = async (workflowId: number) => {
  try {
    const workflow = workflows.value.find(w => w.id === workflowId)
    if (!workflow) return

    const newWorkflow = {
      name: `${workflow.name} - 副本`,
      description: workflow.description,
      definition: workflow.definition
    }

    await workflowApi.createWorkflow(newWorkflow)
    ElMessage.success('工作流复制成功')
    loadWorkflows()
  } catch (error) {
    console.error('复制工作流失败:', error)
    ElMessage.error('复制工作流失败')
  }
}

const exportWorkflow = async (workflowId: number) => {
  try {
    const workflow = workflows.value.find(w => w.id === workflowId)
    if (!workflow) return

    const dataStr = JSON.stringify(workflow, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    
    const link = document.createElement('a')
    link.href = url
    link.download = `${workflow.name}.json`
    link.click()
    
    URL.revokeObjectURL(url)
    ElMessage.success('工作流导出成功')
  } catch (error) {
    console.error('导出工作流失败:', error)
    ElMessage.error('导出工作流失败')
  }
}

const deleteWorkflow = async (workflowId: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这个工作流吗？', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await workflowApi.deleteWorkflow(workflowId)
    ElMessage.success('工作流删除成功')
    loadWorkflows()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除工作流失败:', error)
      ElMessage.error('删除工作流失败')
    }
  }
}

const handleSearch = () => {
  loadWorkflows()
}

// 工具函数
const getNodeCount = (workflow: Workflow) => {
  return workflow.definition?.nodes?.length || 0
}

const getStatusType = (status: string) => {
  switch (status) {
    case 'PUBLISHED': return 'success'
    case 'DRAFT': return 'warning'
    case 'ARCHIVED': return 'info'
    default: return 'info'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'PUBLISHED': return '已发布'
    case 'DRAFT': return '草稿'
    case 'ARCHIVED': return '已归档'
    default: return status
  }
}

const formatDate = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

// 生命周期
onMounted(() => {
  loadWorkflows()
})
</script>

<style scoped>
.workflow-list-container {
  padding: 24px;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  height: 100vh;
  width: 100%;
  box-sizing: border-box;
  overflow-y: auto;
  overflow-x: hidden;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  max-width: 100%;
}

.header h1 {
  margin: 0;
  color: #f1f5f9;
  font-size: 28px;
  font-weight: 700;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.search-bar {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
  gap: 12px;
}

.workflow-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
  margin-bottom: 24px;
  width: 100%;
}

.workflow-card {
  background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid rgba(100, 116, 139, 0.3);
  backdrop-filter: blur(10px);
}

.workflow-card:hover {
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  transform: translateY(-4px);
  border-color: rgba(100, 116, 139, 0.5);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.card-header h3 {
  margin: 0;
  color: #f1f5f9;
  font-size: 18px;
  font-weight: 700;
  flex: 1;
  margin-right: 12px;
}

.card-content {
  margin-bottom: 20px;
}

.description {
  color: #cbd5e1;
  font-size: 14px;
  line-height: 1.6;
  margin: 0 0 16px 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.workflow-stats {
  display: flex;
  gap: 20px;
  margin-bottom: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #94a3b8;
  font-size: 13px;
  font-weight: 500;
}

.workflow-status {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.version {
  color: #94a3b8;
  font-size: 13px;
  font-weight: 500;
}

.card-footer {
  display: flex;
  gap: 12px;
}

.card-footer .el-button {
  flex: 1;
}

.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 60px 40px;
  color: #cbd5e1;
  font-size: 16px;
}



@media (max-width: 1200px) {
  .workflow-list-container {
    padding: 20px;
  }
  
  .workflow-grid {
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 20px;
  }
}

@media (max-width: 768px) {
  .workflow-list-container {
    padding: 16px;
  }
  
  .workflow-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .header h1 {
    font-size: 24px;
  }
  
  .search-bar {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .workflow-card {
    padding: 20px;
  }
}
</style>