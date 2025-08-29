import { api } from './request'
import type { User, UserLogin, UserCreate, AuthTokens, ApiResponse, LoginRequest } from '@/types'

// Auth API
export const authApi = {
  // User login
  login(data: LoginRequest) {
    return api.post<AuthTokens>('/auth/login', data)
  },
  
  // User register
  register(data: UserCreate) {
    return api.post<User>('/auth/register', data)
  },
  
  // Refresh token
  refreshToken(refreshToken: string) {
    return api.post<AuthTokens>('/auth/refresh', {
      refresh_token: refreshToken
    })
  },
  
  // Get current user info
  getCurrentUser() {
    return api.get<User>('/auth/me')
  },
  
  // Logout (optional - mainly client-side)
  logout() {
    // Clear tokens from localStorage
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    return Promise.resolve()
  }
}