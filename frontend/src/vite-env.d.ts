/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
  readonly VITE_API_TIMEOUT: string;
  readonly VITE_WS_BASE_URL: string;
  readonly VITE_DEBUG_MODE: string;
  readonly VITE_ENABLE_CACHE_METRICS: string;
  readonly VITE_ENABLE_TOOL_RENDERER: string;
  readonly VITE_APP_NAME: string;
  readonly VITE_APP_VERSION: string;
  readonly VITE_APP_ENV: string;
  readonly VITE_MAX_RECONNECT_ATTEMPTS: string;
  readonly VITE_WEBSOCKET_TIMEOUT: string;
  readonly VITE_CHUNK_TIMEOUT: string;
  readonly VITE_REQUEST_TIMEOUT: string;
  readonly VITE_LOG_LEVEL: string;
  readonly VITE_LOG_FORMAT: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
