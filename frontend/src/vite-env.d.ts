/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_LOG_LEVEL: string
  readonly VITE_LOG_ENABLE_CONSOLE: string
  readonly VITE_LOG_ENABLE_STORAGE: string
  readonly DEV: boolean
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
