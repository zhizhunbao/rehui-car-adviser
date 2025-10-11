// 常量定义

// API相关常量
export const API_CONSTANTS = {
  BASE_URL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000',
  TIMEOUT: 10000,
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,
  ENDPOINTS: {
    CONVERSATION: '/api/conversation',
    SEARCH: '/api/search',
    CAR_DATA: '/api/cars',
    USER: '/api/user',
    AUTH: '/api/auth',
  },
} as const;

// WebSocket相关常量
export const WEBSOCKET_CONSTANTS = {
  URL: process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws',
  RECONNECT_ATTEMPTS: 5,
  RECONNECT_DELAY: 1000,
  HEARTBEAT_INTERVAL: 30000,
  MESSAGE_TYPES: {
    CONVERSATION: 'conversation',
    SEARCH: 'search',
    NOTIFICATION: 'notification',
    ERROR: 'error',
  },
} as const;

// 存储相关常量
export const STORAGE_CONSTANTS = {
  KEYS: {
    AUTH_TOKEN: 'auth_token',
    USER_INFO: 'user_info',
    THEME: 'theme',
    LANGUAGE: 'language',
    CONVERSATION_HISTORY: 'conversation_history',
    SEARCH_HISTORY: 'search_history',
    SETTINGS: 'app_settings',
  },
  EXPIRY: {
    AUTH_TOKEN: 7 * 24 * 60 * 60 * 1000, // 7天
    USER_INFO: 30 * 24 * 60 * 60 * 1000, // 30天
    CONVERSATION_HISTORY: 90 * 24 * 60 * 60 * 1000, // 90天
  },
} as const;

// 分页相关常量
export const PAGINATION_CONSTANTS = {
  DEFAULT_PAGE_SIZE: 20,
  MAX_PAGE_SIZE: 100,
  PAGE_SIZE_OPTIONS: [10, 20, 50, 100],
} as const;

// 搜索相关常量
export const SEARCH_CONSTANTS = {
  DEBOUNCE_DELAY: 300,
  MIN_QUERY_LENGTH: 2,
  MAX_QUERY_LENGTH: 100,
  MAX_HISTORY_ITEMS: 50,
  SUGGESTION_LIMIT: 10,
  CACHE_DURATION: 5 * 60 * 1000, // 5分钟
} as const;

// 对话相关常量
export const CONVERSATION_CONSTANTS = {
  MAX_MESSAGE_LENGTH: 4000,
  MAX_CONVERSATION_LENGTH: 50,
  TYPING_INDICATOR_DELAY: 1000,
  MESSAGE_RETRY_ATTEMPTS: 3,
  STREAM_CHUNK_SIZE: 1024,
} as const;

// 文件上传相关常量
export const FILE_CONSTANTS = {
  MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
  ALLOWED_IMAGE_TYPES: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
  ALLOWED_DOCUMENT_TYPES: ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
  UPLOAD_CHUNK_SIZE: 1024 * 1024, // 1MB
} as const;

// 主题相关常量
export const THEME_CONSTANTS = {
  LIGHT: 'light',
  DARK: 'dark',
  AUTO: 'auto',
  COLORS: {
    PRIMARY: '#007bff',
    SECONDARY: '#6c757d',
    SUCCESS: '#28a745',
    WARNING: '#ffc107',
    ERROR: '#dc3545',
    INFO: '#17a2b8',
  },
} as const;

// 语言相关常量
export const LANGUAGE_CONSTANTS = {
  SUPPORTED_LANGUAGES: ['zh-CN', 'en-US', 'ja-JP', 'ko-KR'],
  DEFAULT_LANGUAGE: 'zh-CN',
  FALLBACK_LANGUAGE: 'en-US',
} as const;

// 验证相关常量
export const VALIDATION_CONSTANTS = {
  EMAIL_REGEX: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  PHONE_REGEX: /^1[3-9]\d{9}$/,
  PASSWORD_MIN_LENGTH: 8,
  USERNAME_MIN_LENGTH: 3,
  USERNAME_MAX_LENGTH: 20,
  URL_REGEX: /^https?:\/\/.+/,
} as const;

// 错误代码常量
export const ERROR_CODES = {
  NETWORK_ERROR: 'NETWORK_ERROR',
  TIMEOUT_ERROR: 'TIMEOUT_ERROR',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  AUTHENTICATION_ERROR: 'AUTHENTICATION_ERROR',
  AUTHORIZATION_ERROR: 'AUTHORIZATION_ERROR',
  NOT_FOUND_ERROR: 'NOT_FOUND_ERROR',
  SERVER_ERROR: 'SERVER_ERROR',
  UNKNOWN_ERROR: 'UNKNOWN_ERROR',
} as const;

// 状态码常量
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
  UNPROCESSABLE_ENTITY: 422,
  INTERNAL_SERVER_ERROR: 500,
  BAD_GATEWAY: 502,
  SERVICE_UNAVAILABLE: 503,
} as const;

// 事件名称常量
export const EVENT_CONSTANTS = {
  CONVERSATION_MESSAGE_SENT: 'conversation:message:sent',
  CONVERSATION_MESSAGE_RECEIVED: 'conversation:message:received',
  SEARCH_STARTED: 'search:started',
  SEARCH_COMPLETED: 'search:completed',
  USER_LOGIN: 'user:login',
  USER_LOGOUT: 'user:logout',
  THEME_CHANGED: 'theme:changed',
  LANGUAGE_CHANGED: 'language:changed',
} as const;

// 本地存储键名常量
export const LOCAL_STORAGE_KEYS = {
  AUTH_TOKEN: 'auth_token',
  REFRESH_TOKEN: 'refresh_token',
  USER_PROFILE: 'user_profile',
  APP_SETTINGS: 'app_settings',
  CONVERSATION_STATE: 'conversation_state',
  SEARCH_STATE: 'search_state',
  THEME_PREFERENCE: 'theme_preference',
  LANGUAGE_PREFERENCE: 'language_preference',
} as const;

// 路由路径常量
export const ROUTE_PATHS = {
  HOME: '/',
  CONVERSATION: '/conversation',
  SEARCH: '/search',
  PROFILE: '/profile',
  SETTINGS: '/settings',
  LOGIN: '/login',
  REGISTER: '/register',
  NOT_FOUND: '/404',
} as const;

// 组件尺寸常量
export const COMPONENT_SIZES = {
  SMALL: 'small',
  MEDIUM: 'medium',
  LARGE: 'large',
  EXTRA_LARGE: 'extra-large',
} as const;

// 动画持续时间常量
export const ANIMATION_DURATION = {
  FAST: 150,
  NORMAL: 300,
  SLOW: 500,
  VERY_SLOW: 1000,
} as const;

// 断点常量
export const BREAKPOINTS = {
  MOBILE: 768,
  TABLET: 1024,
  DESKTOP: 1200,
  LARGE_DESKTOP: 1440,
} as const;

// 默认配置常量
export const DEFAULT_CONFIG = {
  API_TIMEOUT: 10000,
  RETRY_ATTEMPTS: 3,
  DEBOUNCE_DELAY: 300,
  PAGE_SIZE: 20,
  MAX_FILE_SIZE: 10 * 1024 * 1024,
  THEME: 'light',
  LANGUAGE: 'zh-CN',
} as const;
