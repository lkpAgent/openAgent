<template>
  <div class="knowledge-management">
    <!-- 顶部工具栏 -->
    <div class="knowledge-header">
      <div class="header-left">
        <h2>知识库管理</h2>
        <div class="header-stats">
          <span class="stat-item">
            <el-icon><Collection /></el-icon>
            {{ knowledgeBases.length }} 个知识库
          </span>
          <span class="stat-item">
            <el-icon><Document /></el-icon>
            {{ totalDocuments }} 个文档
          </span>
        </div>
      </div>
      <div class="header-actions">
        <el-input
          v-model="searchQuery"
          placeholder="搜索知识库..."
          style="width: 200px; margin-right: 12px"
          clearable
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="createKnowledgeBase">
          <el-icon><Plus /></el-icon>
          新建知识库
        </el-button>
      </div>
    </div>
    
    <!-- 主内容区域 -->
    <div class="knowledge-content">
      <!-- 左侧：知识库列表 -->
      <div class="knowledge-sidebar">
        <div class="sidebar-header">
          <span>知识库列表</span>
          <el-dropdown @command="handleSortChange">
            <el-button text size="small">
              <el-icon><Sort /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="name">按名称排序</el-dropdown-item>
                <el-dropdown-item command="updated_at">按更新时间</el-dropdown-item>
                <el-dropdown-item command="document_count">按文档数量</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
        
        <div v-if="isLoading" class="loading-placeholder">
          <div class="loading-animation">
            <div class="loading-spinner"></div>
            <p>正在加载知识库...</p>
          </div>
        </div>
        
        <div v-else class="knowledge-list">
          <div 
            v-for="kb in filteredKnowledgeBases" 
            :key="kb.id" 
            :class="['kb-item', { active: selectedKb?.id === kb.id }]"
            @click="selectKnowledgeBase(kb)"
          >
            <div class="kb-item-header">
              <div class="kb-name">{{ kb.name }}</div>
              <div class="kb-status">
                <el-tag :type="kb.is_active ? 'success' : 'info'" size="small">
                  {{ kb.is_active ? '活跃' : '停用' }}
                </el-tag>
              </div>
            </div>
            <div class="kb-description">{{ kb.description || '暂无描述' }}</div>
            <div class="kb-stats">
              <span><el-icon><Document /></el-icon> {{ kb.document_count || 0 }}</span>
              <span><el-icon><Clock /></el-icon> {{ formatTime(kb.updated_at) }}</span>
            </div>
          </div>
          
          <!-- 空状态 -->
          <div v-if="filteredKnowledgeBases.length === 0" class="empty-state">
            <el-empty description="暂无知识库" />
          </div>
        </div>
      </div>
      
      <!-- 右侧：知识库详情 -->
      <div class="knowledge-detail">
        <div v-if="!selectedKb" class="detail-empty">
          <div class="empty-state">
            <div class="empty-icon">
              <el-icon size="48"><FolderOpened /></el-icon>
            </div>
            <h3>选择知识库</h3>
            <p>请从左侧列表中选择一个知识库来查看详情和管理文档</p>
          </div>
        </div>
        
        <div v-else class="detail-content">
          <!-- 知识库信息 -->
          <div class="detail-header">
            <div class="detail-title">
              <h3>{{ selectedKb.name }}</h3>
              <div class="detail-actions">
                <el-upload
                  ref="uploadRef"
                  :action="uploadUrl"
                  :headers="uploadHeaders"
                  :before-upload="beforeUpload"
                  :on-success="onUploadSuccess"
                  :on-error="onUploadError"
                  :on-progress="onUploadProgress"
                  :show-file-list="false"
                  multiple
                >
                  <el-button size="small" type="primary">
                    <el-icon><Upload /></el-icon>
                    上传文档
                  </el-button>
                </el-upload>
                <el-button size="small" @click="editKnowledgeBase(selectedKb)">
                  <el-icon><Edit /></el-icon>
                  编辑
                </el-button>
                <el-button size="small" @click="testKnowledgeBase(selectedKb)">
                  <el-icon><Search /></el-icon>
                  测试搜索
                </el-button>
                <el-button size="small" type="danger" @click="deleteKnowledgeBase(selectedKb)">
                  <el-icon><Delete /></el-icon>
                  删除
                </el-button>
              </div>
            </div>
            <div class="detail-info">
              <p class="detail-description">{{ selectedKb.description || '暂无描述' }}</p>
              <div class="detail-meta">
                <el-tag>{{ selectedKb.embedding_model }}</el-tag>
                <span>分块大小: {{ selectedKb.chunk_size }}</span>
                <span>重叠大小: {{ selectedKb.chunk_overlap }}</span>
                <span>创建时间: {{ formatTime(selectedKb.created_at) }}</span>
              </div>
            </div>
          </div>
          
          <!-- 文档管理 -->
          <div class="document-section">
            <div class="section-header">
              <h4>文档列表</h4>
              <div class="section-actions">
                <!-- 上传进度 -->
                <div v-if="uploadingFiles.length > 0" class="upload-progress">
                  <h5>上传进度</h5>
                  <div v-for="file in uploadingFiles" :key="file.uid" class="progress-item">
                    <div class="progress-info">
                      <span class="file-name">{{ file.name }}</span>
                      <span class="progress-percent">{{ file.percentage }}%</span>
                    </div>
                    <el-progress 
                      :percentage="file.percentage" 
                      :status="file.status"
                      :stroke-width="6"
                    />
                  </div>
                </div>
                <el-button size="small" @click="refreshDocuments">
                  <el-icon><Refresh /></el-icon>
                  刷新
                </el-button>
              </div>
            </div>
            
            <!-- 文档列表 -->
            <div class="document-list" v-loading="isLoadingDocuments">
              <el-table :data="documents" style="width: 100%">
                <el-table-column prop="original_filename" label="文件名" min-width="200">
                  <template #default="{ row }">
                    <div class="file-info">
                      <el-icon class="file-icon">
                        <Document v-if="row.file_type === 'pdf'" />
                        <DocumentCopy v-else-if="row.file_type === 'txt'" />
                        <Tickets v-else />
                      </el-icon>
                      <span>{{ row.original_filename }}</span>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column prop="file_size" label="大小" width="100">
                  <template #default="{ row }">
                    {{ formatFileSize(row.file_size) }}
                  </template>
                </el-table-column>
                <el-table-column prop="status" label="状态" width="100">
                  <template #default="{ row }">
                    <el-tag :type="getStatusType(row.status)" size="small">
                      {{ getStatusText(row.status) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="chunk_count" label="分块数" width="80" />
                <el-table-column prop="created_at" label="上传时间" width="150">
                  <template #default="{ row }">
                    {{ formatTime(row.created_at) }}
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="120">
                  <template #default="{ row }">
                    <el-button size="small" text @click="viewDocument(row)">
                      <el-icon><View /></el-icon>
                    </el-button>
                    <el-button size="small" text type="danger" @click="deleteDocument(row)">
                      <el-icon><Delete /></el-icon>
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
              
              <!-- 空状态 -->
              <div v-if="documents.length === 0" class="empty-documents">
                <el-empty description="暂无文档，请上传文档" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 知识库搜索测试对话框 -->
    <el-dialog
      v-model="testDialogVisible"
      title="知识库搜索测试"
      width="600px"
      :close-on-click-modal="false"
    >
      <div class="test-dialog">
        <div class="test-form">
          <el-form :model="testForm" label-width="80px">
            <el-form-item label="搜索内容">
              <el-input
                v-model="testForm.query"
                type="textarea"
                :rows="3"
                placeholder="请输入要搜索的内容..."
                maxlength="500"
                show-word-limit
              />
            </el-form-item>
            <el-form-item label="返回数量">
              <el-input-number
                v-model="testForm.top_k"
                :min="1"
                :max="20"
                style="width: 120px"
              />
            </el-form-item>
            <el-form-item label="相似度">
              <el-slider
                v-model="testForm.score_threshold"
                :min="0"
                :max="1"
                :step="0.1"
                show-input
                style="width: 300px"
              />
            </el-form-item>
          </el-form>
          
          <div class="test-actions">
            <el-button @click="testDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="performSearch" :loading="isSearching">搜索</el-button>
          </div>
        </div>
        
        <!-- 搜索结果 -->
        <div v-if="searchResults.length > 0" class="search-results">
          <h4>搜索结果</h4>
          <div class="result-list">
            <div v-for="(result, index) in searchResults" :key="index" class="result-item">
              <div class="result-header">
                <span class="result-score">相似度: {{ (result.score * 100).toFixed(1) }}%</span>
                <span class="result-source">来源: {{ result.metadata?.filename || '未知' }}</span>
              </div>
              <div class="result-content">{{ result.content }}</div>
            </div>
          </div>
        </div>
        
        <div v-else-if="hasSearched" class="no-results">
          <el-empty description="未找到相关内容" />
        </div>
      </div>
    </el-dialog>
    
    <!-- 文档详情查看对话框 -->
    <el-dialog v-model="documentDetailVisible" title="文档详情" width="80%" top="5vh">
      <div v-if="currentDocument" class="document-detail">
        <!-- 文档基本信息 -->
        <div class="document-info">
          <h3>{{ currentDocument.original_filename }}</h3>
          <div class="document-meta">
            <el-tag>{{ currentDocument.file_type.toUpperCase() }}</el-tag>
            <span>大小: {{ formatFileSize(currentDocument.file_size) }}</span>
            <span>状态: {{ getStatusText(currentDocument.status) }}</span>
            <span>分块数: {{ currentDocument.chunk_count || 0 }}</span>
            <span>上传时间: {{ formatTime(currentDocument.created_at) }}</span>
          </div>
        </div>
        
        <!-- 文档分段内容 -->
        <div class="document-chunks" v-loading="isLoadingChunks">
          <div class="chunks-header">
            <h4>文档分段内容 ({{ documentChunks.length }} 个分段)</h4>
            <el-button size="small" @click="refreshChunks">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
          
          <div v-if="documentChunks.length === 0 && !isLoadingChunks" class="empty-chunks">
            <el-empty description="暂无分段内容" />
          </div>
          
          <div v-else class="chunks-list">
            <div v-for="(chunk, index) in documentChunks" :key="chunk.id" class="chunk-item">
              <div class="chunk-header">
                <span class="chunk-index">分段 {{ index + 1 }}</span>
                <div class="chunk-meta">
                  <span v-if="chunk.page_number">页码: {{ chunk.page_number }}</span>
                  <span>字符数: {{ chunk.content.length }}</span>
                </div>
              </div>
              <div class="chunk-content">
                {{ chunk.content }}
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="documentDetailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
    
    <!-- 新建/编辑知识库对话框 -->
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
import { storeToRefs } from 'pinia'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Plus, Edit, Delete, Search, Sort, Collection, Document, Clock, 
  Upload, Refresh, View, DocumentCopy, Tickets 
} from '@element-plus/icons-vue'
import { useKnowledgeStore } from '@/stores/knowledge'
import { knowledgeApi } from '@/api/knowledge'
import type { KnowledgeBase, CreateKnowledgeBaseRequest, UpdateKnowledgeBaseRequest, Document as DocumentType, DocumentChunk } from '@/types'

const knowledgeStore = useKnowledgeStore()
const { knowledgeBases } = storeToRefs(knowledgeStore)

// 响应式数据
const isLoading = ref(false)
const isLoadingDocuments = ref(false)
const searchQuery = ref('')
const sortBy = ref('updated_at')
const selectedKb = ref<KnowledgeBase | null>(null)
const documents = ref<DocumentType[]>([])
const uploadingFiles = ref<Array<{
  uid: string
  name: string
  percentage: number
  status: 'uploading' | 'success' | 'exception'
}>>([])

// 对话框状态
const dialogVisible = ref(false)
const isEditing = ref(false)
const currentKb = ref<KnowledgeBase | null>(null)
const documentDetailVisible = ref(false)
const currentDocument = ref<DocumentType | null>(null)
const documentChunks = ref<any[]>([])
const isLoadingChunks = ref(false)
const testDialogVisible = ref(false)
const isSearching = ref(false)
const hasSearched = ref(false)
const searchResults = ref<any[]>([])

// 表单数据
const formData = ref<CreateKnowledgeBaseRequest>({
  name: '',
  description: '',
  embedding_model: 'text-embedding-ada-002',
  chunk_size: 1000,
  chunk_overlap: 200
})

// 搜索测试表单数据
const testForm = ref({
  query: '',
  top_k: 5,
  score_threshold: 0.7
})

// 上传相关
const uploadRef = ref()
const uploadUrl = computed(() => {
  return selectedKb.value ? `/api/knowledge-bases/${selectedKb.value.id}/documents` : ''
})
const uploadHeaders = computed(() => ({
  'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`,
}))

// 计算属性
const totalDocuments = computed(() => {
  return knowledgeBases.value.reduce((total, kb) => total + (kb.document_count || 0), 0)
})

const filteredKnowledgeBases = computed(() => {
  let filtered = knowledgeBases.value
  
  // 搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(kb => 
      kb.name.toLowerCase().includes(query) || 
      (kb.description && kb.description.toLowerCase().includes(query))
    )
  }
  
  // 排序
  filtered.sort((a, b) => {
    switch (sortBy.value) {
      case 'name':
        return a.name.localeCompare(b.name)
      case 'document_count':
        return (b.document_count || 0) - (a.document_count || 0)
      case 'updated_at':
      default:
        return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
    }
  })
  
  return filtered
})

