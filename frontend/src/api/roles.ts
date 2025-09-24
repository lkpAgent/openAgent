import { api } from './request'
import type { Role, ApiResponse } from '@/types'

// Role interfaces
export interface RoleCreate {
  name: string
  code: string
  description?: string
  sort_order?: number
  is_active?: boolean
}

export interface RoleUpdate {
  name?: string
  code?: string
  description?: string
  sort_order?: number
  is_active?: boolean
}

export interface UserRoleAssign {
  user_id: number
  role_ids: number[]
}

export interface RolePermissionAssign {
  permission_ids: number[]
}

export interface PermissionCreate {
  name: string
  code: string
  description?: string
  category?: string
  sort_order?: number
}

export interface PermissionUpdate {
  name?: string
  code?: string
  description?: string
  category?: string
  sort_order?: number
}

// Roles API
export const rolesApi = {
  // Get user roles by user ID
  getUserRoles(userId: number) {
    return api.get<Role[]>(`/admin/roles/user-roles/user/${userId}`)
  },
  
  // Get all roles
  getRoles(params?: {
    skip?: number
    limit?: number
    search?: string
    is_active?: boolean
  }) {
    return api.get<Role[]>('/admin/roles/', { params })
  },
  
  // Get role by ID
  getRole(roleId: number) {
    return api.get<Role>(`/admin/roles/${roleId}`)
  },
  
  // Create new role
  createRole(data: RoleCreate) {
    return api.post<Role>('/admin/roles/', data)
  },
  
  // Update role
  updateRole(roleId: number, data: RoleUpdate) {
    return api.put<Role>(`/admin/roles/${roleId}`, data)
  },
  
  // Delete role
  deleteRole(roleId: number) {
    return api.delete(`/admin/roles/${roleId}`)
  },
  
  // Assign permissions to role
  assignRolePermissions(roleId: number, data: RolePermissionAssign) {
    return api.post(`/admin/roles/${roleId}/permissions`, data)
  },
  
  // Get role permissions
  getRolePermissions(roleId: number) {
    return api.get(`/admin/roles/${roleId}/permissions`)
  },
  
  // Assign roles to user
  assignUserRoles(data: UserRoleAssign) {
    return api.post('/admin/roles/user-roles/assign', data)
  },
  
  // Get role resources
  getRoleResources(roleId: number) {
    return api.get(`/admin/resources/role/${roleId}/`)
  },
  
  // Assign resources to role
  assignRoleResources(roleId: number, resourceIds: number[]) {
    return api.post('/admin/resources/assign-role/', {
      role_id: roleId,
      resource_ids: resourceIds
    })
  }
}

// Permissions API
export const permissionsApi = {
  // Get all permissions
  getPermissions(params?: {
    page?: number
    page_size?: number
    search?: string
    resource?: string
    action?: string
  }) {
    return api.get('/admin/permissions/', { params })
  },
  

  
  // Get permission by ID
  getPermission(permissionId: number) {
    return api.get(`/admin/permissions/${permissionId}`)
  },
  
  // Create permission
  createPermission(data: PermissionCreate) {
    return api.post('/admin/permissions/', data)
  },
  
  // Update permission
  updatePermission(permissionId: number, data: PermissionUpdate) {
    return api.put(`/admin/permissions/${permissionId}`, data)
  },
  
  // Delete permission
  deletePermission(permissionId: number) {
    return api.delete(`/admin/permissions/${permissionId}`)
  }
}