<template>
  <div class="department-management">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">
          <el-icon><OfficeBuilding /></el-icon>
          部门管理
        </h2>
        <p class="page-description">管理组织架构和部门层级关系</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          新增部门
        </el-button>
      </div>
    </div>

    <div class="content-card">
      <!-- 搜索栏 -->
      <div class="search-bar">
        <div class="search-left">
          <el-input
            v-model="searchQuery"
            placeholder="搜索部门名称或描述"
            style="width: 300px"
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          
          <el-button @click="expandAll">
            <el-icon><Expand /></el-icon>
            展开全部
          </el-button>
          
          <el-button @click="collapseAll">
            <el-icon><Fold /></el-icon>
            收起全部
          </el-button>
        </div>
        
        <div class="search-right">
          <el-button @click="handleRefresh">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>

      <!-- 部门树形表格 -->
      <el-table
        ref="tableRef"
        v-loading="loading"
        :data="filteredDepartments"
        style="width: 100%"
        max-height="500px"
        row-key="id"
        :tree-props="{ children: 'children', hasChildren: 'hasChildren' }"
        :default-expand-all="false"
      >
        <el-table-column prop="name" label="部门名称" width="300">
          <template #default="{ row }">
            <div class="department-name">
              <el-icon class="department-icon">
                <OfficeBuilding v-if="row.level === 1" />
                <Collection v-else-if="row.level === 2" />
                <Folder v-else />
              </el-icon>
              <span class="name-text">{{ row.name }}</span>
              <el-tag v-if="row.is_active" type="success" size="small">启用</el-tag>
              <el-tag v-else type="danger" size="small">禁用</el-tag>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="code" label="部门编码" width="150" />
        
        <el-table-column prop="description" label="描述" min-width="200">
          <template #default="{ row }">
            <span v-if="row.description">{{ row.description }}</span>
            <span v-else class="text-muted">暂无描述</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="manager" label="负责人" width="120">
          <template #default="{ row }">
            <div v-if="row.manager" class="manager-info">
              <el-avatar :size="24" :src="row.manager.avatar">
                {{ row.manager.username && row.manager.username.length > 0 ? row.manager.username.charAt(0).toUpperCase() : '?' }}
              </el-avatar>
              <span class="manager-name">{{ row.manager.username || '未知用户' }}</span>
            </div>
            <span v-else class="text-muted">未设置</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="member_count" label="成员数量" width="100" align="center">
          <template #default="{ row }">
            <el-tag type="info" size="small">{{ row.member_count || 0 }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="sort_order" label="排序" width="80" align="center" />
        
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="320" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click="handleEdit(row)"
            >
              编辑
            </el-button>
            <el-button
              type="success"
              size="small"
              @click="handleAddChild(row)"
            >
              添加子部门
            </el-button>
            <el-button
              type="warning"
              size="small"
              @click="handleMembers(row)"
            >
              成员管理
            </el-button>
            <el-button
              type="danger"
              size="small"
              @click="handleDelete(row)"
              :disabled="row.children && row.children.length > 0"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 部门表单对话框 -->
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
        <el-form-item label="上级部门" prop="parent_id">
          <el-tree-select
            v-model="formData.parent_id"
            :data="departmentTreeOptions"
            :props="{ label: 'name', value: 'id', children: 'children' }"
            placeholder="请选择上级部门（可选）"
            style="width: 100%"
            clearable
            check-strictly
          />
        </el-form-item>
        
        <el-form-item label="部门名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入部门名称" />
        </el-form-item>
        
        <el-form-item label="部门编码" prop="code">
          <el-input v-model="formData.code" placeholder="请输入部门编码" />
        </el-form-item>
        
        <el-form-item label="部门描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入部门描述"
          />
        </el-form-item>
        
        <el-form-item label="负责人" prop="manager_id">
          <el-select
            v-model="formData.manager_id"
            placeholder="请选择负责人"
            style="width: 100%"
            clearable
            filterable
          >
            <el-option
              v-for="user in users"
              :key="user.id"
              :label="user.username"
              :value="user.id"
            >
              <div class="user-option">
                <el-avatar :size="20" :src="user.avatar">
                  {{ user.username && user.username.length > 0 ? user.username.charAt(0).toUpperCase() : '?' }}
                </el-avatar>
                <span>{{ user.username || '未知用户' }}</span>
                <span class="user-email">{{ user.email }}</span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="排序" prop="sort_order">
          <el-input-number
            v-model="formData.sort_order"
            :min="0"
            :max="9999"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="状态">
          <el-switch v-model="formData.is_active" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 成员管理对话框 -->
    <el-dialog
      v-model="memberDialogVisible"
      title="成员管理"
      width="800px"
    >
      <div class="member-management">
        <div class="member-header">
          <h4>{{ currentDepartment?.name }} - 成员列表</h4>
          <el-button type="primary" size="small" @click="handleAddMember">
            <el-icon><Plus /></el-icon>
            添加成员
          </el-button>
        </div>
        
        <el-table
          :data="departmentMembers"
          style="width: 100%"
          max-height="400px"
        >
          <el-table-column prop="username" label="用户名" width="120">
            <template #default="{ row }">
              <div class="user-info">
                <el-avatar :size="24" :src="row.avatar">
                  {{ row.username && row.username.length > 0 ? row.username.charAt(0).toUpperCase() : '?' }}
                </el-avatar>
                <span>{{ row.username || '未知用户' }}</span>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column prop="email" label="邮箱" width="200" />
          
          <el-table-column prop="roles" label="角色" width="150">
            <template #default="{ row }">
              <el-tag
                v-for="role in row.roles"
                :key="role.id"
                size="small"
                style="margin-right: 4px"
              >
                {{ role.name }}
              </el-tag>
            </template>
          </el-table-column>
          
          <el-table-column prop="join_date" label="加入时间" width="160">
            <template #default="{ row }">
              {{ formatDateTime(row.join_date) }}
            </template>
          </el-table-column>
          
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button
                type="danger"
                size="small"
                @click="handleRemoveMember(row)"
              >
                移除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      
      <template #footer>
        <el-button @click="memberDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 添加成员对话框 -->
    <el-dialog
      v-model="addMemberDialogVisible"
      title="添加成员"
      width="500px"
    >
      <el-select
        v-model="selectedUsers"
        multiple
        placeholder="请选择要添加的用户"
        style="width: 100%"
        filterable
      >
        <el-option
          v-for="user in availableUsers"
          :key="user.id"
          :label="user.username"
          :value="user.id"
        >
          <div class="user-option">
            <el-avatar :size="20" :src="user.avatar">
              {{ user.username && user.username.length > 0 ? user.username.charAt(0).toUpperCase() : '?' }}
            </el-avatar>
            <span>{{ user.username || '未知用户' }}</span>
            <span class="user-email">{{ user.email }}</span>
          </div>
        </el-option>
      </el-select>
      
      <template #footer>
        <el-button @click="addMemberDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAddMemberSubmit" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import {
  OfficeBuilding,
  Collection,
  Folder,
  Plus,
  Search,
  Refresh,
  Expand,
  Fold
} from '@element-plus/icons-vue'
import { formatDateTime } from '@/utils/date'
import { departmentsApi, usersApi } from '@/api'
import { userDepartmentsApi, type UserDepartmentCreate } from '@/api/userDepartments'
import type { Department, DepartmentCreate, DepartmentUpdate } from '@/api/departments'

// 响应式数据
const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const memberDialogVisible = ref(false)
const addMemberDialogVisible = ref(false)
const isEdit = ref(false)
const currentDepartment = ref<Department | null>(null)
const selectedUsers = ref<number[]>([])

// 搜索
const searchQuery = ref('')

// 表单
const formRef = ref<FormInstance>()
const tableRef = ref()
const formData = reactive<DepartmentCreate>({
  parent_id: null,
  name: '',
  code: '',
  description: '',
  manager_id: null,
  sort_order: 0,
  is_active: true
})

// 响应式数据
const departments = ref<Department[]>([])
const users = ref<any[]>([])

const departmentMembers = ref<any[]>([])
const availableUsers = ref<any[]>([])

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入部门名称', trigger: 'blur' },
    { min: 2, max: 50, message: '部门名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入部门编码', trigger: 'blur' },
    { pattern: /^[A-Z0-9_]+$/, message: '部门编码只能包含大写字母、数字和下划线', trigger: 'blur' }
  ]
}