// 方法
const handleSortChange = (command: string) => {
  sortBy.value = command
}

const selectKnowledgeBase = async (kb: KnowledgeBase) => {
  selectedKb.value = kb
  await loadDocuments(kb.id.toString())
}

const loadDocuments = async (kbId: string) => {
  try {
    isLoadingDocuments.value = true
    documents.value = await knowledgeStore.loadDocuments(kbId)
  } catch (error) {
    ElMessage.error('加载文档失败')
  } finally {
    isLoadingDocuments.value = false
  }
}

const createKnowledgeBase = () => {
  isEditing.value = false
  formData.value = {
    name: '',
    description: '',
    embedding_model: 'text-embedding-ada-002',
    chunk_size: 1000,
    chunk_overlap: 200
  }
  dialogVisible.value = true
}

const editKnowledgeBase = (kb: KnowledgeBase) => {
  isEditing.value = true
  currentKb.value = kb
  formData.value = {
    name: kb.name,
    description: kb.description || '',
    embedding_model: kb.embedding_model,
    chunk_size: kb.chunk_size,
    chunk_overlap: kb.chunk_overlap
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
      await knowledgeStore.updateKnowledgeBase(currentKb.value.id.toString(), formData.value)
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
    
    await knowledgeStore.deleteKnowledgeBase(kb.id.toString())
    ElMessage.success('知识库删除成功')
    if (selectedKb.value?.id === kb.id) {
      selectedKb.value = null
      documents.value = []
    }
  } catch (error) {
    // 用户取消操作
  }
}

