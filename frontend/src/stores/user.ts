import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { authApi, usersApi, rolesApi } from '@/api'
import type { User, UserLogin, UserCreate, UserUpdate, LoginRequest, Role } from '@/types'

export const useUserStore = defineStore('user', () => {
  // State
  const user = ref<User | null>(null)
  const isLoading = ref(false)
  
  // Getters
  const isAuthenticated = computed(() => {
    return !!user.value && !!localStorage.getItem('access_token')
  })
  
  const isAdmin = computed(() => {
    if (!user.value) return false
    
    // Check if user has admin role
    if (user.value.roles) {
      return user.value.roles.some(role => 
        role.is_active && (role.code === 'SUPER_ADMIN' || role.code === 'ADMIN')
      )
    }
    
    return false
  })
  
  // Actions
  const login = async (credentials: LoginRequest) => {
    try {
      isLoading.value = true
      const response = await authApi.login(credentials)
      const { access_token, token_type } = response.data
      
      // Store tokens
      localStorage.setItem('access_token', access_token)
      // Note: Backend doesn't return refresh_token yet, using access_token as placeholder
      localStorage.setItem('refresh_token', access_token)
      
      // Get user info
      await getCurrentUser()
      
      return true
    } catch (error: any) {
      console.error('Login failed:', error)
      ElMessage.error(error.response?.data?.detail || error.message || '登录失败')
      return false
    } finally {
      isLoading.value = false
    }
  }
  
  const register = async (userData: UserCreate) => {
    try {
      isLoading.value = true
      const response = await authApi.register(userData)
      
      ElMessage.success('注册成功，请登录')
      return true
    } catch (error: any) {
      console.error('Registration failed:', error)
      ElMessage.error(error.response?.data?.detail || error.message || '注册失败')
      return false
    } finally {
      isLoading.value = false
    }
  }
  
  const getCurrentUser = async () => {
    try {
      const response = await authApi.getCurrentUser()
      user.value = response.data
      
      // Get user roles
      if (user.value) {
        await getUserRoles()
      }
      
      return user.value
    } catch (error: any) {
      console.error('Get current user failed:', error)
      // Clear invalid tokens
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      user.value = null
      throw error
    }
  }
  
  const getUserRoles = async () => {
    try {
      if (!user.value) return
      
      const response = await rolesApi.getUserRoles(user.value.id)
      if (user.value) {
        user.value.roles = response.data
      }
    } catch (error: any) {
      console.error('Get user roles failed:', error)
      // Don't throw error, just log it as roles are optional
    }
  }
  
  const updateProfile = async (userData: UserUpdate) => {
    try {
      isLoading.value = true
      const response = await usersApi.updateProfile(userData)
      user.value = response.data
      
      ElMessage.success('个人资料更新成功')
      return true
    } catch (error: any) {
      console.error('Update profile failed:', error)
      ElMessage.error(error.response?.data?.detail || error.message || '更新失败')
      return false
    } finally {
      isLoading.value = false
    }
  }
  
  const logout = async () => {
    try {
      await authApi.logout()
      user.value = null
      ElMessage.success('已退出登录')
    } catch (error) {
      console.error('Logout error:', error)
    }
  }
  
  const refreshToken = async () => {
    try {
      const refreshToken = localStorage.getItem('refresh_token')
      if (!refreshToken) {
        throw new Error('No refresh token available')
      }
      
      const response = await authApi.refreshToken(refreshToken)
      const { access_token, token_type } = response.data
      
      localStorage.setItem('access_token', access_token)
      // Note: Backend doesn't return refresh_token yet, using access_token as placeholder
      localStorage.setItem('refresh_token', access_token)
      
      return true
    } catch (error) {
      console.error('Token refresh failed:', error)
      await logout()
      return false
    }
  }
  
  const deleteAccount = async () => {
    try {
      isLoading.value = true
      await usersApi.deleteAccount()
      await logout()
      
      ElMessage.success('账户已删除')
      return true
    } catch (error: any) {
      console.error('Delete account failed:', error)
      ElMessage.error(error.message || '删除账户失败')
      return false
    } finally {
      isLoading.value = false
    }
  }
  
  // Initialize user on store creation
  const initializeUser = async () => {
    const token = localStorage.getItem('access_token')
    if (token && !user.value) {
      try {
        await getCurrentUser()
      } catch (error) {
        // Token is invalid, will be cleared in getCurrentUser
        console.log('Failed to initialize user with stored token')
      }
    }
  }
  
  return {
    // State
    user,
    isLoading,
    
    // Getters
    isAuthenticated,
    isAdmin,
    
    // Actions
    login,
    register,
    getCurrentUser,
    getUserRoles,
    updateProfile,
    logout,
    refreshToken,
    deleteAccount,
    initializeUser
  }
})