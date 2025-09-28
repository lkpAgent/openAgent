import { api } from './request'
import type { PaginationParams } from '@/types'

// LLM Configuration types
export interface LLMConfig {
  id: number
  name: string
  provider: string
  model_name: string
  api_key: string
  base_url?: string
  temperature: number
  max_tokens: number
  top_p: number
  description?: string
  is_active: boolean
  is_default: boolean
  is_embedding: boolean
  extra_config?: Record<string, any>
  created_at: string
  updated_at: string
}

export interface LLMConfigCreate {
  name: string
  provider: string
  model_name: string
  api_key: string
  base_url?: string
  temperature?: number
  max_tokens?: number
  top_p?: number
  description?: string
  is_active?: boolean
  is_default?: boolean
  is_embedding?: boolean
  extra_config?: Record<string, any>
}

export interface LLMConfigUpdate {
  name?: string
  provider?: string
  model_name?: string
  api_key?: string
  base_url?: string
  temperature?: number
  max_tokens?: number
  top_p?: number
  description?: string
  is_active?: boolean
  is_default?: boolean
  is_embedding?: boolean
  extra_config?: Record<string, any>
}

export interface LLMConfigTestRequest {
  message?: string
}

export interface LLMConfigTestResponse {
  success: boolean
  response_time: number
  model_info?: string
  error?: string
  test_message?: any
}

// LLM Configuration API
export const llmConfigApi = {
  // Get all LLM configurations
  getLLMConfigs(params?: {
    skip?: number
    limit?: number
    search?: string
    provider?: string
    is_active?: boolean
    is_embedding?: boolean
  }) {
    return api.get<LLMConfig[]>('/admin/llm-configs/', { params })
  },

  // Get LLM configuration by ID
  getLLMConfig(configId: number) {
    return api.get<LLMConfig>(`/admin/llm-configs/${configId}`)
  },

  // Create new LLM configuration
  createLLMConfig(data: LLMConfigCreate) {
    return api.post<LLMConfig>('/admin/llm-configs/', data)
  },

  // Update LLM configuration
  updateLLMConfig(configId: number, data: LLMConfigUpdate) {
    return api.put<LLMConfig>(`/admin/llm-configs/${configId}`, data)
  },

  // Delete LLM configuration
  deleteLLMConfig(configId: number) {
    return api.delete(`/admin/llm-configs/${configId}`)
  },

  // Test LLM configuration
  testLLMConfig(configId: number, data?: LLMConfigTestRequest) {
    return api.post<LLMConfigTestResponse>(`/admin/llm-configs/${configId}/test`, data || {})
  },

  // Get embedding type configurations
  getEmbeddingConfigs(params?: {
    skip?: number
    limit?: number
    is_active?: boolean
  }) {
    return api.get<LLMConfig[]>('/admin/llm-configs/', { 
      params: { ...params, is_embedding: true }
    })
  },

  // Get chat model configurations
  getChatConfigs(params?: {
    skip?: number
    limit?: number
    is_active?: boolean
  }) {
    return api.get<LLMConfig[]>('/admin/llm-configs/', { 
      params: { ...params, is_embedding: false }
    })
  },

  // Get default configuration
  getDefaultConfig(isEmbedding: boolean = false) {
    return api.get<LLMConfig>('/admin/llm-configs/default', {
      params: { is_embedding: isEmbedding }
    })
  },

  // Get active configurations
  getActiveConfigs(params?: {
    skip?: number
    limit?: number
    is_embedding?: boolean
  }) {
    return api.get<LLMConfig[]>('/admin/llm-configs/', { 
      params: { ...params, is_active: true }
    })
  },

  // Set as default configuration
  setAsDefault(configId: number) {
    return api.post<LLMConfig>(`/admin/llm-configs/${configId}/set-default`)
  },

  // Toggle configuration status
  toggleStatus(configId: number) {
    return api.post<LLMConfig>(`/admin/llm-configs/${configId}/toggle-status`)
  }
}