// 计算属性
const dialogTitle = computed(() => isEdit.value ? '编辑部门' : '新增部门')

const filteredDepartments = computed(() => {
  if (!searchQuery.value) return departments.value
  
  const filterTree = (nodes: any[]) => {
    return nodes.filter(node => {
      const matchesSearch = node.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
                           (node.description && node.description.toLowerCase().includes(searchQuery.value.toLowerCase()))
      
      if (node.children) {
        node.children = filterTree(node.children)
        return matchesSearch || node.children.length > 0
      }
      
      return matchesSearch
    })
  }
  
  return filterTree(JSON.parse(JSON.stringify(departments.value)))
})

const departmentTreeOptions = computed(() => {
  const buildOptions = (nodes: any[], excludeId?: number) => {
    return nodes.filter(node => node.id !== excludeId).map(node => ({
      id: node.id,
      name: node.name,
      children: node.children ? buildOptions(node.children, excludeId) : []
    }))
  }
  
  return buildOptions(departments.value, isEdit.value ? currentDepartment.value?.id : undefined)
})

// 方法
const handleSearch = () => {
  // 搜索逻辑已在计算属性中实现
}

const handleRefresh = () => {
  searchQuery.value = ''
  loadDepartments()
}

const expandAll = () => {
  // 展开所有节点
  if (tableRef.value) {
    const expandRecursively = (data: any[]) => {
      data.forEach(item => {
        tableRef.value.toggleRowExpansion(item, true)
        if (item.children) {
          expandRecursively(item.children)
        }
      })
    }
    expandRecursively(departments.value)
  }
}

