<template>
  <div class="user-management">
    <div class="page-header">
      <h2>用户管理</h2>
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon>
        新增用户
      </el-button>
    </div>

    <el-card class="content-card" shadow="never">
      <!-- 搜索和筛选 -->
      <div class="search-bar">
        <div class="search-left">
          <el-input
            v-model="searchQuery"
            placeholder="搜索用户名、邮箱或手机号"
            style="width: 300px"
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          
          <el-select
            v-model="filterDepartment"
            placeholder="选择部门"
            style="width: 200px; margin-left: 16px"
            clearable
            @change="handleFilter"
          >
            <el-option
              v-for="dept in departments"
              :key="dept.id"
              :label="dept.name"
              :value="dept.id"
            />
          </el-select>
          

        </div>
        
        <div class="search-right">
          <el-button @click="handleRefresh">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>

      <!-- 用户表格 -->
      <el-table
        v-loading="loading"
        :data="filteredUsers"
        style="width: 100%"
        max-height="500px"
        row-key="id"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        
        <el-table-column prop="username" label="用户名" width="120">
          <template #default="{ row }">
            <div class="user-info">
              <el-avatar :size="32" :src="row.avatar">
                {{ row.username && row.username.length > 0 ? row.username.charAt(0).toUpperCase() : '?' }}
              </el-avatar>
              <span class="username">{{ row.username }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="full_name" label="姓名" width="120">
          <template #default="{ row }">
            <span>{{ row.full_name || '-' }}</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="email" label="邮箱" width="200" />
        
        <el-table-column prop="department" label="部门" width="150">
          <template #default="{ row }">
            <span>{{ getDepartmentName(row.department_id) }}</span>
          </template>
        </el-table-column>
        

        
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_active"
              @change="handleStatusChange(row)"
            />
          </template>
        </el-table-column>
        
        <el-table-column prop="last_login_at" label="最后登录" width="160">
          <template #default="{ row }">
            <span v-if="row.last_login_at">
              {{ formatDateTime(row.last_login_at) }}
            </span>
            <span v-else class="text-muted">从未登录</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
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
    </el-card>

    <!-- 用户表单对话框 -->
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
        <el-form-item label="用户名" prop="username">
          <el-input v-model="formData.username" placeholder="请输入用户名" />
        </el-form-item>
        
        <el-form-item label="姓名" prop="full_name">
          <el-input v-model="formData.full_name" placeholder="请输入姓名" />
        </el-form-item>
        
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="formData.email" placeholder="请输入邮箱" />
        </el-form-item>
        
        <el-form-item label="密码" prop="password" v-if="!isEdit">
          <el-input
            v-model="formData.password"
            type="password"
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="部门" prop="department_id">
          <el-select
            v-model="formData.department_id"
            placeholder="请选择部门"
            style="width: 100%"
            clearable
          >
            <el-option
              v-for="dept in departments"
              :key="dept.id"
              :label="dept.name"
              :value="dept.id"
            />
          </el-select>
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


  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import {
  User,
  Plus,
  Search,
  Refresh
} from '@element-plus/icons-vue'
import { formatDateTime } from '@/utils/date'
import { usersApi, departmentsApi, rolesApi, userDepartmentsApi } from '@/api'
import type { User as UserType, Department, Role } from '@/types'

// 响应式数据
const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const currentUser = ref<UserType | null>(null)
const selectedUsers = ref<UserType[]>([])

// 搜索和筛选
const searchQuery = ref('')
const filterDepartment = ref<number | null>(null)
const filterStatus = ref('')

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 表单
const formRef = ref<FormInstance>()
const formData = reactive({
  username: '',
  email: '',
  password: '',
  full_name: '',
  department_id: null as number | null,
  is_active: true
})

// 数据
const users = ref<UserType[]>([])
const departments = ref<Department[]>([])
const roles = ref<Role[]>([])

// 表单验证规则
const formRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 20, message: '用户名长度在 2 到 20 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少 6 个字符', trigger: 'blur' }
  ],
  full_name: [
    { max: 50, message: '姓名长度不能超过 50 个字符', trigger: 'blur' }
  ]
}

