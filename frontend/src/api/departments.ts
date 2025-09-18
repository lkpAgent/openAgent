import { api } from './request'
import type { PaginationParams } from '@/types'

// Department types
export interface Department {
  id: number
  name: string
  code: string
  description?: string
  parent_id?: number
  manager_id?: number
  is_active: boolean
  created_at: string
  updated_at: string
  manager?: {
    id: number
    username: string
    full_name?: string
  }
  children?: Department[]
  user_count?: number
}

export interface DepartmentCreate {
  name: string
  code: string
  description?: string
  parent_id?: number
  manager_id?: number
  is_active?: boolean
  sort_order?: number
}

export interface DepartmentUpdate {
  name?: string
  code?: string
  description?: string
  parent_id?: number
  manager_id?: number
  is_active?: boolean
  sort_order?: number
}

// Departments API
export const departmentsApi = {
  // Get all departments
  getDepartments(params?: {
    skip?: number
    limit?: number
    search?: string
    parent_id?: number
    is_active?: boolean
    include_children?: boolean
  }) {
    return api.get<{
      departments: Department[]
      total: number
      page: number
      page_size: number
    }>('/admin/departments/', { params })
  },
  
  // Get department tree
  getDepartmentTree() {
    return api.get<Department[]>('/admin/departments/tree')
  },
  
  // Create new department
  createDepartment(data: DepartmentCreate) {
    return api.post<Department>('/admin/departments/', data)
  },
  
  // Get department by ID
  getDepartmentById(departmentId: number) {
    return api.get<Department>(`/admin/departments/${departmentId}`)
  },
  
  // Update department by ID
  updateDepartmentById(departmentId: number, data: DepartmentUpdate) {
    return api.put<Department>(`/admin/departments/${departmentId}`, data)
  },
  
  // Delete department by ID
  deleteDepartmentById(departmentId: number) {
    return api.delete(`/admin/departments/${departmentId}`)
  },
  
  // Get department users
  getDepartmentUsers(departmentId: number, params?: PaginationParams) {
    return api.get<{
      users: any[]
      total: number
      page: number
      page_size: number
    }>(`/admin/departments/${departmentId}/users`, { params })
  }
}