const collapseAll = () => {
  // 收起所有节点
  if (tableRef.value) {
    const collapseRecursively = (data: any[]) => {
      data.forEach(item => {
        tableRef.value.toggleRowExpansion(item, false)
        if (item.children) {
          collapseRecursively(item.children)
        }
      })
    }
    collapseRecursively(departments.value)
  }
}

const handleCreate = () => {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  isEdit.value = true
  Object.assign(formData, {
    parent_id: row.parent_id,
    name: row.name,
    code: row.code,
    description: row.description,
    manager_id: row.manager?.id,
    sort_order: row.sort_order,
    is_active: row.is_active
  })
  currentDepartment.value = row
  dialogVisible.value = true
}

const handleAddChild = (row: any) => {
  isEdit.value = false
  resetForm()
  formData.parent_id = row.id
  dialogVisible.value = true
}

const handleDelete = async (row: any) => {
  if (row.children && row.children.length > 0) {
    ElMessage.warning('请先删除子部门')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除部门 "${row.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await departmentsApi.deleteDepartmentById(row.id)
    
    ElMessage.success('删除成功')
    loadDepartments()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error(error.message || '删除失败')
    }
  }
}

const handleMembers = (row: Department) => {
  currentDepartment.value = row
  loadDepartmentMembers(row.id)
  memberDialogVisible.value = true
}

const handleAddMember = () => {
  loadAvailableUsers()
  addMemberDialogVisible.value = true
}

