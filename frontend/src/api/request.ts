import axios, { type AxiosRequestConfig, type AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'
import type { ApiResponse } from '@/types'

// Create axios instance
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
request.interceptors.request.use(
  (config: AxiosRequestConfig) => {
    // Add auth token
    const token = localStorage.getItem('access_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// 防止重复处理401错误的标志
let isHandling401 = false

// Response interceptor
request.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    const { data } = response
    
    // Handle successful response
    if (data.success !== false) {
      return response
    }
    
    // Handle business logic errors
    const message = data.message || data.error || 'Request failed'
    ElMessage.error(message)
    return Promise.reject(new Error(message))
  },
  async (error) => {
    const { response, message } = error
    
    if (response) {
      const { status, data } = response
      
      switch (status) {
        case 401:
          // 防止重复处理401错误
          if (!isHandling401) {
            isHandling401 = true
            
            // 延迟处理，避免并发请求重复跳转
            setTimeout(() => {
              console.log('认证失败，跳转到登录页面')
              ElMessage.error('登录已过期，请重新登录')
              
              // 强制跳转到登录页面，添加expired参数标识token过期
              router.replace('/login?expired=true')
              isHandling401 = false
            }, 100)
          }
          break
          
        case 403:
          ElMessage.error('没有权限访问该资源')
          break
          
        case 404:
          ElMessage.error('请求的资源不存在')
          break
          
        case 400:
          // Bad request errors - 支持detail字段
          const badRequestMsg = data?.detail || data?.message || data?.error || '请求参数错误'
          ElMessage.error(badRequestMsg)
          break
          
        case 422:
          // Validation errors
          const errorMessage = data?.detail?.[0]?.msg || data?.message || '请求参数错误'
          ElMessage.error(errorMessage)
          break
          
        case 500:
          ElMessage.error('服务器内部错误')
          break
          
        default:
          const msg = data?.message || data?.error || `请求失败 (${status})`
          ElMessage.error(msg)
      }
    } else if (message.includes('timeout')) {
      ElMessage.error('请求超时，请稍后重试')
    } else if (message.includes('Network Error')) {
      ElMessage.error('网络连接失败，请检查网络')
    } else {
      ElMessage.error('请求失败，请稍后重试')
    }
    
    return Promise.reject(error)
  }
)

// Request methods
export const api = {
  get<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<ApiResponse<T>>> {
    return request.get(url, config)
  },
  
  post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<ApiResponse<T>>> {
    return request.post(url, data, config)
  },
  
  put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<ApiResponse<T>>> {
    return request.put(url, data, config)
  },
  
  patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<ApiResponse<T>>> {
    return request.patch(url, data, config)
  },
  
  delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<ApiResponse<T>>> {
    return request.delete(url, config)
  },
  
  upload<T = any>(url: string, formData: FormData, config?: AxiosRequestConfig): Promise<AxiosResponse<ApiResponse<T>>> {
    return request.post(url, formData, {
      ...config,
      headers: {
        'Content-Type': 'multipart/form-data',
        ...config?.headers
      }
    })
  }
}

export default request