const testKnowledgeBase = (kb: KnowledgeBase) => {
  selectedKb.value = kb
  testDialogVisible.value = true
  hasSearched.value = false
  searchResults.value = []
  testForm.value = {
    query: '',
    top_k: 5,
    score_threshold: 0.7
  }
}

const performSearch = async () => {
  if (!testForm.value.query.trim()) {
    ElMessage.warning('请输入搜索内容')
    return
  }
  
  if (!selectedKb.value) {
    ElMessage.error('请选择知识库')
    return
  }
  
  isSearching.value = true
  hasSearched.value = true
  
  try {
    const searchData = {
      knowledge_base_id: selectedKb.value.id.toString(),
      query: testForm.value.query,
      top_k: testForm.value.top_k,
      score_threshold: testForm.value.score_threshold
    }
    
    searchResults.value = await knowledgeStore.searchKnowledgeBase(searchData)
    
    if (searchResults.value.length === 0) {
      ElMessage.info('未找到相关内容，请尝试调整搜索条件')
    } else {
      ElMessage.success(`找到 ${searchResults.value.length} 条相关内容`)
    }
  } catch (error) {
    ElMessage.error('搜索失败，请稍后重试')
    searchResults.value = []
  } finally {
    isSearching.value = false
  }
}

// 文档相关方法
const refreshDocuments = () => {
  if (selectedKb.value) {
    loadDocuments(selectedKb.value.id.toString())
  }
}

