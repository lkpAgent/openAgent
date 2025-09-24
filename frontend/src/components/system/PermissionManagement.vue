<template>
  <div class="permission-management">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">
          <el-icon><Lock /></el-icon>
          权限管理
        </h2>
        <p class="page-description">管理系统权限和功能模块</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          新增权限
        </el-button>
      </div>
    </div>

    <div class="content-card">
      <!-- 搜索栏 -->
      <div class="search-bar">
        <div class="search-left">
          <el-input
            v-model="searchForm.search"
            placeholder="搜索权限名称或编码"
            style="width: 300px"
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          
          <el-select
            v-model="searchForm.resource"
            placeholder="选择资源"
            style="width: 200px"
            clearable
            @change="handleFilter"
          >
            <el-option label="用户" value="user" />
            <el-option label="角色" value="role" />
            <el-option label="权限" value="permission" />
            <el-option label="部门" value="department" />
            <el-option label="系统" value="system" />
            <el-option label="大模型" value="llm_config" />
          </el-select>
          
          <el-select
            v-model="searchForm.action"
            placeholder="操作类型"
            style="width: 150px"
            clearable
            @change="handleFilter"
          >
            <el-option label="创建" value="create" />
            <el-option label="读取" value="read" />
            <el-option label="更新" value="update" />
            <el-option label="删除" value="delete" />
            <el-option label="管理" value="manage" />
            <el-option label="分配" value="assign" />
            <el-option label="系统管理" value="admin" />
          </el-select>
        </div>
        
        <div class="search-right">
          <el-button @click="handleRefresh">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>

      <!-- 表格容器 -->
      <div class="table-container">
        <!-- 权限表格 -->
        <div class="table-wrapper">
          <el-table
            v-loading="loading"
            :data="permissions"
            style="width: 100%"
            height="100%"
            row-key="id"
            :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
            :default-expand-all="false"
            @selection-change="handleSelectionChange"
          >
            <el-table-column type="selection" width="55" />
            
            <el-table-column prop="name" label="权限名称" width="200">
              <template #default="{ row }">
                <div class="permission-name">
                  <el-icon class="permission-icon" style="color: #409eff">
                    <Lock />
                  </el-icon>
                  <span class="name-text">{{ row.name }}</span>
                </div>
              </template>
            </el-table-column>
            
            <el-table-column prop="code" label="权限编码" width="200">
              <template #default="{ row }">
                <el-tag type="info" size="small">
                  {{ row.code }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="resource" label="资源标识" width="150">
              <template #default="{ row }">
                <el-tag type="info" size="small">
                  {{ row.resource }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="description" label="描述" min-width="200">
              <template #default="{ row }">
                <span v-if="row.description">{{ row.description }}</span>
                <span v-else class="text-muted">暂无描述</span>
              </template>
            </el-table-column>
            
            <el-table-column prop="action" label="操作类型" width="120">
              <template #default="{ row }">
                <el-tag :type="getActionTagType(row.action)" size="small">
                  {{ getActionText(row.action) }}
                </el-tag>
              </template>
            </el-table-column>
            

            

            
            <el-table-column prop="created_at" label="创建时间" width="160">
              <template #default="{ row }">
                {{ formatDateTime(row.created_at) }}
              </template>
            </el-table-column>
            
            <el-table-column label="操作" width="280" fixed="right">
              <template #default="{ row }">
                <el-button
                  type="primary"
                  size="small"
                  @click="handleEdit(row)"
                >
                  编辑
                </el-button>

                <el-button
                  type="danger"
                  size="small"
                  @click="handleDelete(row)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 分页 -->
        <div class="pagination-container">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :total="total"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </div>
    </div>

    <!-- 权限表单对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      @close="handleDialogClose"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="权限名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入权限名称" />
        </el-form-item>
        
        <el-form-item label="权限编码" prop="code">
          <el-input v-model="formData.code" placeholder="请输入权限编码" />
        </el-form-item>
        
        <el-form-item label="资源标识" prop="resource">
          <el-input
            v-model="formData.resource"
            placeholder="请输入资源标识（如：user、role、system）"
          />
        </el-form-item>
        
        <el-form-item label="操作类型" prop="action">
          <el-select v-model="formData.action" placeholder="请选择操作类型" style="width: 100%">
            <el-option label="创建" value="create" />
            <el-option label="读取" value="read" />
            <el-option label="更新" value="update" />
            <el-option label="删除" value="delete" />
            <el-option label="管理" value="manage" />
            <el-option label="分配" value="assign" />
            <el-option label="系统管理" value="admin" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="权限描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入权限描述"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 批量操作对话框 -->
    <el-dialog
      v-model="batchDialogVisible"
      title="批量操作"
      width="500px"
    >
      <div class="batch-operations">
        <p>已选择 <strong>{{ selectedPermissions.length }}</strong> 个权限</p>
        
        <div class="operation-buttons">

          
          <el-button
            type="danger"
            @click="handleBatchDelete"
            :loading="submitting"
          >
            批量删除
          </el-button>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="batchDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import {
  Lock,
  Folder,
  Mouse,
  Connection,
  Plus,
  Search,
  Refresh
} from '@element-plus/icons-vue'
import { formatDateTime } from '@/utils/date'
import { permissionsApi, type Permission, type PermissionCreate, type PermissionUpdate } from '@/api/roles'

// 响应式数据
const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const batchDialogVisible = ref(false)
const isEdit = ref(false)
const currentPermission = ref(null)
const selectedPermissions = ref([])

// 搜索和筛选
const searchForm = ref({
  search: '',
  resource: '',
  action: ''
})

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 表单
const formRef = ref<FormInstance>()
const formData = reactive<PermissionCreate>({
  name: '',
  code: '',
  resource: '',
  action: '',
  description: ''
})



// 权限数据
const permissions = ref<Permission[]>([])
const resources = ref<string[]>([])
const actions = ref<string[]>([])

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入权限名称', trigger: 'blur' },
    { min: 2, max: 50, message: '权限名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入权限编码', trigger: 'blur' },
    { pattern: /^[A-Z0-9_]+$/, message: '权限编码只能包含大写字母、数字和下划线', trigger: 'blur' }
  ],
  resource: [
    { required: true, message: '请输入资源标识', trigger: 'blur' }
  ],
  action: [
    { required: true, message: '请输入操作类型', trigger: 'blur' }
  ]
}

