import { api } from './request'
import type { 
  KnowledgeBase, 
  KnowledgeBaseCreate, 
  KnowledgeBaseUpdate, 
  Document, 
  DocumentUpload,
  DocumentListResponse,
  DocumentChunksResponse,
  SearchRequest,
  SearchResult,
  PaginationParams 
} from '@/types'

// Knowledge Base API
export const knowledgeApi = {
  // Knowledge Bases
  getKnowledgeBases(params?: PaginationParams) {
    return api.get<KnowledgeBase[]>('/knowledge-bases/', { params })
  },
  
  createKnowledgeBase(data: KnowledgeBaseCreate) {
    return api.post<KnowledgeBase>('/knowledge-bases/', data)
  },
  
  getKnowledgeBase(knowledgeBaseId: string) {
    return api.get<KnowledgeBase>(`/knowledge-bases/${knowledgeBaseId}`)
  },
  
  updateKnowledgeBase(knowledgeBaseId: string, data: KnowledgeBaseUpdate) {
    return api.put<KnowledgeBase>(`/knowledge-bases/${knowledgeBaseId}`, data)
  },
  
  deleteKnowledgeBase(knowledgeBaseId: string) {
    return api.delete(`/knowledge-bases/${knowledgeBaseId}`)
  },
  
  // Documents
  getDocuments(knowledgeBaseId: string, params?: PaginationParams) {
    return api.get<DocumentListResponse>(`/knowledge-bases/${knowledgeBaseId}/documents`, { params })
  },
  
  uploadDocument(knowledgeBaseId: string, file: File) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('knowledge_base_id', knowledgeBaseId)
    
    return api.upload<Document>(`/knowledge-bases/${knowledgeBaseId}/documents`, formData)
  },
  
  deleteDocument(knowledgeBaseId: string, documentId: string) {
    return api.delete(`/knowledge-bases/${knowledgeBaseId}/documents/${documentId}`)
  },
  
  processDocument(knowledgeBaseId: string, documentId: string) {
    return api.post<Document>(`/knowledge-bases/${knowledgeBaseId}/documents/${documentId}/process`)
  },
  
  getDocumentChunks(knowledgeBaseId: string, documentId: string) {
    return api.get<DocumentChunksResponse>(`/knowledge-bases/${knowledgeBaseId}/documents/${documentId}/chunks`)
  },
  
  // Search
  searchKnowledgeBase(data: SearchRequest) {
    return api.post<SearchResult[]>(`/knowledge-bases/${data.knowledge_base_id}/search`, {
      query: data.query,
      top_k: data.top_k,
      score_threshold: data.score_threshold
    })
  }
}