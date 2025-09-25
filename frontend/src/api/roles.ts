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
  
}