// 计算属性
const dialogTitle = computed(() => isEdit.value ? '编辑权限' : '新增权限')



// 方法
const getActionTagType = (action: string) => {
  const typeMap = {
    'create': 'success',
    'read': 'info',
    'update': 'warning',
    'delete': 'danger',
    'manage': 'primary',
    'assign': '',
    'admin': 'danger'
  }
  return typeMap[action] || 'info'
}

const getActionText = (action: string) => {
  const textMap = {
    'create': '创建',
    'read': '读取',
    'update': '更新',
    'delete': '删除',
    'manage': '管理',
    'assign': '分配',
    'admin': '系统管理'
  }
  return textMap[action] || action
}

const handleSearch = () => {
  currentPage.value = 1
  loadPermissions()
}

const handleFilter = () => {
  currentPage.value = 1
  loadPermissions()
}

const handleRefresh = () => {
  searchForm.value = {
    search: '',
    resource: '',
    action: ''
  }
  loadPermissions()
}

const handleSelectionChange = (selection: any[]) => {
  selectedPermissions.value = selection
}

const handleCreate = () => {
  isEdit.value = false
  currentPermission.value = null
  resetForm()
  dialogVisible.value = true
}

const handleEdit = (permission: Permission) => {
  isEdit.value = true
  currentPermission.value = permission
  Object.assign(formData, {
    name: permission.name,
    code: permission.code,
    resource: permission.resource,
    action: permission.action,
    description: permission.description
  })
  dialogVisible.value = true
}