// 计算属性
const dialogTitle = computed(() => {
  return isEdit.value ? '编辑用户' : '新增用户'
})

const filteredUsers = computed(() => {
  let result = users.value
  
  // 搜索过滤
  if (searchQuery.value) {
    result = result.filter(user => 
      user.username.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      user.email.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      (user.full_name && user.full_name.toLowerCase().includes(searchQuery.value.toLowerCase()))
    )
  }
  
  // 部门过滤
  if (filterDepartment.value) {
    result = result.filter(user => user.department_id === filterDepartment.value)
  }
  
  return result
})

// 方法
const getDepartmentName = (departmentId: number | null) => {
  if (!departmentId) return '-'
  const department = departments.value.find(d => d.id === departmentId)
  return department?.name || '-'
}

const handleSearch = () => {
  // 搜索逻辑已在计算属性中处理
}

const handleFilter = () => {
  // 筛选逻辑已在计算属性中处理
}

const handleRefresh = async () => {
  searchQuery.value = ''
  filterDepartment.value = null
  filterStatus.value = ''
  await loadUsers()
}

const handleSelectionChange = (selection: UserType[]) => {
  selectedUsers.value = selection
}

const handleCreate = () => {
  isEdit.value = false
  currentUser.value = null
  resetForm()
  dialogVisible.value = true
}

const handleEdit = async (user: UserType) => {
  isEdit.value = true
  currentUser.value = user
  
  // 获取用户的部门信息
  let userDepartmentId = user.department_id
  if (!userDepartmentId && user.id) {
    try {
      const response = await userDepartmentsApi.getUserDepartments(user.id, true)
      const primaryDept = response.data.departments?.find(dept => dept.is_primary)
      if (primaryDept) {
        userDepartmentId = primaryDept.department_id
      } else if (response.data.departments?.length > 0) {
        // 如果没有主要部门，使用第一个部门
        userDepartmentId = response.data.departments[0].department_id
      }
    } catch (error) {
      console.warn('获取用户部门信息失败:', error)
    }
  }
  
  // 填充表单数据
  Object.assign(formData, {
    username: user.username,
    email: user.email,
    password: '', // 编辑时密码为空
    full_name: user.full_name || '',
    department_id: userDepartmentId,
    is_active: user.is_active
  })
  
  dialogVisible.value = true
}

const handleDelete = async (user: UserType) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${user.username}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    loading.value = true
    await usersApi.deleteUserById(user.id)
    ElMessage.success('删除成功')
    await loadUsers()
  } catch (error: any) {
    if (error.message !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  } finally {
    loading.value = false
  }
}

const handleStatusChange = async (user: UserType) => {
  try {
    await usersApi.updateUserStatus(user.id, user.is_active)
    ElMessage.success(`用户状态已${user.is_active ? '启用' : '禁用'}`)
  } catch (error: any) {
    // 如果失败，恢复原状态
    user.is_active = !user.is_active
    ElMessage.error(error.message || '状态更新失败')
  }
}