const beforeUpload = (file: File) => {
  const allowedTypes = ['application/pdf', 'text/plain', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
  if (!allowedTypes.includes(file.type)) {
    ElMessage.error('只支持 PDF、TXT、DOC、DOCX 格式的文件')
    return false
  }
  
  const maxSize = 10 * 1024 * 1024 // 10MB
  if (file.size > maxSize) {
    ElMessage.error('文件大小不能超过 10MB')
    return false
  }
  
  // 添加到上传列表
  uploadingFiles.value.push({
    uid: file.uid || Date.now().toString(),
    name: file.name,
    percentage: 0,
    status: 'uploading'
  })
  
  return true
}

const onUploadProgress = (event: any, file: any) => {
  const uploadFile = uploadingFiles.value.find(f => f.uid === file.uid)
  if (uploadFile) {
    uploadFile.percentage = Math.round(event.percent)
  }
}

const onUploadSuccess = (response: any, file: any) => {
  const uploadFile = uploadingFiles.value.find(f => f.uid === file.uid)
  if (uploadFile) {
    uploadFile.status = 'success'
    uploadFile.percentage = 100
  }
  
  ElMessage.success('文档上传成功')
  
  // 延迟移除上传项并刷新文档列表
  setTimeout(() => {
    uploadingFiles.value = uploadingFiles.value.filter(f => f.uid !== file.uid)
    refreshDocuments()
  }, 2000)
}

const onUploadError = (error: any, file: any) => {
  const uploadFile = uploadingFiles.value.find(f => f.uid === file.uid)
  if (uploadFile) {
    uploadFile.status = 'exception'
  }
  
  ElMessage.error('文档上传失败')
  
  // 延迟移除失败的上传项
  setTimeout(() => {
    uploadingFiles.value = uploadingFiles.value.filter(f => f.uid !== file.uid)
  }, 3000)
}

const viewDocument = async (doc: DocumentType) => {
  currentDocument.value = doc
  documentDetailVisible.value = true
  await loadDocumentChunks()
}

const loadDocumentChunks = async () => {
  if (!currentDocument.value || !selectedKb.value) return
  
  isLoadingChunks.value = true
  try {
    const response = await knowledgeApi.getDocumentChunks(
      selectedKb.value.id.toString(),
      currentDocument.value.id.toString()
    )
    documentChunks.value = response.data.chunks
  } catch (error) {
    ElMessage.error('获取文档分段失败')
    documentChunks.value = []
  } finally {
    isLoadingChunks.value = false
  }
}

const refreshChunks = async () => {
  await loadDocumentChunks()
}

const deleteDocument = async (doc: DocumentType) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除文档 "${doc.original_filename}" 吗？`,
      '删除确认',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await knowledgeStore.deleteDocument(selectedKb.value!.id.toString(), doc.id.toString())
    ElMessage.success('文档删除成功')
    refreshDocuments()
  } catch (error) {
    // 用户取消操作
  }
}

// 工具方法
const formatTime = (timestamp: string) => {
  if (!timestamp) return ''
  return new Date(timestamp).toLocaleDateString('zh-CN')
}

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const getStatusType = (status: string) => {
  switch (status) {
    case 'processed': return 'success'
    case 'processing': return 'warning'
    case 'failed': return 'danger'
    default: return 'info'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'processed': return '已处理'
    case 'processing': return '处理中'
    case 'failed': return '失败'
    default: return '未知'
  }
}

onMounted(async () => {
  isLoading.value = true
  try {
    await knowledgeStore.loadKnowledgeBases()
  } catch (error) {
    ElMessage.error('加载知识库失败')
  } finally {
    isLoading.value = false
  }
})
</script>

<style scoped>
.knowledge-management {
  padding: 0;
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
  background: #1e293b;
}

/* 顶部工具栏 */
.knowledge-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 20px;
  background: #334155;
  border-bottom: 1px solid #475569;
}

.header-left h2 {
  margin: 0 0 8px 0;
  color: #f1f5f9;
  font-size: 24px;
  font-weight: 600;
}

.header-stats {
  display: flex;
  gap: 20px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #94a3b8;
  font-size: 14px;
}

.header-actions {
  display: flex;
  align-items: center;
}

/* 主内容区域 */
.knowledge-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* 左侧知识库列表 */
.knowledge-sidebar {
  width: 350px;
  background: #1e293b;
  border-right: 1px solid #475569;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #475569;
  font-weight: 600;
  color: #f1f5f9;
}

.knowledge-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.kb-item {
  padding: 16px;
  margin-bottom: 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid transparent;
  position: relative;
  overflow: hidden;
}

.kb-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.1), transparent);
  transition: left 0.5s ease;
}

.kb-item:hover::before {
  left: 100%;
}

.kb-item:hover {
  background: #334155;
  border-color: #475569;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15);
}

.kb-item.active {
  background: rgba(99, 102, 241, 0.1);
  border-color: #6366f1;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.2);
}

.kb-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.kb-name {
  font-weight: 600;
  color: #f1f5f9;
  font-size: 14px;
}

.kb-description {
  color: #94a3b8;
  font-size: 12px;
  line-height: 1.4;
  margin-bottom: 8px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.kb-stats {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #64748b;
}

.kb-stats span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.empty-state {
  padding: 40px 20px;
  text-align: center;
}

/* 右侧详情区域 */
.knowledge-detail {
  flex: 1;
  background: #1e293b;
  display: flex;
  flex-direction: column;
}

.detail-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.detail-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.detail-header {
  padding: 20px;
  border-bottom: 1px solid #475569;
}

.detail-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.detail-title h3 {
  margin: 0;
  color: #f1f5f9;
  font-size: 20px;
  font-weight: 600;
}

.detail-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.detail-description {
  color: #94a3b8;
  margin: 0 0 12px 0;
  line-height: 1.5;
}

.detail-meta {
  display: flex;
  gap: 16px;
  align-items: center;
  font-size: 12px;
  color: #64748b;
}

/* 文档管理区域 */
.document-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #475569;
}

.section-header h4 {
  margin: 0;
  color: #f1f5f9;
  font-size: 16px;
  font-weight: 600;
}

.section-actions {
  display: flex;
  gap: 8px;
}

.document-list {
  flex: 1;
  overflow: hidden;
  padding: 20px;
}

/* 上传按钮样式 */
.detail-actions .el-upload {
  display: inline-block;
}

/* 上传进度样式 */
.upload-progress {
  margin-top: 16px;
  padding: 16px;
  background: #334155;
  border-radius: 6px;
  border: 1px solid #475569;
  animation: slideInUp 0.3s ease;
}

@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.upload-progress h5 {
  margin: 0 0 12px 0;
  color: #f1f5f9;
  font-size: 14px;
  font-weight: 600;
}

.progress-item {
  margin-bottom: 12px;
}

.progress-item:last-child {
  margin-bottom: 0;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.file-name {
  color: #f1f5f9;
  font-size: 13px;
  font-weight: 500;
  flex: 1;
  text-align: left;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.progress-percent {
  color: #94a3b8;
  font-size: 12px;
  font-weight: 600;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-icon {
  color: #409eff;
}

.empty-documents {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
}

/* 对话框样式 */
.dialog-form {
  padding: 20px 0;
}

.form-row {
  display: flex;
  gap: 16px;
}

.form-row .el-form-item {
  flex: 1;
}

.form-item-description {
  color: #909399;
  font-size: 12px;
  margin-top: 4px;
}

/* 搜索测试对话框样式 */
.test-dialog {
  max-height: 600px;
  overflow-y: auto;
}

.test-form {
  margin-bottom: 20px;
}

.test-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e5e7eb;
}

.search-results {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e5e7eb;
}

.search-results h4 {
  margin: 0 0 15px 0;
  color: #374151;
  font-size: 16px;
  font-weight: 600;
}

.result-list {
  max-height: 300px;
  overflow-y: auto;
}

.result-item {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 10px;
  transition: all 0.3s ease;
  animation: fadeInUp 0.3s ease;
}

.result-item:hover {
  background: #f3f4f6;
  border-color: #d1d5db;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-size: 12px;
}

.result-score {
  background: #dbeafe;
  color: #1e40af;
  padding: 2px 8px;
  border-radius: 12px;
  font-weight: 500;
}

.result-source {
  color: #6b7280;
}

.result-content {
  color: #374151;
  line-height: 1.6;
  font-size: 14px;
}

.no-results {
  margin-top: 20px;
  padding: 40px 0;
  text-align: center;
}

/* 加载动画样式 */
.loading-placeholder {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 300px;
}

.loading-animation {
  text-align: center;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f4f6;
  border-top: 3px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-animation p {
  color: #6b7280;
  font-size: 14px;
  margin: 0;
}

/* 空状态样式 */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #94a3b8;
}

.empty-icon {
  margin-bottom: 16px;
  opacity: 0.6;
}

.empty-state h3 {
  margin: 0 0 8px 0;
  color: #f1f5f9;
  font-size: 18px;
  font-weight: 600;
}

.empty-state p {
  margin: 0;
  font-size: 14px;
  line-height: 1.5;
}

/* 文档详情弹窗样式 */
.document-detail {
  max-height: 70vh;
  overflow-y: auto;
}

.document-info {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #475569;
}

.document-info h3 {
  margin: 0 0 12px 0;
  color: #f1f5f9;
  font-size: 18px;
  font-weight: 600;
}

.document-meta {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  align-items: center;
  font-size: 14px;
  color: #94a3b8;
}

.document-chunks {
  margin-top: 16px;
}

.chunks-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.chunks-header h4 {
  margin: 0;
  color: #f1f5f9;
  font-size: 16px;
  font-weight: 600;
}

.empty-chunks {
  text-align: center;
  padding: 40px 20px;
}

.chunks-list {
  max-height: 400px;
  overflow-y: auto;
}

.chunk-item {
  border: 1px solid #475569;
  border-radius: 8px;
  margin-bottom: 12px;
  overflow: hidden;
}

.chunk-header {
  background: #1e293b;
  padding: 12px 16px;
  border-bottom: 1px solid #475569;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chunk-index {
  font-weight: 600;
  color: #f1f5f9;
  font-size: 14px;
}

.chunk-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #94a3b8;
}

.chunk-content {
  padding: 16px;
  background: #0f172a;
  font-size: 14px;
  line-height: 1.6;
  color: #e2e8f0;
  white-space: pre-wrap;
  word-break: break-word;
}

/* Element Plus 对话框深色主题样式 */
:deep(.el-dialog) {
  background-color: #1e293b !important;
  border: 1px solid #475569 !important;
  border-radius: 12px !important;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4) !important;
}

:deep(.el-dialog__header) {
  background-color: #1e293b !important;
  border-bottom: 1px solid #475569 !important;
  padding: 20px 24px 16px !important;
}

:deep(.el-dialog__title) {
  color: #f1f5f9 !important;
  font-size: 18px !important;
  font-weight: 600 !important;
}

:deep(.el-dialog__headerbtn) {
  color: #94a3b8 !important;
  font-size: 18px !important;
}

:deep(.el-dialog__headerbtn:hover) {
  color: #f1f5f9 !important;
}

:deep(.el-dialog__body) {
  background-color: #1e293b !important;
  color: #e2e8f0 !important;
  padding: 24px !important;
}

:deep(.el-dialog__footer) {
  background-color: #1e293b !important;
  border-top: 1px solid #475569 !important;
  padding: 16px 24px 20px !important;
}

/* Element Plus 表单深色主题样式 */
:deep(.el-form-item__label) {
  color: #f1f5f9 !important;
}

:deep(.el-input__wrapper) {
  background-color: #0f172a !important;
  border: 1px solid #475569 !important;
  border-radius: 6px !important;
  box-shadow: none !important;
}

:deep(.el-input__wrapper:hover) {
  border-color: #6366f1 !important;
}

:deep(.el-input__wrapper.is-focus) {
  border-color: #6366f1 !important;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2) !important;
}

:deep(.el-input__inner) {
  color: #e2e8f0 !important;
  background-color: transparent !important;
}

:deep(.el-input__inner::placeholder) {
  color: #94a3b8 !important;
}

:deep(.el-textarea__inner) {
  background-color: #0f172a !important;
  border: 1px solid #475569 !important;
  color: #e2e8f0 !important;
  border-radius: 6px !important;
}

:deep(.el-textarea__inner:hover) {
  border-color: #6366f1 !important;
}

:deep(.el-textarea__inner:focus) {
  border-color: #6366f1 !important;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2) !important;
}

:deep(.el-textarea__inner::placeholder) {
  color: #94a3b8 !important;
}

/* Element Plus 按钮深色主题样式 */
:deep(.el-button) {
  border-radius: 6px !important;
}

:deep(.el-button--default) {
  background-color: #334155 !important;
  border-color: #475569 !important;
  color: #e2e8f0 !important;
}

:deep(.el-button--default:hover) {
  background-color: #475569 !important;
  border-color: #64748b !important;
  color: #f1f5f9 !important;
}

:deep(.el-button--primary) {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
  border-color: #6366f1 !important;
  color: white !important;
}

:deep(.el-button--primary:hover) {
  background: linear-gradient(135deg, #5855eb 0%, #7c3aed 100%) !important;
  border-color: #5855eb !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4) !important;
}

/* Element Plus 消息框深色主题样式 */
:deep(.el-message-box) {
  background-color: #1e293b !important;
  border: 1px solid #475569 !important;
  border-radius: 12px !important;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4) !important;
}

:deep(.el-message-box__header) {
  background-color: #1e293b !important;
  border-bottom: 1px solid #475569 !important;
}

:deep(.el-message-box__title) {
  color: #f1f5f9 !important;
}

:deep(.el-message-box__content) {
  color: #e2e8f0 !important;
}

:deep(.el-message-box__message) {
  color: #e2e8f0 !important;
}

/* Element Plus 表格深色主题样式 */
:deep(.el-table) {
  background-color: #1e293b !important;
  border: 1px solid #475569 !important;
  border-radius: 8px !important;
  overflow: hidden !important;
}

:deep(.el-table__header-wrapper) {
  background-color: #0f172a !important;
}

:deep(.el-table__header) {
  background-color: #0f172a !important;
}

:deep(.el-table th) {
  background-color: #0f172a !important;
  border-bottom: 1px solid #475569 !important;
  color: #f1f5f9 !important;
  font-weight: 600 !important;
}

:deep(.el-table th.el-table__cell) {
  background-color: #0f172a !important;
  border-bottom: 1px solid #475569 !important;
}

:deep(.el-table td) {
  background-color: #1e293b !important;
  border-bottom: 1px solid #334155 !important;
  color: #e2e8f0 !important;
}

:deep(.el-table td.el-table__cell) {
  background-color: #1e293b !important;
  border-bottom: 1px solid #334155 !important;
}

:deep(.el-table__row:hover > td) {
  background-color: #334155 !important;
}

:deep(.el-table__body tr:hover > td) {
  background-color: #334155 !important;
}

:deep(.el-table__empty-block) {
  background-color: #1e293b !important;
}

:deep(.el-table__empty-text) {
  color: #94a3b8 !important;
}

/* 表格内按钮样式优化 */
:deep(.el-table .el-button--small) {
  padding: 4px 8px !important;
  font-size: 12px !important;
  border-radius: 4px !important;
}

:deep(.el-table .el-button.is-text) {
  background-color: transparent !important;
  border: none !important;
  padding: 4px 8px !important;
}

:deep(.el-table .el-button.is-text:not(.is-disabled):hover) {
  background-color: rgba(99, 102, 241, 0.1) !important;
  color: #6366f1 !important;
}

:deep(.el-table .el-button--danger.is-text:not(.is-disabled):hover) {
  background-color: rgba(239, 68, 68, 0.1) !important;
  color: #ef4444 !important;
}

/* Element Plus 标签深色主题样式 */
:deep(.el-tag) {
  border-radius: 4px !important;
  font-size: 11px !important;
  padding: 2px 6px !important;
}

:deep(.el-tag--success) {
  background-color: rgba(34, 197, 94, 0.1) !important;
  border-color: #22c55e !important;
  color: #22c55e !important;
}

:deep(.el-tag--warning) {
  background-color: rgba(245, 158, 11, 0.1) !important;
  border-color: #f59e0b !important;
  color: #f59e0b !important;
}

:deep(.el-tag--danger) {
  background-color: rgba(239, 68, 68, 0.1) !important;
  border-color: #ef4444 !important;
  color: #ef4444 !important;
}

:deep(.el-tag--info) {
  background-color: rgba(148, 163, 184, 0.1) !important;
  border-color: #94a3b8 !important;
  color: #94a3b8 !important;
}

/* Element Plus 空状态深色主题样式 */
:deep(.el-empty) {
  background-color: transparent !important;
}

:deep(.el-empty__description) {
  color: #94a3b8 !important;
}

:deep(.el-empty__image svg) {
  fill: #475569 !important;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .knowledge-content {
    flex-direction: column;
  }
  
  .knowledge-sidebar {
    width: 100%;
    height: 300px;
  }
  
  .document-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .chunks-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}

@media (max-width: 768px) {
  .knowledge-management {
    padding: 12px;
  }
  
  .knowledge-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .header-actions {
    justify-content: space-between;
  }
  
  .detail-title {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .detail-meta {
    flex-direction: column;
    gap: 8px;
    align-items: flex-start;
  }
}
</style>