<template>
  <div class="resource-management">
    <div class="header">
      <h2>资源管理</h2>
      <div class="actions">
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          新增资源
        </el-button>
        <el-button 
          type="danger" 
          :disabled="selectedResources.length === 0"
          @click="handleBatchDelete"
        >
          <el-icon><Delete /></el-icon>
          批量删除
        </el-button>
        <el-button type="warning" @click="openRoleAssignDialog">
          角色资源分配
        </el-button>
        <el-button 
          type="success" 
          :disabled="selectedResources.length === 0"
          @click="handleBatchEnable"
        >
          <el-icon><Check /></el-icon>
          批量启用
        </el-button>
        <el-button 
          type="warning" 
          :disabled="selectedResources.length === 0"
          @click="handleBatchDisable"
        >
          <el-icon><Close /></el-icon>
          批量禁用
        </el-button>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="filters">
      <el-form :model="filters" inline>
        <el-form-item label="搜索">
          <el-input
            v-model="filters.search"
            placeholder="请输入资源名称或编码"
            clearable
            @change="loadResources"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="filters.type" placeholder="请选择类型" clearable @change="loadResources">
            <el-option label="菜单" value="menu" />
            <el-option label="按钮" value="button" />
            <el-option label="API" value="api" />
          </el-select>
        </el-form-item>
        <el-form-item label="父级资源">
          <el-select 
            v-model="filters.parent_id" 
            placeholder="请选择父级资源" 
            clearable 
            @change="loadResources"
            @focus="loadParentResourcesIfNeeded"
          >
            <el-option label="无" :value="null" />
            <el-option 
              v-for="resource in parentResources" 
              :key="resource.id" 
              :label="resource.name" 
              :value="resource.id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadResources">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="resetFilters">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 表格容器 -->
    <div class="table-container">
      <!-- 资源表格 -->
      <div class="table-wrapper">
        <el-table
          v-loading="loading"
          :data="resources"
          @selection-change="handleSelectionChange"
          row-key="id"
          default-expand-all
          :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
        >
          <el-table-column type="selection" width="55" />
          <el-table-column prop="name" label="资源名称" min-width="150" />
          <el-table-column prop="code" label="资源编码" min-width="150" />
          <el-table-column prop="type" label="类型" width="80">
            <template #default="{ row }">
              <el-tag :type="getTypeTagType(row.type)">{{ getTypeLabel(row.type) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="path" label="路径" min-width="200" />
          <el-table-column prop="icon" label="图标" width="80">
            <template #default="{ row }">
              <el-icon v-if="row.icon">
                <component :is="row.icon" />
              </el-icon>
            </template>
          </el-table-column>
          <el-table-column prop="sort_order" label="排序" width="80" />
          <el-table-column prop="requires_auth" label="需要认证" width="100">
            <template #default="{ row }">
              <el-tag :type="row.requires_auth ? 'success' : 'info'">
                {{ row.requires_auth ? '是' : '否' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="requires_admin" label="需要管理员" width="120">
            <template #default="{ row }">
              <el-tag :type="row.requires_admin ? 'warning' : 'info'">
                {{ row.requires_admin ? '是' : '否' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="is_active" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'danger'">
                {{ row.is_active ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" size="small" @click="handleEdit(row)">
                编辑
              </el-button>
              <el-button 
                :type="row.is_active ? 'warning' : 'success'" 
                size="small" 
                @click="handleToggleStatus(row)"
              >
                {{ row.is_active ? '禁用' : '启用' }}
              </el-button>
              <el-button type="danger" size="small" @click="handleDelete(row)">
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 分页区域 -->
      <div style="background: #1e293b; padding: 20px; margin: 20px 0; border-radius: 4px; display: flex; justify-content: center; align-items: center; min-height: 60px;">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadResources"
          @current-change="loadResources"
        />
      </div>
    </div>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingResource ? '编辑资源' : '新增资源'"
      width="600px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="120px"
      >
        <el-form-item label="资源名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入资源名称" />
        </el-form-item>
        <el-form-item label="资源编码" prop="code">
          <el-input v-model="form.code" placeholder="请输入资源编码" />
        </el-form-item>
        <el-form-item label="资源类型" prop="type">
          <el-select v-model="form.type" placeholder="请选择资源类型">
            <el-option label="菜单" value="menu" />
            <el-option label="按钮" value="button" />
            <el-option label="API" value="api" />
          </el-select>
        </el-form-item>
        <el-form-item label="父级资源" prop="parent_id">
          <el-select 
            v-model="form.parent_id" 
            placeholder="请选择父级资源" 
            clearable
            @focus="loadParentResourcesIfNeeded"
          >
            <el-option label="无" :value="null" />
            <el-option 
              v-for="resource in parentResources" 
              :key="resource.id" 
              :label="resource.name" 
              :value="resource.id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="路径" prop="path" v-if="form.type === 'menu' || form.type === 'api'">
          <el-input v-model="form.path" placeholder="请输入路径" />
        </el-form-item>
        <el-form-item label="组件" prop="component" v-if="form.type === 'menu'">
          <el-input v-model="form.component" placeholder="请输入组件路径" />
        </el-form-item>
        <el-form-item label="图标" prop="icon" v-if="form.type === 'menu'">
          <el-input v-model="form.icon" placeholder="请输入图标名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="排序" prop="sort_order">
          <el-input-number v-model="form.sort_order" :min="0" />
        </el-form-item>
        <el-form-item label="需要认证">
          <el-switch v-model="form.requires_auth" />
        </el-form-item>
        <el-form-item label="需要管理员">
          <el-switch v-model="form.requires_admin" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ editingResource ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 角色资源分配对话框 -->
    <el-dialog
      v-model="showRoleAssignDialog"
      title="角色资源分配"
      width="800px"
      :close-on-click-modal="false"
    >
      <div class="role-assign-content">
        <div class="role-section">
          <h4>选择角色</h4>
          <el-select
            v-model="selectedRoleId"
            placeholder="请选择角色"
            style="width: 100%; margin-bottom: 20px;"
            @change="loadRoleResources"
          >
            <el-option
              v-for="role in roles"
              :key="role.id"
              :label="role.name"
              :value="role.id"
            />
          </el-select>
        </div>
        
        <div class="resources-section" v-if="selectedRoleId">
          <h4>分配资源</h4>
          <el-tree
            ref="resourceTreeRef"
            :data="resourceTreeData"
            :props="{ children: 'children', label: 'name' }"
            show-checkbox
            node-key="id"
            :default-checked-keys="roleResourceIds"
            :check-strictly="false"
          >
            <template #default="{ node, data }">
              <span class="tree-node">
                <el-icon v-if="data.icon" class="node-icon">
                  <component :is="data.icon" />
                </el-icon>
                <span>{{ data.name }}</span>
                <el-tag size="small" :type="getResourceTypeColor(data.type)">{{ data.type }}</el-tag>
              </span>
            </template>
          </el-tree>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="showRoleAssignDialog = false">取消</el-button>
        <el-button 
          type="primary" 
          :loading="assignSubmitting"
          :disabled="!selectedRoleId"
          @click="handleRoleResourceAssign"
        >
          确定分配
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import { Plus, Delete, Check, Close, Search, Refresh } from '@element-plus/icons-vue'
import { resourcesApi, type Resource, type ResourceCreate, type ResourceUpdate } from '@/api/resources'
import { rolesApi, type Role } from '@/api/roles'

// 响应式数据
const loading = ref(false)
const submitting = ref(false)
const showCreateDialog = ref(false)
const editingResource = ref<Resource | null>(null)
const selectedResources = ref<Resource[]>([])
const resources = ref<Resource[]>([])
const parentResources = ref<Resource[]>([])

// 角色资源分配相关
const showRoleAssignDialog = ref(false)
const assignSubmitting = ref(false)
const selectedRoleId = ref<number | null>(null)
const roles = ref<Role[]>([])
const resourceTreeData = ref<Resource[]>([])
const roleResourceIds = ref<number[]>([])
const resourceTreeRef = ref<InstanceType<typeof import('element-plus').ElTree>>()

// 搜索和筛选
const filters = reactive({
  search: '',
  type: '',
  parent_id: null as number | null
})

// 分页
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 表单
const formRef = ref<FormInstance>()
const form = reactive<ResourceCreate>({
  name: '',
  code: '',
  type: 'menu',
  path: '',
  component: '',
  icon: '',
  description: '',
  parent_id: null,
  sort_order: 0,
  requires_auth: true,
  requires_admin: false
})

// 表单验证规则
const formRules = {
  name: [{ required: true, message: '请输入资源名称', trigger: 'blur' }],
  code: [{ required: true, message: '请输入资源编码', trigger: 'blur' }],
  type: [{ required: true, message: '请选择资源类型', trigger: 'change' }],
  sort_order: [{ required: true, message: '请输入排序', trigger: 'blur' }]
}

// 计算属性
const getTypeTagType = (type: string) => {
  const typeMap: Record<string, string> = {
    menu: 'primary',
    button: 'success',
    api: 'warning'
  }
  return typeMap[type] || 'info'
}

const getTypeLabel = (type: string) => {
  const typeMap: Record<string, string> = {
    menu: '菜单',
    button: '按钮',
    api: 'API'
  }
  return typeMap[type] || type
}

// 方法
const loadResources = async () => {
  loading.value = true
  try {
    const params = {
      ...filters,
      page: pagination.page,
      size: pagination.size
    }
    const response = await resourcesApi.getResources(params)
    // 后端现在返回标准分页格式
    resources.value = response.data.items
    pagination.total = response.data.total
  } catch (error) {
    console.error('加载资源列表失败:', error)
    ElMessage.error('加载资源列表失败')
  } finally {
    loading.value = false
  }
}

const loadParentResources = async () => {
  try {
    const response = await resourcesApi.getResources({ 
      type: 'menu',
      page: 1,
      size: 100  // 获取足够多的菜单项
    })
    parentResources.value = response.data.items
  } catch (error) {
    console.error('加载父级资源失败:', error)
  }
}

// 懒加载父级资源
const loadParentResourcesIfNeeded = () => {
  if (parentResources.value.length === 0) {
    loadParentResources()
  }
}

// 打开角色资源分配对话框
const openRoleAssignDialog = async () => {
  try {
    // 同时加载角色和资源树数据
    await Promise.all([
      loadRoles(),
      loadResourceTree()
    ])
    showRoleAssignDialog.value = true
  } catch (error) {
    console.error('加载角色资源分配数据失败:', error)
    ElMessage.error('加载数据失败')
  }
}

const resetFilters = () => {
  filters.search = ''
  filters.type = ''
  filters.parent_id = null
  pagination.page = 1
  loadResources()
}

const handleSelectionChange = (selection: Resource[]) => {
  selectedResources.value = selection
}

const handleEdit = (resource: Resource) => {
  editingResource.value = resource
  Object.assign(form, resource)
  showCreateDialog.value = true
}

const handleDelete = async (resource: Resource) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除资源 "${resource.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await resourcesApi.deleteResource(resource.id)
    ElMessage.success('删除成功')
    loadResources()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleToggleStatus = async (resource: Resource) => {
  try {
    const updateData: ResourceUpdate = {
      is_active: !resource.is_active
    }
    await resourcesApi.updateResource(resource.id, updateData)
    ElMessage.success(`${resource.is_active ? '禁用' : '启用'}成功`)
    loadResources()
  } catch (error) {
    ElMessage.error(`${resource.is_active ? '禁用' : '启用'}失败`)
  }
}

const handleBatchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedResources.value.length} 个资源吗？`,
      '确认批量删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const resourceIds = selectedResources.value.map(r => r.id)
    await resourcesApi.batchDeleteResources(resourceIds)
    ElMessage.success('批量删除成功')
    loadResources()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

const handleBatchEnable = async () => {
  try {
    const resourceIds = selectedResources.value.map(r => r.id)
    await resourcesApi.batchUpdateResourceStatus(resourceIds, true)
    ElMessage.success('批量启用成功')
    loadResources()
  } catch (error) {
    ElMessage.error('批量启用失败')
  }
}

const handleBatchDisable = async () => {
  try {
    const resourceIds = selectedResources.value.map(r => r.id)
    await resourcesApi.batchUpdateResourceStatus(resourceIds, false)
    ElMessage.success('批量禁用成功')
    loadResources()
  } catch (error) {
    ElMessage.error('批量禁用失败')
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    submitting.value = true
    
    if (editingResource.value) {
      // 更新资源
      const updateData: ResourceUpdate = { ...form }
      await resourcesApi.updateResource(editingResource.value.id, updateData)
      ElMessage.success('更新成功')
    } else {
      // 创建资源
      await resourcesApi.createResource(form)
      ElMessage.success('创建成功')
    }
    
    showCreateDialog.value = false
    loadResources()
  } catch (error) {
    ElMessage.error(editingResource.value ? '更新失败' : '创建失败')
  } finally {
    submitting.value = false
  }
}

const resetForm = () => {
  editingResource.value = null
  Object.assign(form, {
    name: '',
    code: '',
    type: 'menu',
    path: '',
    component: '',
    icon: '',
    description: '',
    parent_id: null,
    sort_order: 0,
    requires_auth: true,
    requires_admin: false
  })
  formRef.value?.resetFields()
}

// 角色资源分配相关方法
const loadRoles = async () => {
  try {
    const response = await rolesApi.getRoles()
    roles.value = response.data.items
  } catch (error) {
    ElMessage.error('加载角色列表失败')
  }
}

const loadResourceTree = async () => {
  try {
    const response = await resourcesApi.getResources({
      page: 1,
      size: 1000  // 获取所有资源用于树形结构
    })
    resourceTreeData.value = response.data.items
  } catch (error) {
    ElMessage.error('加载资源树失败')
  }
}

const loadRoleResources = async () => {
  if (!selectedRoleId.value) return
  
  try {
    const response = await rolesApi.getRoleResources(selectedRoleId.value)
    roleResourceIds.value = response.data.map((r: Resource) => r.id)
  } catch (error) {
    ElMessage.error('加载角色资源失败')
  }
}

const handleRoleResourceAssign = async () => {
  if (!selectedRoleId.value || !resourceTreeRef.value) return
  
  try {
    assignSubmitting.value = true
    const checkedKeys = resourceTreeRef.value.getCheckedKeys()
    const halfCheckedKeys = resourceTreeRef.value.getHalfCheckedKeys()
    const resourceIds = [...checkedKeys, ...halfCheckedKeys] as number[]
    
    await rolesApi.assignRoleResources(selectedRoleId.value, resourceIds)
    ElMessage.success('角色资源分配成功')
    showRoleAssignDialog.value = false
  } catch (error) {
    ElMessage.error('角色资源分配失败')
  } finally {
    assignSubmitting.value = false
  }
}

const getResourceTypeColor = (type: string) => {
  const colorMap: Record<string, string> = {
    menu: 'primary',
    button: 'success',
    api: 'warning'
  }
  return colorMap[type] || 'info'
}

// 生命周期
onMounted(() => {
  loadResources()
  // 只在需要时才加载父级资源和资源树
})
</script>

<style scoped>
.resource-management {
  height: 100vh;
  display: flex;
  flex-direction: column;
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
  max-height: calc(100vh - 360px);
  overflow: auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h2 {
  margin: 0;
  color: #e2e8f0;
  font-size: 20px;
  font-weight: 600;
}

.actions {
  display: flex;
  gap: 10px;
}

.filters {
  background: #1e293b;
  border: 1px solid #334155;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #334155;
}

.role-assign-content {
  max-height: 500px;
  overflow-y: auto;
}

.role-section h4,
.resources-section h4 {
  margin: 0 0 10px 0;
  color: #e2e8f0;
  font-size: 14px;
  font-weight: 600;
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.node-icon {
  font-size: 16px;
}

.el-tree {
  max-height: 300px;
  overflow-y: auto;
}

/* Element Plus 深色主题覆盖 */
:deep(.el-table) {
  background-color: #0f172a;
  color: #e2e8f0;
}

:deep(.el-table th.el-table__cell) {
  background-color: #0f172a;
  color: #e2e8f0;
  border-bottom: 1px solid #334155;
}

:deep(.el-table td.el-table__cell) {
  border-bottom: 1px solid #334155;
  background-color: #0f172a;
  color: #e2e8f0;
}

:deep(.el-table__body tr) {
  background-color: #0f172a;
}

:deep(.el-table tr:hover > td) {
  background-color: #1e293b !important;
}

:deep(.el-input__wrapper) {
  background-color: #0f172a;
  border: 1px solid #334155;
  color: #e2e8f0;
}

:deep(.el-input__inner) {
  color: #e2e8f0;
}

:deep(.el-input__wrapper:hover) {
  border-color: #6366f1;
}

:deep(.el-input__wrapper.is-focus) {
  border-color: #6366f1;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
}

:deep(.el-select .el-input__wrapper) {
  background-color: #0f172a;
  border: 1px solid #334155;
}

:deep(.el-pagination) {
  color: #e2e8f0;
}

:deep(.el-pagination .el-pager li) {
  background-color: #1e293b;
  color: #e2e8f0;
  border: 1px solid #334155;
}

:deep(.el-pagination .el-pager li:hover) {
  color: #6366f1;
}

:deep(.el-pagination .el-pager li.is-active) {
  background-color: #6366f1;
  color: white;
}

:deep(.el-pagination button) {
  background-color: #1e293b;
  color: #e2e8f0;
  border: 1px solid #334155;
}

:deep(.el-pagination button:hover) {
  color: #6366f1;
}

:deep(.el-tag) {
  background-color: #1e293b;
  border: 1px solid #334155;
  color: #e2e8f0;
}

:deep(.el-tag.el-tag--success) {
  background-color: rgba(34, 197, 94, 0.2);
  border-color: #22c55e;
  color: #22c55e;
}

:deep(.el-tag.el-tag--warning) {
  background-color: rgba(245, 158, 11, 0.2);
  border-color: #f59e0b;
  color: #f59e0b;
}

:deep(.el-tag.el-tag--danger) {
  background-color: rgba(239, 68, 68, 0.2);
  border-color: #ef4444;
  color: #ef4444;
}

:deep(.el-tag.el-tag--primary) {
  background-color: rgba(99, 102, 241, 0.2);
  border-color: #6366f1;
  color: #6366f1;
}

:deep(.el-tag.el-tag--info) {
  background-color: rgba(148, 163, 184, 0.2);
  border-color: #94a3b8;
  color: #94a3b8;
}

/* 弹出框样式 */
:deep(.el-dialog) {
  background-color: #1e293b;
  border: 1px solid #334155;
}

:deep(.el-dialog__header) {
  background-color: #1e293b;
  border-bottom: 1px solid #334155;
  padding: 20px 24px 16px;
}

:deep(.el-dialog__title) {
  color: #e2e8f0;
  font-size: 18px;
  font-weight: 600;
}

:deep(.el-dialog__headerbtn .el-dialog__close) {
  color: #94a3b8;
}

:deep(.el-dialog__headerbtn .el-dialog__close:hover) {
  color: #e2e8f0;
}

:deep(.el-dialog__body) {
  background-color: #1e293b;
  color: #e2e8f0;
  padding: 24px;
}

:deep(.el-dialog__footer) {
  background-color: #1e293b;
  border-top: 1px solid #334155;
  padding: 16px 24px 20px;
}

:deep(.el-form-item__label) {
  color: #e2e8f0;
}

:deep(.el-form-item__error) {
  color: #ef4444;
}

:deep(.el-switch.is-checked .el-switch__core) {
  background-color: #6366f1;
}

:deep(.el-switch__core) {
  background-color: #374151;
  border-color: #374151;
}

:deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background-color: #6366f1;
  border-color: #6366f1;
}

:deep(.el-checkbox__inner) {
  background-color: #374151;
  border-color: #6b7280;
}

:deep(.el-checkbox__label) {
  color: #e2e8f0;
}

:deep(.el-tree) {
  background-color: #0f172a;
  color: #e2e8f0;
}

:deep(.el-tree-node__content) {
  background-color: #0f172a;
  color: #e2e8f0;
}

:deep(.el-tree-node__content:hover) {
  background-color: #1e293b;
}

:deep(.el-tree-node.is-current > .el-tree-node__content) {
  background-color: #1e293b;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .header {
    flex-direction: column;
    gap: 16px;
  }
  
  .actions {
    flex-wrap: wrap;
    justify-content: center;
  }
  
  .filters {
    padding: 16px;
  }
}
</style>