const handleDelete = async (row: Permission) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除权限 "${row.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await permissionsApi.deletePermission(row.id)
    ElMessage.success('删除成功')
    loadPermissions()
  } catch (error: any) {
    if (error.message !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}





const handleBatchDelete = async () => {
  if (selectedPermissions.value.length === 0) {
    ElMessage.warning('请选择要删除的权限')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedPermissions.value.length} 个权限吗？`,
      '批量删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    submitting.value = true
    
    // 批量删除权限
    const deletePromises = selectedPermissions.value.map(permission => 
      permissionsApi.deletePermission(permission.id)
    )
    
    await Promise.all(deletePromises)
    
    ElMessage.success('批量删除成功')
    selectedPermissions.value = []
    loadPermissions()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除失败:', error)
      ElMessage.error('批量删除失败')
    }
  } finally {
    submitting.value = false
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    submitting.value = true
    
    if (isEdit.value && currentPermission.value) {
      await permissionsApi.updatePermission(currentPermission.value.id, formData as PermissionUpdate)
      ElMessage.success('更新成功')
    } else {
      await permissionsApi.createPermission(formData)
      ElMessage.success('创建成功')
    }
    
    dialogVisible.value = false
    loadPermissions()
  } catch (error) {
    ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
  } finally {
    submitting.value = false
  }
}

const handleDialogClose = () => {
  resetForm()
}

const resetForm = () => {
  Object.assign(formData, {
    name: '',
    code: '',
    resource: '',
    action: '',
    description: ''
  })
  formRef.value?.clearValidate()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  loadPermissions()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  loadPermissions()
}

// 获取资源和操作列表
const getResourcesAndActions = async () => {
  try {
    // 从当前权限列表中提取唯一的资源和操作
    if (permissions.value.length > 0) {
      const uniqueResources = [...new Set(permissions.value.map((p: any) => p.resource))]
      const uniqueActions = [...new Set(permissions.value.map((p: any) => p.action))]
      
      resources.value = uniqueResources
      actions.value = uniqueActions
    }
  } catch (error) {
    console.error('获取资源和操作列表失败:', error)
  }
}

const loadPermissions = async () => {
  loading.value = true
  try {
    const response = await permissionsApi.getPermissions({
      page: currentPage.value,
      page_size: pageSize.value,
      search: searchForm.value.search,
      resource: searchForm.value.resource,
      action: searchForm.value.action
    })
    permissions.value = response.data.items || []
    total.value = response.data.total || 0
    
    // 更新资源和操作列表
    getResourcesAndActions()
  } catch (error) {
    ElMessage.error('加载权限列表失败')
    console.error('加载权限列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 生命周期
onMounted(() => {
  loadPermissions()
})
</script>

<style scoped>
.permission-management {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #1e293b;
  padding: 20px;
  overflow: hidden;
}

.table-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.table-wrapper {
  flex: 1;
  min-height: 0;
  max-height: calc(100vh - 300px);
  overflow: auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding: 20px;
  background: #334155;
  border-radius: 8px;
  border: 1px solid #475569;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #f1f5f9;
}

.page-description {
  font-size: 14px;
  color: #94a3b8;
  margin: 0;
}

.content-card {
  background: #334155;
  border-radius: 8px;
  padding: 24px;
  border: 1px solid #475569;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.search-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
}

.search-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.permission-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.permission-icon {
  font-size: 16px;
}

.name-text {
  font-weight: 500;
}

.resource-path {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 3px;
  color: #606266;
}

.text-muted {
  color: #64748b;
  font-size: 12px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #475569;
}

.batch-operations {
  padding: 16px 0;
  text-align: center;
}

.operation-buttons {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 16px;
}

/* 表格深色主题 */
:deep(.el-table) {
  background-color: #1e293b !important;
  color: #f1f5f9 !important;
}

:deep(.el-table th.el-table__cell) {
  background-color: #334155 !important;
  color: #f1f5f9 !important;
  border-bottom: 1px solid #475569 !important;
}

:deep(.el-table td.el-table__cell) {
  background-color: #1e293b !important;
  color: #f1f5f9 !important;
  border-bottom: 1px solid #475569 !important;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background-color: #334155 !important;
}

:deep(.el-table__body tr:hover > td) {
  background-color: #475569 !important;
}

:deep(.el-table__empty-block) {
  background-color: #1e293b !important;
  color: #94a3b8 !important;
}

/* 弹出框深色主题 */
:deep(.el-dialog) {
  background-color: #334155 !important;
  border: 1px solid #475569 !important;
}

:deep(.el-dialog__header) {
  background-color: #334155 !important;
  border-bottom: 1px solid #475569 !important;
}

:deep(.el-dialog__title) {
  color: #f1f5f9 !important;
}

:deep(.el-dialog__body) {
  background-color: #334155 !important;
  color: #f1f5f9 !important;
}

:deep(.el-form-item__label) {
  color: #f1f5f9 !important;
}

:deep(.el-input__wrapper) {
  background-color: #1e293b !important;
  border: 1px solid #475569 !important;
}

:deep(.el-input__inner) {
  background-color: #1e293b !important;
  color: #f1f5f9 !important;
}

:deep(.el-select .el-input__wrapper) {
  background-color: #1e293b !important;
}

:deep(.el-textarea__inner) {
  background-color: #1e293b !important;
  color: #f1f5f9 !important;
  border: 1px solid #475569 !important;
}

/* 下拉选择框深色主题 */
:deep(.el-select-dropdown) {
  background-color: #334155 !important;
  border: 1px solid #475569 !important;
}

:deep(.el-select-dropdown__item) {
  background-color: #334155 !important;
  color: #f1f5f9 !important;
}

:deep(.el-select-dropdown__item:hover) {
  background-color: #475569 !important;
}

:deep(.el-select-dropdown__item.selected) {
  background-color: #1e40af !important;
  color: #f1f5f9 !important;
}

/* 开关组件深色主题 */
:deep(.el-switch) {
  --el-switch-off-color: #475569 !important;
}

/* 按钮深色主题 */
:deep(.el-button--default) {
  background-color: #475569 !important;
  border-color: #475569 !important;
  color: #f1f5f9 !important;
}

:deep(.el-button--default:hover) {
  background-color: #64748b !important;
  border-color: #64748b !important;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
  }
  
  .search-bar {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-left {
    flex-direction: column;
  }
  
  .operation-buttons {
    flex-direction: column;
  }
}
</style>