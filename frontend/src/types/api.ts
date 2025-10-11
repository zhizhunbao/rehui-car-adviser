// API相关类型定义

// 基础API响应类型
export interface ApiResponse<T = any> {
  success: boolean;
  data: T;
  message?: string;
  code?: string | number;
  timestamp: number;
}

// API错误响应类型
export interface ApiError {
  success: false;
  error: {
    code: string | number;
    message: string;
    details?: any;
  };
  timestamp: number;
}

// 分页响应类型
export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
    hasNext: boolean;
    hasPrev: boolean;
  };
}

// 请求配置类型
export interface RequestConfig {
  url: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  headers?: Record<string, string>;
  data?: any;
  params?: Record<string, any>;
  timeout?: number;
  retries?: number;
}

// HTTP客户端配置类型
export interface HttpClientConfig {
  baseURL: string;
  timeout: number;
  retries: number;
  retryDelay: number;
  headers: Record<string, string>;
}

// API客户端接口
export interface ApiClient {
  get<T>(url: string, config?: Partial<RequestConfig>): Promise<ApiResponse<T>>;
  post<T>(url: string, data?: any, config?: Partial<RequestConfig>): Promise<ApiResponse<T>>;
  put<T>(url: string, data?: any, config?: Partial<RequestConfig>): Promise<ApiResponse<T>>;
  delete<T>(url: string, config?: Partial<RequestConfig>): Promise<ApiResponse<T>>;
  patch<T>(url: string, data?: any, config?: Partial<RequestConfig>): Promise<ApiResponse<T>>;
}

// 请求拦截器类型
export interface RequestInterceptor {
  onRequest?: (config: RequestConfig) => RequestConfig | Promise<RequestConfig>;
  onRequestError?: (error: any) => Promise<any>;
}

// 响应拦截器类型
export interface ResponseInterceptor {
  onResponse?: (response: any) => any | Promise<any>;
  onResponseError?: (error: any) => Promise<any>;
}

// 上传文件类型
export interface FileUpload {
  file: File;
  name?: string;
  type?: string;
  size: number;
  lastModified: number;
}

// 上传进度回调类型
export interface UploadProgressCallback {
  (progress: number): void;
}

// 下载配置类型
export interface DownloadConfig {
  filename?: string;
  contentType?: string;
  onProgress?: UploadProgressCallback;
}

// 用户认证相关类型
export interface LoginCredentials {
  username: string;
  password: string;
  remember?: boolean;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
  firstName?: string;
  lastName?: string;
}

export interface UserProfile {
  id: string;
  username: string;
  email: string;
  firstName?: string;
  lastName?: string;
  avatar?: string;
  preferences?: {
    theme?: 'light' | 'dark';
    language?: string;
    notifications?: boolean;
  };
  createdAt: number;
  updatedAt: number;
}

// 对话 API 相关类型
export interface SendMessageRequest {
  message: string;
  session_id?: string;
  conversation_history?: Array<{
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
  }>;
  model?: string;
  temperature?: number;
  max_tokens?: number;
  stream?: boolean;
}

export interface SendMessageResponse {
  success: boolean;
  message: {
    role: 'assistant';
    content: string;
    timestamp: string;
  };
  session_id: string;
  conversation_history: Array<{
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
  }>;
  error?: string;
}

// 搜索 API 相关类型
export interface SearchRequest {
  query: string;
  type?: 'car' | 'dealer' | 'review' | 'price' | 'all';
  filters?: {
    brand?: string[];
    model?: string[];
    year?: { min?: number; max?: number };
    price?: { min?: number; max?: number };
    mileage?: { min?: number; max?: number };
    fuelType?: string[];
    transmission?: string[];
    bodyType?: string[];
    location?: string;
    radius?: number;
  };
  sort?: {
    field: 'price' | 'year' | 'mileage' | 'rating' | 'distance' | 'created_at';
    order: 'asc' | 'desc';
  };
  pagination?: {
    page: number;
    limit: number;
  };
}

export interface SearchResponse {
  results: Array<{
    id: string;
    title: string;
    description: string;
    url: string;
    imageUrl?: string;
    price?: number;
    currency?: string;
    location?: string;
    distance?: number;
    rating?: number;
    reviewCount?: number;
    metadata?: {
      year?: number;
      mileage?: number;
      fuelType?: string;
      transmission?: string;
      bodyType?: string;
      [key: string]: any;
    };
  }>;
  total: number;
  page: number;
  limit: number;
  hasMore: boolean;
  suggestions?: string[];
}

// 汽车数据相关类型
export interface CarDetails {
  id: string;
  title: string;
  description: string;
  price: number;
  currency: string;
  year: number;
  mileage: number;
  fuelType: string;
  transmission: string;
  bodyType: string;
  color: string;
  location: string;
  images: string[];
  features: string[];
  specifications: {
    engine: string;
    power: string;
    torque: string;
    acceleration: string;
    topSpeed: string;
    fuelConsumption: string;
    emissions: string;
    safety: string[];
    comfort: string[];
    technology: string[];
  };
  dealer: {
    name: string;
    contact: string;
    rating: number;
    reviews: number;
  };
  createdAt: string;
  updatedAt: string;
}

export interface CarListItem {
  id: string;
  title: string;
  price: number;
  currency: string;
  year: number;
  mileage: number;
  fuelType: string;
  transmission: string;
  bodyType: string;
  location: string;
  imageUrl: string;
  rating: number;
  reviewCount: number;
}
