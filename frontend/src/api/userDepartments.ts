import { api } from './request'
import type { PaginationParams } from '@/types'

// User Department types
export interface UserDepartment {
  id: number
  user_id: number
  department_id: number
  is_primary: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface UserDepartmentWithDetails extends UserDepartment {
  user_name?: string
  user_email?: string
  department_name?: string
  department_code?: string
}

export interface DepartmentUserList {
  department_id: number
  department_name: string
  department_code: string
  users: UserDepartmentWithDetails[]
  total_users: number
  active_users: number
}

export interface UserDepartmentCreate {
  user_id: number
  department_id: number
  is_primary?: boolean
  is_active?: boolean
}

export interface UserDepartmentUpdate {
  is_primary?: boolean
  is_active?: boolean
}

// User Departments API
export const userDepartmentsApi = {
  // Create user-department association
  createUserDepartment(data: UserDepartmentCreate) {
    return api.post<UserDepartment>('/admin/user-departments/', data)
  },

  // Get all departments for a user
  getUserDepartments(userId: number, activeOnly: boolean = true) {
    return api.get<{
      user_id: number
      user_name: string
      user_email: string
      departments: UserDepartmentWithDetails[]
      total_departments: number
      active_departments: number
    }>(`/admin/user-departments/user/${userId}`, {
      params: { active_only: activeOnly }
    })
  },

  // Get all users in a department
  getDepartmentUsers(departmentId: number, activeOnly: boolean = true) {
    return api.get<DepartmentUserList>(`/admin/user-departments/department/${departmentId}`, {
      params: { active_only: activeOnly }
    })
  },

  // Update user-department association
  updateUserDepartment(userId: number, departmentId: number, data: UserDepartmentUpdate) {
    return api.put<UserDepartment>(`/admin/user-departments/user/${userId}/department/${departmentId}`, data)
  },

  // Remove user from department
  removeUserFromDepartment(userId: number, departmentId: number) {
    return api.delete(`/admin/user-departments/user/${userId}/department/${departmentId}`)
  },

  // Set user's primary department
  setUserPrimaryDepartment(userId: number, departmentId: number) {
    return api.put(`/admin/user-departments/user/${userId}/primary-department`, {
      department_id: departmentId
    })
  },

  // Bulk create user-department associations
  bulkCreateUserDepartments(data: {
    user_ids: number[]
    department_id: number
    is_primary?: boolean
    is_active?: boolean
  }) {
    return api.post('/admin/user-departments/bulk', data)
  },

  // Get user's department tree
  getUserDepartmentTree(userId: number) {
    return api.get<{
      user_id: number
      department_tree: any[]
    }>(`/admin/user-departments/user/${userId}/tree`)
  },

  // Get all user IDs that have department associations
  getUsersWithDepartments(activeOnly: boolean = true) {
    return api.get<{
      user_ids: number[]
    }>('/admin/user-departments/users-with-departments', {
      params: { active_only: activeOnly }
    })
  }
}