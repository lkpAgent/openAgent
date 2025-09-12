// API Response Types
export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  message?: string
  error?: string
}

// User Types
export interface User {
  id: number
  username: string
  email: string
  full_name?: string
  is_active: boolean
  is_superuser: boolean
  avatar_url?: string
  bio?: string
  created_at: string
  updated_at: string
}

export interface UserCreate {
  username: string
  email: string
  password: string
  full_name?: string
}

export interface UserUpdate {
  username?: string
  email?: string
  full_name?: string
  bio?: string
  avatar_url?: string
}

export interface UserLogin {
  username: string
  password: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
}

// Conversation Types
export interface Conversation {
  id: number
  title: string
  user_id: number
  knowledge_base_id?: number
  system_prompt?: string
  model_name: string
  temperature: string
  max_tokens: number
  is_archived: boolean
  created_at: string
  updated_at: string
  message_count?: number
  last_message_at?: string
}

export interface ConversationCreate {
  title: string
  knowledge_base_id?: number
  system_prompt?: string
  model_name?: string
  temperature?: string
  max_tokens?: number
}

export interface ConversationUpdate {
  title?: string
  knowledge_base_id?: number
  system_prompt?: string
  model_name?: string
  temperature?: string
  max_tokens?: number
  is_archived?: boolean
}

// Message Types
export type MessageRole = 'user' | 'assistant' | 'system'
export type MessageType = 'text' | 'image' | 'file' | 'audio'

export interface Message {
  id: number
  conversation_id: number
  role: MessageRole
  content: string
  message_type: MessageType
  metadata?: Record<string, any>
  context_documents?: string[]
  prompt_tokens?: number
  completion_tokens?: number
  total_tokens?: number
  created_at: string
  updated_at: string
  status?: string // 用于显示流式状态，如"正在思考..."、"正在使用工具..."等
  thinking_data?: ThinkingData // LangGraph智能体思考过程数据
}

// LangGraph思考过程数据结构
export interface ThinkingData {
  steps: ThinkingStep[]
  tool_calls: ToolCall[]
  current_step: string
  status: 'thinking' | 'tool_calling' | 'completed' | 'error'
}

export interface ThinkingStep {
  id: number
  type: 'thinking' | 'tool_start' | 'tool_end'
  content: string
  timestamp: string
  node_name?: string
  tool_call?: ToolCall
}

export interface ToolCall {
  id: number
  name: string
  input: Record<string, any>
  output: any
  status: 'running' | 'completed' | 'error'
  timestamp: string
}

export interface MessageCreate {
  content: string
  message_type?: MessageType
  metadata?: Record<string, any>
}

export interface ChatRequest {
  message: string
  conversation_id?: number
  stream?: boolean
  use_knowledge_base?: boolean
  knowledge_base_id?: number
  use_agent?: boolean
  use_langgraph?: boolean
  temperature?: number
  max_tokens?: number
}

export interface ChatResponse {
  user_message: Message
  assistant_message: Message
  total_tokens?: number
  model_used: string
}

// Knowledge Base Types
export interface KnowledgeBase {
  id: number
  name: string
  description?: string
  embedding_model: string
  chunk_size: number
  chunk_overlap: number
  is_active: boolean
  vector_db_type: string
  collection_name: string
  created_at: string
  updated_at: string
  document_count?: number
}

export interface KnowledgeBaseCreate {
  name: string
  description?: string
  embedding_model?: string
  chunk_size?: number
  chunk_overlap?: number
}

export interface KnowledgeBaseUpdate {
  name?: string
  description?: string
  embedding_model?: string
  chunk_size?: number
  chunk_overlap?: number
  is_active?: boolean
}

// Document Types
export type DocumentStatus = 'pending' | 'processing' | 'completed' | 'failed'

export interface Document {
  id: number
  knowledge_base_id: number
  filename: string
  original_filename: string
  file_path: string
  file_size: number
  file_type: string
  mime_type: string
  status: DocumentStatus
  processing_error?: string
  content?: string
  metadata?: Record<string, any>
  chunk_count?: number
  embedding_info?: Record<string, any>
  created_at: string
  updated_at: string
}

export interface DocumentUpload {
  file: File
  knowledge_base_id: number
}

export interface DocumentListResponse {
  documents: Document[]
  total: number
  page: number
  page_size: number
}

// Document Chunk Types
export interface DocumentChunk {
  id: string
  content: string
  metadata: Record<string, any>
  page_number?: number
  chunk_index: number
  start_char?: number
  end_char?: number
}

export interface DocumentChunksResponse {
  document_id: number
  document_name: string
  total_chunks: number
  chunks: DocumentChunk[]
}

export interface SearchRequest {
  query: string
  knowledge_base_id: number
  top_k?: number
  score_threshold?: number
}

export interface SearchResult {
  content: string
  metadata: Record<string, any>
  score: number
  document_id: number
}

// UI State Types
export interface ChatState {
  conversations: Conversation[]
  currentConversation: Conversation | null
  messages: Message[]
  isLoading: boolean
  isStreaming: boolean
}

export interface KnowledgeState {
  knowledgeBases: KnowledgeBase[]
  currentKnowledgeBase: KnowledgeBase | null
  documents: Document[]
  isLoading: boolean
}

export interface UserState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
}

// Form Types
export interface LoginForm {
  username: string
  password: string
  remember: boolean
}

export interface RegisterForm {
  username: string
  email: string
  password: string
  confirmPassword: string
  fullName: string
}

export interface ProfileForm {
  username: string
  email: string
  fullName: string
  bio: string
}

// Component Props Types
export interface MessageItemProps {
  message: Message
  isStreaming?: boolean
}

export interface ConversationItemProps {
  conversation: Conversation
  isActive?: boolean
}

export interface KnowledgeBaseItemProps {
  knowledgeBase: KnowledgeBase
  isActive?: boolean
}

export interface DocumentItemProps {
  document: Document
}

// Utility Types
export type LoadingState = 'idle' | 'loading' | 'success' | 'error'

export interface PaginationParams {
  page?: number
  size?: number
  skip?: number
  limit?: number
}

export interface SortParams {
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

export interface FilterParams {
  search?: string
  status?: string
  is_active?: boolean
  [key: string]: any
}