const handleRemoveMember = async (user: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要将 "${user.user_name || user.username}" 从部门中移除吗？`,
      '确认移除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 调用API移除用户
    await userDepartmentsApi.removeUserFromDepartment(user.user_id || user.id, currentDepartment.value.id)
    ElMessage.success('移除成功')
    loadDepartmentMembers(currentDepartment.value.id)
  } catch (error: any) {
    if (error.response) {
      ElMessage.error(error.response.data.detail || '移除失败')
    }
    // 用户取消或其他错误
  }
}

const handleAddMemberSubmit = async () => {
  if (selectedUsers.value.length === 0) {
    ElMessage.warning('请选择要添加的用户')
    return
  }
  
  try {
    submitting.value = true
    
    // 批量添加用户到部门
    const promises = selectedUsers.value.map(userId => {
      const data: UserDepartmentCreate = {
        user_id: userId,
        department_id: currentDepartment.value.id,
        is_primary: false,
        is_active: true
      }
      return userDepartmentsApi.createUserDepartment(data)
    })
    
    await Promise.all(promises)
    
    ElMessage.success('添加成功')
    addMemberDialogVisible.value = false
    selectedUsers.value = []
    loadDepartmentMembers(currentDepartment.value.id)
  } catch (error: any) {
    console.error('添加成员失败:', error)
    if (error.response) {
      ElMessage.error(error.response.data.detail || '添加失败')
    } else {
      ElMessage.error('添加失败')
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
    
    const departmentData: DepartmentCreate | DepartmentUpdate = {
      name: formData.name,
      code: formData.code,
      description: formData.description,
      parent_id: formData.parent_id || null,
      manager_id: formData.manager_id || null,
      is_active: formData.is_active,
      sort_order: formData.sort_order
    }
    
    if (isEdit.value && currentDepartment.value) {
      await departmentsApi.updateDepartmentById(currentDepartment.value.id, departmentData)
      ElMessage.success('更新成功')
    } else {
      await departmentsApi.createDepartment(departmentData as DepartmentCreate)
      ElMessage.success('创建成功')
    }
    
    dialogVisible.value = false
    loadDepartments()
  } catch (error: any) {
    if (error !== false) { // 不是表单验证错误
      console.error('提交失败:', error)
      ElMessage.error(error.message || (isEdit.value ? '更新失败' : '创建失败'))
    }
  } finally {
    submitting.value = false
  }
}

const handleDialogClose = () => {
  resetForm()
}

const resetForm = () => {
  Object.assign(formData, {
    parent_id: null,
    name: '',
    code: '',
    description: '',
    manager_id: null,
    sort_order: 0,
    is_active: true
  })
  formRef.value?.clearValidate()
}

const loadDepartments = async () => {
  loading.value = true
  try {
    const response = await departmentsApi.getDepartmentTree()
    departments.value = response.data
    
    // ElMessage.success('部门数据加载成功')
  } catch (error: any) {
    console.error('加载部门数据失败:', error)
    ElMessage.error(error.message || '加载部门数据失败')
  } finally {
    loading.value = false
  }
}

const loadUsers = async () => {
  try {
    const response = await usersApi.getUsers({ limit: 1000 })
    users.value = response.data.users
  } catch (error: any) {
    console.error('加载用户列表失败:', error)
  }
}

const loadDepartmentMembers = async (departmentId: number) => {
  try {
    const response = await userDepartmentsApi.getDepartmentUsers(departmentId)
    // 确保response和response.data存在
    if (response && response.data && response.data.users) {
      // 转换数据格式以适配前端显示
      departmentMembers.value = response.data.users.map(user => ({
        id: user.user_id || user.id,
        user_id: user.user_id || user.id,
        username: user.user_name || user.username || '',
        user_name: user.user_name || user.username || '',
        email: user.user_email || user.email || '',
        avatar: user.avatar || '',
        roles: user.roles || [], // 角色信息需要从其他接口获取
        join_date: user.created_at,
        is_primary: user.is_primary || false,
        is_active: user.is_active !== false
      }))
    } else {
      departmentMembers.value = []
    }
  } catch (error: any) {
    console.error('加载部门成员失败:', error)
    departmentMembers.value = []
    ElMessage.error(error.response?.data?.detail || '加载部门成员失败')
  }
}

const loadAvailableUsers = async () => {
  try {
    // 获取所有用户
    const allUsersResponse = await usersApi.getUsers({ limit: 1000 })
    // 获取已有部门关联的用户ID列表
    const usersWithDepartmentsResponse = await userDepartmentsApi.getUsersWithDepartments(true)
    
    if (allUsersResponse && allUsersResponse.data && allUsersResponse.data.users) {
      const allUsers = allUsersResponse.data.users
      const usersWithDepartments = usersWithDepartmentsResponse?.data?.user_ids || []
      
      // 过滤掉已有部门关联的用户（确保一个用户只能属于一个部门）
      availableUsers.value = allUsers.filter(user => 
        !usersWithDepartments.includes(user.id)
      )
    } else {
      availableUsers.value = []
    }
  } catch (error: any) {
    console.error('加载可用用户失败:', error)
    availableUsers.value = []
    ElMessage.error(error.response?.data?.detail || '加载可用用户失败')
  }
}

// 生命周期
onMounted(() => {
  loadDepartments()
  loadUsers()
})
</script>

<style scoped>
.department-management {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #1e293b;
  padding: 20px;
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

.department-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.department-icon {
  color: #409eff;
}

.name-text {
  font-weight: 500;
}

.manager-info {
  display: flex;
  align-items: center;
  gap: 6px;
}

.manager-name {
  font-size: 12px;
}

.text-muted {
  color: #64748b;
  font-size: 12px;
}

.member-management {
  padding: 16px 0;
}

.member-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.member-header h4 {
  margin: 0;
  color: #f1f5f9;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-email {
  font-size: 12px;
  color: #909399;
  margin-left: auto;
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
}
</style>