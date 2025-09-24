<template>
  <div class="role-management">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">
          <el-icon><UserFilled /></el-icon>
          角色管理
        </h2>
        <p class="page-description">管理系统角色和权限分配</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          新增角色
        </el-button>
      </div>
    </div>

    <div class="content-card">
      <!-- 搜索栏 -->
      <div class="search-bar">
        <div class="search-left">
          <el-input
            v-model="searchQuery"
            placeholder="搜索角色名称或描述"
            style="width: 300px"
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          
          <el-select
            v-model="filterStatus"
            placeholder="状态筛选"
            style="width: 150px"
            clearable
            @change="handleFilter"
          >
            <el-option label="启用" value="active" />
            <el-option label="禁用" value="inactive" />
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
        <!-- 角色表格 -->
        <div class="table-wrapper">
          <el-table
            v-loading="loading"
            :data="filteredRoles"
            style="width: 100%"
            height="100%"
            row-key="id"
            @selection-change="handleSelectionChange"
          >
            <el-table-column type="selection" width="55" />
            
            <el-table-column prop="name" label="角色名称" width="150">
              <template #default="{ row }">
                <div class="role-name">
                  <el-icon class="role-icon" :style="{ color: getRoleColor(row.code) }">
                    <Star v-if="row.code === 'SUPER_ADMIN'" />
                    <Key v-else-if="row.code === 'ADMIN'" />
                    <User v-else />
                  </el-icon>
                  <span class="name-text">{{ row.name }}</span>
                </div>
              </template>
            </el-table-column>
            
            <el-table-column prop="code" label="角色编码" width="150">
              <template #default="{ row }">
                <el-tag :type="getRoleTagType(row.code)" size="small">
                  {{ row.code }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="description" label="描述" min-width="200">
              <template #default="{ row }">
                <span v-if="row.description">{{ row.description }}</span>
                <span v-else class="text-muted">暂无描述</span>
              </template>
            </el-table-column>
            
            <el-table-column prop="permissions" label="权限数量" width="100" align="center">
              <template #default="{ row }">
                <el-tag type="info" size="small">
                  {{ row.permissions?.length || 0 }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="user_count" label="用户数量" width="100" align="center">
              <template #default="{ row }">
                <el-tag type="success" size="small">
                  {{ row.user_count || 0 }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="is_active" label="状态" width="100">
              <template #default="{ row }">
                <el-switch
                  v-model="row.is_active"
                  @change="handleStatusChange(row)"
                  :disabled="row.code === 'SUPER_ADMIN'"
                />
              </template>
            </el-table-column>
            
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
                  type="warning"
                  size="small"
                  @click="handlePermissions(row)"
                >
                  权限配置
                </el-button>
                <el-button
                  type="info"
                  size="small"
                  @click="handleUsers(row)"
                >
                  用户列表
                </el-button>
                <el-button
                  type="danger"
                  size="small"
                  @click="handleDelete(row)"
                  :disabled="row.code === 'SUPER_ADMIN' || row.user_count > 0"
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

    <!-- 角色表单对话框 -->
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
        <el-form-item label="角色名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入角色名称" />
        </el-form-item>
        
        <el-form-item label="角色编码" prop="code">
          <el-input
            v-model="formData.code"
            placeholder="请输入角色编码"
            :disabled="isEdit && currentRole?.code === 'SUPER_ADMIN'"
          />
        </el-form-item>
        
        <el-form-item label="角色描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入角色描述"
          />
        </el-form-item>
        
        <el-form-item label="状态">
          <el-switch
            v-model="formData.is_active"
            :disabled="isEdit && currentRole?.code === 'SUPER_ADMIN'"
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

    <!-- 权限配置对话框 -->
    <el-dialog
      v-model="permissionDialogVisible"
      title="权限配置"
      width="800px"
    >
      <div class="permission-config">
        <div class="config-header">
          <h4>{{ currentRole?.name }} - 权限配置</h4>
          <div class="config-actions">
            <el-button size="small" @click="selectAllPermissions">
              全选
            </el-button>
            <el-button size="small" @click="clearAllPermissions">
              清空
            </el-button>
          </div>
        </div>
        
        <div class="permission-tree">
          <el-tree
            ref="permissionTreeRef"
            :data="permissionTree"
            :props="{ label: 'name', children: 'children' }"
            show-checkbox
            node-key="id"
            :default-checked-keys="selectedPermissions"
            @check="handlePermissionCheck"
          >
            <template #default="{ node, data }">
              <div class="permission-node">
                <el-icon class="permission-icon">
                  <Folder v-if="data.type === 'module'" />
                  <Document v-else />
                </el-icon>
                <span class="permission-name">{{ data.name }}</span>
                <span class="permission-code">{{ data.code }}</span>
                <span v-if="data.description" class="permission-desc">
                  {{ data.description }}
                </span>
              </div>
            </template>
          </el-tree>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="permissionDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handlePermissionSubmit" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 用户列表对话框 -->
    <el-dialog
      v-model="userDialogVisible"
      title="角色用户"
      width="700px"
    >
      <div class="role-users">
        <div class="users-header">
          <h4>{{ currentRole?.name }} - 用户列表</h4>
          <el-button type="primary" size="small" @click="handleAssignUser">
            <el-icon><Plus /></el-icon>
            分配用户
          </el-button>
        </div>
        
        <el-table
          :data="roleUsers"
          style="width: 100%"
          max-height="400px"
        >
          <el-table-column prop="username" label="用户名" width="120">
            <template #default="{ row }">
              <div class="user-info">
                <el-avatar :size="24" :src="row.avatar">
                  {{ row.username && row.username.length > 0 ? row.username.charAt(0).toUpperCase() : '?' }}
                </el-avatar>
                <span>{{ row.username }}</span>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column prop="email" label="邮箱" width="200" />
          
          <el-table-column prop="department" label="部门" width="120">
            <template #default="{ row }">
              <span v-if="row.department">{{ row.department.name }}</span>
              <span v-else class="text-muted">未分配</span>
            </template>
          </el-table-column>
          
          <el-table-column prop="assign_date" label="分配时间" width="160">
            <template #default="{ row }">
              {{ formatDateTime(row.assign_date) }}
            </template>
          </el-table-column>
          
          <el-table-column label="操作" width="100">
            <template #default="{ row }">
              <el-button
                type="danger"
                size="small"
                @click="handleUnassignUser(row)"
                :disabled="currentRole?.code === 'SUPER_ADMIN' && row.roles?.some(role => role.code === 'SUPER_ADMIN')"
              >
                移除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      
      <template #footer>
        <el-button @click="userDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 分配用户对话框 -->
    <el-dialog
      v-model="assignUserDialogVisible"
      title="分配用户"
      width="500px"
    >
      <el-select
        v-model="selectedUserIds"
        multiple
        placeholder="请选择要分配的用户"
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
            <span>{{ user.username }}</span>
            <span class="user-email">{{ user.email }}</span>
          </div>
        </el-option>
      </el-select>
      
      <template #footer>
        <el-button @click="assignUserDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAssignUserSubmit" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import {
  UserFilled,
  Star,
  Key,
  User,
  Plus,
  Search,
  Refresh,
  Folder,
  Document
} from '@element-plus/icons-vue'
import { formatDateTime } from '@/utils/date'
import { rolesApi, permissionsApi, type RoleCreate, type RoleUpdate } from '@/api/roles'
import { usersApi } from '@/api/users'

// 响应式数据
const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const permissionDialogVisible = ref(false)
const userDialogVisible = ref(false)
const assignUserDialogVisible = ref(false)
const isEdit = ref(false)
const currentRole = ref(null)
const selectedRoles = ref([])
const selectedPermissions = ref([])
const selectedUserIds = ref([])

// 搜索和筛选
const searchQuery = ref('')
const filterStatus = ref('')

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 表单
const formRef = ref<FormInstance>()
const permissionTreeRef = ref()
const formData = reactive({
  name: '',
  code: '',
  description: '',
  is_active: true
})

// 数据
const roles = ref([])
const permissionTree = ref([])

const roleUsers = ref([])
const availableUsers = ref([])

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入角色名称', trigger: 'blur' },
    { min: 2, max: 50, message: '角色名称长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入角色编码', trigger: 'blur' },
    { pattern: /^[A-Z0-9_]+$/, message: '角色编码只能包含大写字母、数字和下划线', trigger: 'blur' }
  ]
}

// 计算属性
const dialogTitle = computed(() => isEdit.value ? '编辑角色' : '新增角色')

const filteredRoles = computed(() => {
  // 数据已经在API层面进行了过滤，直接返回
  return roles.value
})

// 方法
const getRoleColor = (roleCode: string) => {
  const colorMap = {
    'SUPER_ADMIN': '#f56c6c',
    'ADMIN': '#e6a23c',
    'DEPT_ADMIN': '#409eff',
    'USER': '#67c23a'
  }
  return colorMap[roleCode] || '#909399'
}

const getRoleTagType = (roleCode: string) => {
  const typeMap = {
    'SUPER_ADMIN': 'danger',
    'ADMIN': 'warning',
    'DEPT_ADMIN': 'primary',
    'USER': 'success'
  }
  return typeMap[roleCode] || 'info'
}

const handleSearch = () => {
  currentPage.value = 1
  loadRoles()
}

const handleFilter = () => {
  currentPage.value = 1
  loadRoles()
}

const handleRefresh = () => {
  searchQuery.value = ''
  filterStatus.value = ''
  loadRoles()
}

const handleSelectionChange = (selection: any[]) => {
  selectedRoles.value = selection
}

const handleCreate = () => {
  isEdit.value = false
  resetForm()
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  isEdit.value = true
  Object.assign(formData, {
    name: row.name,
    code: row.code,
    description: row.description,
    is_active: row.is_active
  })
  currentRole.value = row
  dialogVisible.value = true
}

const handleDelete = async (row: any) => {
  if (row.user_count > 0) {
    ElMessage.warning('该角色下还有用户，无法删除')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除角色 "${row.name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await rolesApi.deleteRole(row.id)
    ElMessage.success('删除成功')
    loadRoles()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

const handleStatusChange = async (row: any) => {
  try {
    await rolesApi.updateRole(row.id, { is_active: row.is_active })
    ElMessage.success(`角色状态已${row.is_active ? '启用' : '禁用'}`)
  } catch (error) {
    // 恢复原状态
    row.is_active = !row.is_active
    console.error('状态更新失败:', error)
    ElMessage.error('状态更新失败')
  }
}

const handlePermissions = async (row: any) => {
  currentRole.value = row
  try {
    const response = await rolesApi.getRolePermissions(row.id)
    const rolePermissionIds = response.data?.map((p: any) => p.id) || []
    selectedPermissions.value = rolePermissionIds
    
    // 等待下一个tick确保树组件已渲染
    await nextTick()
    if (permissionTreeRef.value) {
      permissionTreeRef.value.setCheckedKeys(rolePermissionIds)
    }
  } catch (error) {
    console.error('加载角色权限失败:', error)
    selectedPermissions.value = []
  }
  permissionDialogVisible.value = true
}

const handleUsers = (row: any) => {
  currentRole.value = row
  loadRoleUsers(row.id)
  userDialogVisible.value = true
}

const handleAssignUser = () => {
  loadAvailableUsers()
  assignUserDialogVisible.value = true
}

const handleUnassignUser = async (user: any) => {
  if (!currentRole.value) return
  
  try {
    await ElMessageBox.confirm(
      `确定要将 "${user.username}" 从角色中移除吗？`,
      '确认移除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 获取用户当前的所有角色，然后移除指定角色
    const userRolesResponse = await rolesApi.getUserRoles(user.id)
    const currentRoleIds = userRolesResponse.data?.map((role: any) => role.id) || []
    const newRoleIds = currentRoleIds.filter((id: number) => id !== currentRole.value.id)
    
    await rolesApi.assignUserRoles({
      user_id: user.id,
      role_ids: newRoleIds
    })
    
    ElMessage.success('移除成功')
    loadRoleUsers(currentRole.value.id)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('移除失败:', error)
      ElMessage.error('移除失败')
    }
  }
}

const selectAllPermissions = () => {
  if (permissionTreeRef.value) {
    const permissionKeys = []
    const collectPermissionKeys = (nodes: any[]) => {
      nodes.forEach(node => {
        if (node.type === 'permission') {
          permissionKeys.push(node.id)
        }
        if (node.children) {
          collectPermissionKeys(node.children)
        }
      })
    }
    collectPermissionKeys(permissionTree.value)
    permissionTreeRef.value.setCheckedKeys(permissionKeys)
  }
}

const clearAllPermissions = () => {
  if (permissionTreeRef.value) {
    permissionTreeRef.value.setCheckedKeys([])
  }
}

const handlePermissionCheck = () => {
  if (permissionTreeRef.value) {
    const checkedKeys = permissionTreeRef.value.getCheckedKeys()
    // 只保留权限节点的ID，过滤掉资源节点
    selectedPermissions.value = checkedKeys.filter(key => 
      typeof key === 'number' || !key.toString().startsWith('resource_')
    )
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    submitting.value = true
    
    const roleData = {
      name: formData.name,
      code: formData.code,
      description: formData.description,
      is_active: formData.is_active
    }
    
    if (isEdit.value && currentRole.value) {
      await rolesApi.updateRole(currentRole.value.id, roleData)
      ElMessage.success('更新成功')
    } else {
      await rolesApi.createRole(roleData as RoleCreate)
      ElMessage.success('创建成功')
    }
    
    dialogVisible.value = false
    loadRoles()
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
  } finally {
    submitting.value = false
  }
}

const handlePermissionSubmit = async () => {
  if (!currentRole.value) return
  
  try {
    submitting.value = true
    
    // 使用已过滤的权限ID（只包含权限节点，不包含资源节点）
    await rolesApi.assignRolePermissions(currentRole.value.id, {
      permission_ids: selectedPermissions.value
    })
    
    ElMessage.success('权限配置成功')
    permissionDialogVisible.value = false
    loadRoles()
  } catch (error) {
    console.error('权限配置失败:', error)
    ElMessage.error('权限配置失败')
  } finally {
    submitting.value = false
  }
}

const handleAssignUserSubmit = async () => {
  if (selectedUserIds.value.length === 0) {
    ElMessage.warning('请选择要分配的用户')
    return
  }
  
  if (!currentRole.value) return
  
  try {
    submitting.value = true
    
    // 为每个选中的用户分配角色
    for (const userId of selectedUserIds.value) {
      await rolesApi.assignUserRoles({
        user_id: userId,
        role_ids: [currentRole.value.id]
      })
    }
    
    ElMessage.success('分配成功')
    assignUserDialogVisible.value = false
    selectedUserIds.value = []
    loadRoleUsers(currentRole.value.id)
  } catch (error) {
    console.error('分配失败:', error)
    ElMessage.error('分配失败')
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
    description: '',
    is_active: true
  })
  formRef.value?.clearValidate()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  loadRoles()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  loadRoles()
}

const loadRoles = async () => {
  loading.value = true
  try {
    const params = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value,
      search: searchQuery.value || undefined,
      is_active: filterStatus.value === 'active' ? true : filterStatus.value === 'inactive' ? false : undefined
    }
    
    const response = await rolesApi.getRoles(params)
    roles.value = response.data || []
    
    // 获取总数（如果API返回分页信息）
    total.value = response.data?.length || roles.value.length
  } catch (error) {
    console.error('加载角色列表失败:', error)
    ElMessage.error('加载角色列表失败')
  } finally {
    loading.value = false
  }
}

const loadRoleUsers = async (roleId: number) => {
  try {
    // 获取拥有该角色的用户列表
    const response = await usersApi.getUsers({ role_id: roleId })
    roleUsers.value = response.data?.users || []
  } catch (error) {
    console.error('加载角色用户失败:', error)
    ElMessage.error('加载角色用户失败')
    roleUsers.value = []
  }
}

const loadAvailableUsers = async () => {
  try {
    // 获取所有用户，前端过滤已分配该角色的用户
    const response = await usersApi.getUsers()
    const allUsers = response.data?.users || []
    
    // 过滤掉已经拥有该角色的用户
    const roleUserIds = roleUsers.value.map(user => user.id)
    availableUsers.value = allUsers.filter(user => !roleUserIds.includes(user.id))
  } catch (error) {
    console.error('加载可用用户失败:', error)
    ElMessage.error('加载可用用户失败')
    availableUsers.value = []
  }
}

// 加载权限数据
const loadPermissions = async () => {
  try {
    const response = await permissionsApi.getPermissions()
    console.log('权限API响应:', response)
    
    // 确保获取到的是数组数据
    let permissions = []
    if (response.data) {
      if (Array.isArray(response.data)) {
        permissions = response.data
      } else if (Array.isArray(response.data.items)) {
        permissions = response.data.items
      } else if (Array.isArray(response.data.permissions)) {
        permissions = response.data.permissions
      } else if (Array.isArray(response.data.data)) {
        permissions = response.data.data
      }
    }
    
    console.log('处理后的权限数据:', permissions)
    
    // 将平铺的权限数据转换为树形结构
    permissionTree.value = buildPermissionTree(permissions)
  } catch (error) {
    console.error('加载权限列表失败:', error)
    ElMessage.error('加载权限列表失败')
    permissionTree.value = []
  }
}

// 构建权限树形结构
const buildPermissionTree = (permissions: any[]) => {
  const resourceMap = new Map()
  
  // 按资源分组
  permissions.forEach(permission => {
    // 从code字段解析资源和操作，格式如 'user:create' 或 'system:admin'
    const codeParts = permission.code.split(':')
    const resource = codeParts[0] || 'other'
    const action = codeParts[1] || 'unknown'
    
    if (!resourceMap.has(resource)) {
      resourceMap.set(resource, {
        id: `resource_${resource}`,
        name: getResourceName(resource),
        code: resource,
        type: 'module',
        children: []
      })
    }
    
    // 添加权限到对应资源下
    resourceMap.get(resource).children.push({
      id: permission.id,
      name: permission.name,
      code: permission.code,
      type: 'permission',
      description: permission.description,
      resource: resource,
      action: action
    })
  })
  
  return Array.from(resourceMap.values())
}

// 获取资源显示名称
const getResourceName = (resource: string) => {
  const resourceNames = {
    'user': '用户管理',
    'role': '角色管理', 
    'permission': '权限管理',
    'department': '部门管理',
    'system': '系统管理'
  }
  return resourceNames[resource] || resource
}

// 生命周期
onMounted(() => {
  loadRoles()
  loadPermissions()
})
</script>

<style scoped>
.role-management {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #1e293b;
  padding: 20px;
  overflow: hidden;
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

.role-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.role-icon {
  font-size: 16px;
}

.name-text {
  font-weight: 500;
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

.permission-config {
  padding: 16px 0;
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.config-header h4 {
  margin: 0;
  color: #f1f5f9;
}

.config-actions {
  display: flex;
  gap: 8px;
}

.permission-tree {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #475569;
  border-radius: 6px;
  padding: 12px;
  background: #1e293b;
}

.permission-node {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.permission-icon {
  color: #409eff;
}

.permission-name {
  font-weight: 500;
}

.permission-code {
  font-size: 12px;
  color: #64748b;
  background: #475569;
  padding: 2px 6px;
  border-radius: 3px;
}

.permission-desc {
  font-size: 12px;
  color: #94a3b8;
  margin-left: auto;
}

.role-users {
  padding: 16px 0;
}

.users-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.users-header h4 {
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
  color: #64748b;
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