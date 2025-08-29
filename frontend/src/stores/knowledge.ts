import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { knowledgeApi } from '@/api'
import type { 
  KnowledgeBase, 
  KnowledgeBaseCreate, 
  KnowledgeBaseUpdate, 
  Document,
  SearchRequest,
  SearchResult
} from '@/types'

export const useKnowledgeStore = defineStore('knowledge', () => {
  // State
  const knowledgeBases = ref<KnowledgeBase[]>([])
  const currentKnowledgeBase = ref<KnowledgeBase | null>(null)
  const documents = ref<Document[]>([])
  const searchResults = ref<SearchResult[]>([])
  const isLoading = ref(false)
  const isLoadingDocuments = ref(false)
  const isUploading = ref(false)
  const isSearching = ref(false)
  
  // Getters
  const activeKnowledgeBases = computed(() => {
    return knowledgeBases.value.filter(kb => kb.is_active)
  })
  
  const sortedKnowledgeBases = computed(() => {
    return [...knowledgeBases.value].sort((a, b) => 
      new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
    )
  })
  
  const documentsByStatus = computed(() => {
    const grouped = {
      pending: [] as Document[],
      processing: [] as Document[],
      completed: [] as Document[],
      failed: [] as Document[]
    }
    
    documents.value.forEach(doc => {
      if (doc.status in grouped) {
        grouped[doc.status as keyof typeof grouped].push(doc)
      }
    })
    
    return grouped
  })
  
  // Actions
  const loadKnowledgeBases = async () => {
    try {
      isLoading.value = true
      const response = await knowledgeApi.getKnowledgeBases()
      knowledgeBases.value = response.data.data || []
    } catch (error: any) {
      console.error('Load knowledge bases failed:', error)
      ElMessage.error('加载知识库列表失败')
    } finally {
      isLoading.value = false
    }
  }
  
  const createKnowledgeBase = async (data: KnowledgeBaseCreate) => {
    try {
      isLoading.value = true
      const response = await knowledgeApi.createKnowledgeBase(data)
      const newKnowledgeBase = response.data.data!
      
      knowledgeBases.value.unshift(newKnowledgeBase)
      currentKnowledgeBase.value = newKnowledgeBase
      
      ElMessage.success('创建知识库成功')
      return newKnowledgeBase
    } catch (error: any) {
      console.error('Create knowledge base failed:', error)
      ElMessage.error('创建知识库失败')
      return null
    } finally {
      isLoading.value = false
    }
  }
  
  const loadKnowledgeBase = async (knowledgeBaseId: string) => {
    try {
      isLoading.value = true
      const response = await knowledgeApi.getKnowledgeBase(knowledgeBaseId)
      currentKnowledgeBase.value = response.data.data!
      
      // Update in list if exists
      const index = knowledgeBases.value.findIndex(kb => kb.id === knowledgeBaseId)
      if (index !== -1) {
        knowledgeBases.value[index] = currentKnowledgeBase.value
      }
      
      return currentKnowledgeBase.value
    } catch (error: any) {
      console.error('Load knowledge base failed:', error)
      ElMessage.error('加载知识库失败')
      return null
    } finally {
      isLoading.value = false
    }
  }
  
  const updateKnowledgeBase = async (knowledgeBaseId: string, data: KnowledgeBaseUpdate) => {
    try {
      const response = await knowledgeApi.updateKnowledgeBase(knowledgeBaseId, data)
      const updatedKnowledgeBase = response.data.data!
      
      // Update in list
      const index = knowledgeBases.value.findIndex(kb => kb.id === knowledgeBaseId)
      if (index !== -1) {
        knowledgeBases.value[index] = updatedKnowledgeBase
      }
      
      // Update current if it's the same
      if (currentKnowledgeBase.value?.id === knowledgeBaseId) {
        currentKnowledgeBase.value = updatedKnowledgeBase
      }
      
      ElMessage.success('知识库更新成功')
      return updatedKnowledgeBase
    } catch (error: any) {
      console.error('Update knowledge base failed:', error)
      ElMessage.error('更新知识库失败')
      return null
    }
  }
  
  const deleteKnowledgeBase = async (knowledgeBaseId: string) => {
    try {
      await knowledgeApi.deleteKnowledgeBase(knowledgeBaseId)
      
      // Remove from list
      knowledgeBases.value = knowledgeBases.value.filter(kb => kb.id !== knowledgeBaseId)
      
      // Clear current if it's the same
      if (currentKnowledgeBase.value?.id === knowledgeBaseId) {
        currentKnowledgeBase.value = null
        documents.value = []
      }
      
      ElMessage.success('知识库删除成功')
      return true
    } catch (error: any) {
      console.error('Delete knowledge base failed:', error)
      ElMessage.error('删除知识库失败')
      return false
    }
  }
  
  const loadDocuments = async (knowledgeBaseId: string) => {
    try {
      isLoadingDocuments.value = true
      const response = await knowledgeApi.getDocuments(knowledgeBaseId)
      documents.value = response.data.data || []
      return documents.value
    } catch (error: any) {
      console.error('Load documents failed:', error)
      ElMessage.error('加载文档列表失败')
      return []
    } finally {
      isLoadingDocuments.value = false
    }
  }
  
  const uploadDocument = async (knowledgeBaseId: string, file: File) => {
    try {
      isUploading.value = true
      const response = await knowledgeApi.uploadDocument(knowledgeBaseId, file)
      const newDocument = response.data.data!
      
      documents.value.unshift(newDocument)
      
      ElMessage.success('文档上传成功')
      return newDocument
    } catch (error: any) {
      console.error('Upload document failed:', error)
      ElMessage.error('文档上传失败')
      return null
    } finally {
      isUploading.value = false
    }
  }
  
  const deleteDocument = async (knowledgeBaseId: string, documentId: string) => {
    try {
      await knowledgeApi.deleteDocument(knowledgeBaseId, documentId)
      
      // Remove from list
      documents.value = documents.value.filter(doc => doc.id !== documentId)
      
      ElMessage.success('文档删除成功')
      return true
    } catch (error: any) {
      console.error('Delete document failed:', error)
      ElMessage.error('删除文档失败')
      return false
    }
  }
  
  const processDocument = async (knowledgeBaseId: string, documentId: string) => {
    try {
      const response = await knowledgeApi.processDocument(knowledgeBaseId, documentId)
      const updatedDocument = response.data.data!
      
      // Update in list
      const index = documents.value.findIndex(doc => doc.id === documentId)
      if (index !== -1) {
        documents.value[index] = updatedDocument
      }
      
      ElMessage.success('文档处理已开始')
      return updatedDocument
    } catch (error: any) {
      console.error('Process document failed:', error)
      ElMessage.error('文档处理失败')
      return null
    }
  }
  
  const searchKnowledgeBase = async (data: SearchRequest) => {
    try {
      isSearching.value = true
      const response = await knowledgeApi.searchKnowledgeBase(data)
      searchResults.value = response.data.data || []
      return searchResults.value
    } catch (error: any) {
      console.error('Search knowledge base failed:', error)
      ElMessage.error('搜索失败')
      return []
    } finally {
      isSearching.value = false
    }
  }
  
  const clearSearchResults = () => {
    searchResults.value = []
  }
  
  const clearCurrentKnowledgeBase = () => {
    currentKnowledgeBase.value = null
    documents.value = []
    searchResults.value = []
  }
  
  const updateDocumentStatus = (documentId: string, status: Document['status'], error?: string) => {
    const index = documents.value.findIndex(doc => doc.id === documentId)
    if (index !== -1) {
      documents.value[index].status = status
      if (error) {
        documents.value[index].processing_error = error
      }
    }
  }
  
  return {
    // State
    knowledgeBases,
    currentKnowledgeBase,
    documents,
    searchResults,
    isLoading,
    isLoadingDocuments,
    isUploading,
    isSearching,
    
    // Getters
    activeKnowledgeBases,
    sortedKnowledgeBases,
    documentsByStatus,
    
    // Actions
    loadKnowledgeBases,
    createKnowledgeBase,
    loadKnowledgeBase,
    updateKnowledgeBase,
    deleteKnowledgeBase,
    loadDocuments,
    uploadDocument,
    deleteDocument,
    processDocument,
    searchKnowledgeBase,
    clearSearchResults,
    clearCurrentKnowledgeBase,
    updateDocumentStatus
  }
})