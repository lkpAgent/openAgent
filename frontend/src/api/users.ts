import { api } from './request'
import type { User, UserUpdate, UserCreate, PaginationParams } from '@/types'

// Users API
export const usersApi = {
  // Get current user profile
  getProfile() {
    return api.get<User>('/users/profile')
  },
  
  // Update current user profile
  updateProfile(data: UserUpdate) {
    return api.put<User>('/users/profile', data)
  },
  
  // Delete current user account
  deleteAccount() {
    return api.delete('/users/profile')
  },
  
  // Change password
  changePassword(data: { current_password: string; new_password: string }) {
    return api.put('/users/change-password', data)
  },
  
  // Admin: Get all users with pagination and filters
  getUsers(params?: {
    skip?: number
    limit?: number
    search?: string
    department_id?: number
    role_id?: number
    is_active?: boolean
  }) {
    return api.get<{
      users: User[]
      total: number
      page: number
      page_size: number
    }>('/users/', { params })
  },
  
  // Admin: Create new user
  createUser(data: UserCreate & {
    department_id?: number
    is_admin?: boolean
    is_active?: boolean
  }) {
    return api.post<User>('/users/', data)
  },
  
  // Admin: Get user by ID
  getUserById(userId: number) {
    return api.get<User>(`/users/${userId}`)
  },
  
  // Admin: Update user by ID
  updateUserById(userId: number, data: UserUpdate & {
    password?: string
    department_id?: number
    is_admin?: boolean
    is_active?: boolean
  }) {
    return api.put<User>(`/users/${userId}`, data)
  },
  
  // Admin: Delete user by ID
  deleteUserById(userId: number) {
    return api.delete(`/users/${userId}`)
  },
  
  // Admin: Update user status
  updateUserStatus(userId: number, is_active: boolean) {
    return api.put<User>(`/users/${userId}`, { is_active })
  },

  // Admin: Reset user password
  resetUserPassword(userId: number, newPassword: string) {
    return api.put(`/users/${userId}/reset-password`, { new_password: newPassword })
  }
}