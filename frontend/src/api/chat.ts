import { api } from './request'
import type { 
  Conversation, 
  ConversationCreate, 
  ConversationUpdate, 
  Message, 
  ChatRequest, 
  ChatResponse,
  PaginationParams 
} from '@/types'

// Chat API
export const chatApi = {
  // Conversations
  getConversations(params?: PaginationParams) {
    return api.get<Conversation[]>('/chat/conversations', { params })
  },
  
  createConversation(data: ConversationCreate) {
    return api.post<Conversation>('/chat/conversations', data)
  },
  
  getConversation(conversationId: string) {
    return api.get<Conversation>(`/chat/conversations/${conversationId}`)
  },
  
  updateConversation(conversationId: string, data: ConversationUpdate) {
    return api.put<Conversation>(`/chat/conversations/${conversationId}`, data)
  },
  
  deleteConversation(conversationId: string) {
    return api.delete(`/chat/conversations/${conversationId}`)
  },
  
  // Messages
  getMessages(conversationId: string, params?: PaginationParams) {
    return api.get<Message[]>(`/chat/conversations/${conversationId}/messages`, { params })
  },
  
  // Chat
  sendMessage(conversationId: string, data: ChatRequest) {
    return api.post<ChatResponse>(`/chat/conversations/${conversationId}/chat`, data)
  },
  
  // Stream chat (for Server-Sent Events)
  sendMessageStream(data: ChatRequest) {
    const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
    const token = localStorage.getItem('access_token')
    
    return new EventSource(`${baseURL}/chat/stream`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      // Note: EventSource doesn't support POST with body directly
      // This would need to be implemented differently, possibly using fetch with ReadableStream
    })
  },
  
  // Alternative stream implementation using fetch
  async sendMessageStreamFetch(conversationId: string, data: ChatRequest): Promise<ReadableStream<Uint8Array> | null> {
    const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
    const token = localStorage.getItem('access_token')
    
    try {
      const response = await fetch(`${baseURL}/chat/conversations/${conversationId}/chat/stream`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      })
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return response.body
    } catch (error) {
      console.error('Stream request failed:', error)
      throw error
    }
  }
}