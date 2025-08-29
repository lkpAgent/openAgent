import { api } from './request'
import type { User, UserUpdate, PaginationParams } from '@/types'

// Users API
export const usersApi = {
  // Get current user profile
  getProfile() {
    return api.get<User>('/users/me')
  },
  
  // Update current user profile
  updateProfile(data: UserUpdate) {
    return api.put<User>('/users/me', data)
  },
  
  // Delete current user account
  deleteAccount() {
    return api.delete('/users/me')
  },
  
  // Admin: Get all users
  getUsers(params?: PaginationParams) {
    return api.get<User[]>('/users/', { params })
  },
  
  // Admin: Get user by ID
  getUserById(userId: string) {
    return api.get<User>(`/users/${userId}`)
  },
  
  // Admin: Update user by ID
  updateUserById(userId: string, data: UserUpdate) {
    return api.put<User>(`/users/${userId}`, data)
  },
  
  // Admin: Delete user by ID
  deleteUserById(userId: string) {
    return api.delete(`/users/${userId}`)
  }
}