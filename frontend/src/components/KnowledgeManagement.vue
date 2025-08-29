<template>
  <div class="knowledge-management">
    <div class="knowledge-header">
      <h2>知识库管理</h2>
      <el-button type="primary" @click="createKnowledgeBase">
        <el-icon><Plus /></el-icon>
        新建知识库
      </el-button>
    </div>
    
    <div class="knowledge-content">
      <!-- 知识库列表 -->
      <div class="knowledge-list">
        <el-card v-for="kb in knowledgeBases" :key="kb.id" class="kb-card">
          <template #header>
            <div class="kb-header">
              <span class="kb-name">{{ kb.name }}</span>
              <div class="kb-actions">
                <el-button size="small" text @click="editKnowledgeBase(kb)">
                  <el-icon><Edit /></el-icon>
                </el-button>
                <el-button size="small" text type="danger" @click="deleteKnowledgeBase(kb)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
          </template>
          
          <div class="kb-info">
            <p class="kb-description">{{ kb.description || '暂无描述' }}</p>
            <div class="kb-stats">
              <span>文档数量: {{ kb.document_count || 0 }}</span>
              <span>更新时间: {{ formatTime(kb.updated_at) }}</span>
            </div>
          </div>
        </el-card>
      </div>
    </div>
    
    <!-- 创建/编辑知识库对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEditing ? '编辑知识库' : '新建知识库'" width="500px">
      <el-form :model="formData" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="formData.name" placeholder="请输入知识库名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="formData.description" type="textarea" :rows="3" placeholder="请输入知识库描述" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveKnowledgeBase">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'
import { useKnowledgeStore } from '@/stores/knowledge'
import type { KnowledgeBase } from '@/types/knowledge'

const knowledgeStore = useKnowledgeStore()

const dialogVisible = ref(false)
const isEditing = ref(false)
const currentKb = ref<KnowledgeBase | null>(null)
const formData = ref({
  name: '',
  description: ''
})

const knowledgeBases = computed(() => knowledgeStore.knowledgeBases)

const createKnowledgeBase = () => {
  isEditing.value = false
  formData.value = { name: '', description: '' }
  dialogVisible.value = true
}

const editKnowledgeBase = (kb: KnowledgeBase) => {
  isEditing.value = true
  currentKb.value = kb
  formData.value = {
    name: kb.name,
    description: kb.description || ''
  }
  dialogVisible.value = true
}

const saveKnowledgeBase = async () => {
  if (!formData.value.name.trim()) {
    ElMessage.error('请输入知识库名称')
    return
  }
  
  try {
    if (isEditing.value && currentKb.value) {
      await knowledgeStore.updateKnowledgeBase(currentKb.value.id, formData.value)
      ElMessage.success('知识库更新成功')
    } else {
      await knowledgeStore.createKnowledgeBase(formData.value)
      ElMessage.success('知识库创建成功')
    }
    dialogVisible.value = false
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const deleteKnowledgeBase = async (kb: KnowledgeBase) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除知识库 "${kb.name}" 吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await knowledgeStore.deleteKnowledgeBase(kb.id)
    ElMessage.success('知识库删除成功')
  } catch (error) {
    // 用户取消操作
  }
}

const formatTime = (timestamp: string) => {
  if (!timestamp) return ''
  return new Date(timestamp).toLocaleDateString('zh-CN')
}

onMounted(() => {
  knowledgeStore.loadKnowledgeBases()
})
</script>

<style scoped>
.knowledge-management {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.knowledge-header {
  padding: 20px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fafbfc;
}

.knowledge-header h2 {
  margin: 0;
  color: #303133;
}

.knowledge-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.knowledge-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.kb-card {
  transition: all 0.3s ease;
}

.kb-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.kb-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.kb-name {
  font-weight: 600;
  color: #303133;
}

.kb-actions {
  display: flex;
  gap: 4px;
}

.kb-info {
  padding-top: 8px;
}

.kb-description {
  color: #606266;
  margin-bottom: 12px;
  line-height: 1.5;
}

.kb-stats {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
}
</style>