import { api } from './request'
import type { 
  KnowledgeBase, 
  KnowledgeBaseCreate, 
  KnowledgeBaseUpdate, 
  Document, 
  DocumentUpload,
  SearchRequest,
  SearchResult,
  PaginationParams 
} from '@/types'

// Knowledge Base API
export const knowledgeApi = {
  // Knowledge Bases
  getKnowledgeBases(params?: PaginationParams) {
    return api.get<KnowledgeBase[]>('/knowledge/', { params })
  },
  
  createKnowledgeBase(data: KnowledgeBaseCreate) {
    return api.post<KnowledgeBase>('/knowledge/', data)
  },
  
  getKnowledgeBase(knowledgeBaseId: string) {
    return api.get<KnowledgeBase>(`/knowledge/${knowledgeBaseId}`)
  },
  
  updateKnowledgeBase(knowledgeBaseId: string, data: KnowledgeBaseUpdate) {
    return api.put<KnowledgeBase>(`/knowledge/${knowledgeBaseId}`, data)
  },
  
  deleteKnowledgeBase(knowledgeBaseId: string) {
    return api.delete(`/knowledge/${knowledgeBaseId}`)
  },
  
  // Documents
  getDocuments(knowledgeBaseId: string, params?: PaginationParams) {
    return api.get<Document[]>(`/knowledge/${knowledgeBaseId}/documents`, { params })
  },
  
  uploadDocument(knowledgeBaseId: string, file: File) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('knowledge_base_id', knowledgeBaseId)
    
    return api.upload<Document>(`/knowledge/${knowledgeBaseId}/documents/upload`, formData)
  },
  
  deleteDocument(knowledgeBaseId: string, documentId: string) {
    return api.delete(`/knowledge/${knowledgeBaseId}/documents/${documentId}`)
  },
  
  processDocument(knowledgeBaseId: string, documentId: string) {
    return api.post<Document>(`/knowledge/${knowledgeBaseId}/documents/${documentId}/process`)
  },
  
  // Search
  searchKnowledgeBase(data: SearchRequest) {
    return api.post<SearchResult[]>(`/knowledge/${data.knowledge_base_id}/search`, {
      query: data.query,
      top_k: data.top_k,
      score_threshold: data.score_threshold
    })
  }
}