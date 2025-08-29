<template>
  <div class="knowledge-container">
    <div class="knowledge-header">
      <h1>知识库管理</h1>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        创建知识库
      </el-button>
    </div>
    
    <div class="knowledge-content">
      <!-- 知识库列表 -->
      <div class="knowledge-list">
        <el-card
          v-for="kb in knowledgeBases"
          :key="kb.id"
          class="knowledge-card"
          shadow="hover"
        >
          <template #header>
            <div class="card-header">
              <span class="kb-name">{{ kb.name }}</span>
              <el-dropdown @command="(command) => handleKnowledgeCommand(command, kb)">
                <el-button type="text" size="small">
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="edit">编辑</el-dropdown-item>
                    <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>
          
          <div class="kb-info">
            <p class="kb-description">{{ kb.description || '暂无描述' }}</p>
            <div class="kb-stats">
              <el-tag size="small">{{ kb.document_count || 0 }} 个文档</el-tag>
              <span class="kb-time">{{ formatTime(kb.updated_at) }}</span>
            </div>
          </div>
          
          <div class="kb-actions">
            <el-button size="small" @click="viewDocuments(kb)">
              查看文档
            </el-button>
            <el-button type="primary" size="small" @click="uploadDocument(kb)">
              上传文档
            </el-button>
          </div>
        </el-card>
        
        <!-- 空状态 -->
        <div v-if="knowledgeBases.length === 0" class="empty-state">
          <el-empty description="暂无知识库">
            <el-button type="primary" @click="showCreateDialog = true">
              创建第一个知识库
            </el-button>
          </el-empty>
        </div>
      </div>
      
      <!-- 文档列表 -->
      <div v-if="selectedKnowledgeBase" class="documents-panel">
        <div class="panel-header">
          <h3>{{ selectedKnowledgeBase.name }} - 文档列表</h3>
          <div class="panel-actions">
            <el-button size="small" @click="selectedKnowledgeBase = null">
              关闭
            </el-button>
            <el-button type="primary" size="small" @click="uploadDocument(selectedKnowledgeBase)">
              上传文档
            </el-button>
          </div>
        </div>
        
        <div class="documents-list">
          <el-table :data="documents" style="width: 100%">
            <el-table-column prop="filename" label="文件名" />
            <el-table-column prop="size" label="大小" width="100">
              <template #default="{ row }">
                {{ formatFileSize(row.size) }}
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getDocumentStatusType(row.status)">
                  {{ getDocumentStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="上传时间" width="180">
              <template #default="{ row }">
                {{ formatTime(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button
                  type="danger"
                  size="small"
                  text
                  @click="deleteDocument(row)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </div>
    
    <!-- 创建知识库对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="创建知识库"
      width="500px"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-width="80px"
      >
        <el-form-item label="名称" prop="name">
          <el-input v-model="createForm.name" placeholder="请输入知识库名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="createForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入知识库描述"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="createKnowledgeBase">
          创建
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 编辑知识库对话框 -->
    <el-dialog
      v-model="showEditDialog"
      title="编辑知识库"
      width="500px"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="createRules"
        label-width="80px"
      >
        <el-form-item label="名称" prop="name">
          <el-input v-model="editForm.name" placeholder="请输入知识库名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="editForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入知识库描述"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" :loading="updating" @click="updateKnowledgeBase">
          保存
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 文件上传对话框 -->
    <el-dialog
      v-model="showUploadDialog"
      title="上传文档"
      width="600px"
    >
      <el-upload
        ref="uploadRef"
        class="upload-demo"
        drag
        multiple
        :auto-upload="false"
        :on-change="handleFileChange"
        :file-list="fileList"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 txt, pdf, doc, docx, md 格式文件，单个文件不超过 10MB
          </div>
        </template>
      </el-upload>
      
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button
          type="primary"
          :loading="uploading"
          :disabled="fileList.length === 0"
          @click="handleUpload"
        >
          上传
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules, type UploadFile } from 'element-plus'
import { Plus, MoreFilled, UploadFilled } from '@element-plus/icons-vue'
import { useKnowledgeStore } from '@/stores/knowledge'
import { formatTime, formatFileSize, getDocumentStatusColor, getDocumentStatusText } from '@/utils'
import type { KnowledgeBase, Document } from '@/types'

const knowledgeStore = useKnowledgeStore()

const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const showUploadDialog = ref(false)
const creating = ref(false)
const updating = ref(false)
const uploading = ref(false)
const selectedKnowledgeBase = ref<KnowledgeBase | null>(null)
const currentEditingKB = ref<KnowledgeBase | null>(null)
const fileList = ref<UploadFile[]>([])

const createFormRef = ref<FormInstance>()
const editFormRef = ref<FormInstance>()
const uploadRef = ref()

const createForm = reactive({
  name: '',
  description: ''
})

const editForm = reactive({
  name: '',
  description: ''
})

const createRules: FormRules = {
  name: [
    { required: true, message: '请输入知识库名称', trigger: 'blur' },
    { min: 2, max: 50, message: '名称长度在2-50个字符', trigger: 'blur' }
  ]
}

const knowledgeBases = computed(() => knowledgeStore.knowledgeBases)
const documents = computed(() => knowledgeStore.documents)

onMounted(() => {
  knowledgeStore.loadKnowledgeBases()
})

const handleKnowledgeCommand = (command: string, kb: KnowledgeBase) => {
  switch (command) {
    case 'edit':
      editKnowledgeBase(kb)
      break
    case 'delete':
      deleteKnowledgeBase(kb)
      break
  }
}

const createKnowledgeBase = async () => {
  if (!createFormRef.value) return
  
  try {
    await createFormRef.value.validate()
    creating.value = true
    
    await knowledgeStore.createKnowledgeBase(createForm)
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    
    // 重置表单
    createForm.name = ''
    createForm.description = ''
  } catch (error) {
    console.error('创建失败:', error)
  } finally {
    creating.value = false
  }
}

const editKnowledgeBase = (kb: KnowledgeBase) => {
  currentEditingKB.value = kb
  editForm.name = kb.name
  editForm.description = kb.description || ''
  showEditDialog.value = true
}

const updateKnowledgeBase = async () => {
  if (!editFormRef.value || !currentEditingKB.value) return
  
  try {
    await editFormRef.value.validate()
    updating.value = true
    
    await knowledgeStore.updateKnowledgeBase(currentEditingKB.value.id, editForm)
    ElMessage.success('更新成功')
    showEditDialog.value = false
  } catch (error) {
    console.error('更新失败:', error)
  } finally {
    updating.value = false
  }
}

const deleteKnowledgeBase = async (kb: KnowledgeBase) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除知识库 "${kb.name}" 吗？此操作不可恢复。`,
      '确认删除',
      { type: 'warning' }
    )
    
    await knowledgeStore.deleteKnowledgeBase(kb.id)
    ElMessage.success('删除成功')
    
    // 如果当前选中的知识库被删除，关闭文档面板
    if (selectedKnowledgeBase.value?.id === kb.id) {
      selectedKnowledgeBase.value = null
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const viewDocuments = async (kb: KnowledgeBase) => {
  selectedKnowledgeBase.value = kb
  await knowledgeStore.loadDocuments(kb.id)
}

const uploadDocument = (kb: KnowledgeBase) => {
  selectedKnowledgeBase.value = kb
  showUploadDialog.value = true
  fileList.value = []
}

const handleFileChange = (file: UploadFile) => {
  // 文件类型验证
  const allowedTypes = ['txt', 'pdf', 'doc', 'docx', 'md']
  const fileExtension = file.name.split('.').pop()?.toLowerCase()
  
  if (!fileExtension || !allowedTypes.includes(fileExtension)) {
    ElMessage.error('不支持的文件类型')
    return false
  }
  
  // 文件大小验证（10MB）
  if (file.size && file.size > 10 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过 10MB')
    return false
  }
  
  return true
}

const handleUpload = async () => {
  if (!selectedKnowledgeBase.value || fileList.value.length === 0) return
  
  uploading.value = true
  
  try {
    for (const file of fileList.value) {
      if (file.raw) {
        await knowledgeStore.uploadDocument(selectedKnowledgeBase.value.id, file.raw)
      }
    }
    
    ElMessage.success('上传成功')
    showUploadDialog.value = false
    fileList.value = []
    
    // 刷新文档列表
    if (selectedKnowledgeBase.value) {
      await knowledgeStore.loadDocuments(selectedKnowledgeBase.value.id)
    }
  } catch (error) {
    ElMessage.error('上传失败')
  } finally {
    uploading.value = false
  }
}

const deleteDocument = async (document: Document) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除文档 "${document.filename}" 吗？`,
      '确认删除',
      { type: 'warning' }
    )
    
    await knowledgeStore.deleteDocument(document.id)
    ElMessage.success('删除成功')
    
    // 刷新文档列表
    if (selectedKnowledgeBase.value) {
      await knowledgeStore.loadDocuments(selectedKnowledgeBase.value.id)
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const getDocumentStatusType = (status: string) => {
  switch (status) {
    case 'processed':
      return 'success'
    case 'processing':
      return 'warning'
    case 'failed':
      return 'danger'
    default:
      return 'info'
  }
}
</script>

<style scoped>
.knowledge-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.knowledge-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.knowledge-header h1 {
  margin: 0;
  color: #333;
}

.knowledge-content {
  display: flex;
  gap: 20px;
}

.knowledge-list {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.knowledge-card {
  height: fit-content;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.kb-name {
  font-weight: 600;
  font-size: 16px;
}

.kb-info {
  margin-bottom: 15px;
}

.kb-description {
  color: #666;
  margin: 0 0 10px 0;
  line-height: 1.5;
}

.kb-stats {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.kb-time {
  font-size: 12px;
  color: #999;
}

.kb-actions {
  display: flex;
  gap: 10px;
}

.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 40px;
}

.documents-panel {
  width: 500px;
  background: white;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
  height: fit-content;
}

.panel-header {
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
}

.panel-actions {
  display: flex;
  gap: 10px;
}

.documents-list {
  padding: 20px;
}

.upload-demo {
  width: 100%;
}
</style>