const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    submitting.value = true
    
    if (isEdit.value && currentUser.value) {
      // 更新用户基本信息
      const updateData = { ...formData }
      if (!updateData.password) {
        delete updateData.password // 如果密码为空，不更新密码
      }
      // 移除部门ID，因为部门关联通过单独的API处理
      const departmentId = updateData.department_id
      delete updateData.department_id
      
      await usersApi.updateUserById(currentUser.value.id, updateData)
      
      // 处理部门关联更新
      if (departmentId !== currentUser.value.department_id) {
        try {
          // 获取用户当前的部门关联
          const currentDepts = await userDepartmentsApi.getUserDepartments(currentUser.value.id, true)
          
          // 移除当前的主要部门关联
          if (currentDepts.data.departments?.length > 0) {
            const primaryDept = currentDepts.data.departments.find(dept => dept.is_primary)
            if (primaryDept) {
              await userDepartmentsApi.removeUserFromDepartment(currentUser.value.id, primaryDept.department_id)
            }
          }
          
          // 如果选择了新部门，创建新的关联
          if (departmentId) {
            await userDepartmentsApi.createUserDepartment({
              user_id: currentUser.value.id,
              department_id: departmentId,
              is_primary: true,
              is_active: true
            })
          }
        } catch (deptError: any) {
          console.warn('部门关联更新失败:', deptError)
          ElMessage.warning('用户信息更新成功，但部门关联更新失败')
        }
      }
      
      ElMessage.success('更新成功')
    } else {
      // 创建用户
      const createData = { ...formData }
      const departmentId = createData.department_id
      delete createData.department_id
      
      const newUser = await usersApi.createUser(createData)
      
      // 如果选择了部门，创建部门关联
      if (departmentId && newUser.data.id) {
        try {
          await userDepartmentsApi.createUserDepartment({
            user_id: newUser.data.id,
            department_id: departmentId,
            is_primary: true,
            is_active: true
          })
        } catch (deptError: any) {
          console.warn('部门关联创建失败:', deptError)
          ElMessage.warning('用户创建成功，但部门关联创建失败')
        }
      }
      
      ElMessage.success('创建成功')
    }
    
    dialogVisible.value = false
    await loadUsers()
  } catch (error: any) {
    ElMessage.error(error.message || '操作失败')
  } finally {
    submitting.value = false
  }
}



const handleDialogClose = () => {
  resetForm()
}

const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
  Object.assign(formData, {
    username: '',
    email: '',
    password: '',
    full_name: '',
    department_id: null,
    is_active: true
  })
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  loadUsers()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  loadUsers()
}

const loadUsers = async () => {
  try {
    loading.value = true
    const response = await usersApi.getUsers({
      page: currentPage.value,
      size: pageSize.value,
      search: searchQuery.value,
      department_id: filterDepartment.value,
      is_active: filterStatus.value !== '' ? filterStatus.value : undefined
    })
    // 修正数据解析：API返回的是{users: [...], total: ...}格式
    users.value = response.data.users || response.data.items || []
    total.value = response.data.total || 0
  } catch (error: any) {
    console.error('加载用户列表失败:', error)
    ElMessage.error(error.message || '加载用户列表失败')
  } finally {
    loading.value = false
  }
}

const loadDepartments = async () => {
  try {
    const response = await departmentsApi.getDepartments()
    // 根据API响应格式，直接使用response.data
    departments.value = response.data || []
  } catch (error: any) {
    console.error('加载部门列表失败:', error)
  }
}

// 生命周期
onMounted(async () => {
  await Promise.all([
    loadUsers(),
    loadDepartments()
  ])
})
</script>

<style scoped>
.user-management {
  height: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  color: #e2e8f0;
  font-size: 20px;
  font-weight: 600;
}

.content-card {
  border-radius: 8px;
  background: #1e293b;
  border: 1px solid #334155;
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
  flex-wrap: wrap;
  gap: 16px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.username {
  font-weight: 500;
}

.roles-container {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.text-muted {
  color: #94a3b8;
  font-size: 12px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #334155;
}

.role-assignment {
  padding: 16px 0;
}

.assignment-user {
  margin-bottom: 16px;
  font-size: 14px;
  color: #e2e8f0;
}

.role-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.role-item {
  margin: 0;
  padding: 12px;
  border: 1px solid #334155;
  border-radius: 6px;
  transition: all 0.3s ease;
  background: #0f172a;
}

.role-item:hover {
  border-color: #6366f1;
  background-color: #1e293b;
}

.role-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.role-name {
  font-weight: 500;
  color: #e2e8f0;
}

.role-description {
  font-size: 12px;
  color: #94a3b8;
}

/* Element Plus 深色主题覆盖 */
:deep(.el-table) {
  background-color: transparent;
  color: #e2e8f0;
}

:deep(.el-table) {
  background-color: #0f172a;
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