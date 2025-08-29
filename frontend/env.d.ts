/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_APP_TITLE: string
  readonly VITE_APP_VERSION: string
  readonly VITE_ENABLE_MOCK: string
  readonly VITE_UPLOAD_MAX_SIZE: string
  readonly VITE_SUPPORTED_FILE_TYPES: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}