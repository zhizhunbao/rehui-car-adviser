// 搜索相关类型定义

// 搜索类型
export type SearchType = 'car' | 'dealer' | 'review' | 'price' | 'all';

// 搜索过滤器类型
export interface SearchFilters {
  brand?: string[];
  model?: string[];
  year?: {
    min?: number;
    max?: number;
  };
  price?: {
    min?: number;
    max?: number;
  };
  mileage?: {
    min?: number;
    max?: number;
  };
  fuelType?: string[];
  transmission?: string[];
  bodyType?: string[];
  location?: string;
  radius?: number;
}

// 搜索排序类型
export interface SearchSort {
  field: 'price' | 'year' | 'mileage' | 'rating' | 'distance' | 'created_at';
  order: 'asc' | 'desc';
}

// 搜索请求类型
export interface SearchRequest {
  query: string;
  type?: SearchType;
  filters?: SearchFilters;
  sort?: SearchSort;
  pagination?: {
    page: number;
    limit: number;
  };
  location?: {
    latitude: number;
    longitude: number;
  };
}

// 搜索结果类型
export interface SearchResult {
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
}

// 汽车列表项类型（别名）
export type CarListing = SearchResult;

// 搜索响应类型
export interface SearchResponse {
  results: SearchResult[];
  total: number;
  page: number;
  limit: number;
  hasMore: boolean;
  suggestions?: string[];
  filters?: {
    available: SearchFilters;
    applied: SearchFilters;
  };
  aggregations?: {
    brands: Array<{ name: string; count: number }>;
    models: Array<{ name: string; count: number }>;
    priceRanges: Array<{ range: string; count: number }>;
    locations: Array<{ name: string; count: number }>;
  };
}

// 搜索状态类型
export interface SearchState {
  query: string;
  results: SearchResult[];
  isLoading: boolean;
  error: string | null;
  total: number;
  page: number;
  limit: number;
  hasMore: boolean;
  filters: SearchFilters;
  sort: SearchSort;
  suggestions: string[];
  searchHistory: string[];
}

// 搜索操作类型
export interface SearchActions {
  search: (request: SearchRequest) => Promise<void>;
  loadMore: () => Promise<void>;
  setQuery: (query: string) => void;
  setFilters: (filters: SearchFilters) => void;
  setSort: (sort: SearchSort) => void;
  clearFilters: () => void;
  clearResults: () => void;
  addToHistory: (query: string) => void;
  clearHistory: () => void;
}

// 搜索上下文类型
export interface SearchContextType {
  query: string;
  results: SearchResult[];
  isLoading: boolean;
  error: string | null;
  total: number;
  page: number;
  limit: number;
  hasMore: boolean;
  filters: SearchFilters;
  sort: SearchSort;
  suggestions: string[];
  searchHistory: string[];
  search: (request: SearchRequest) => Promise<void>;
  loadMore: () => Promise<void>;
  setQuery: (query: string) => void;
  setFilters: (filters: SearchFilters) => void;
  setSort: (sort: SearchSort) => void;
  clearFilters: () => void;
  clearResults: () => void;
  addToHistory: (query: string) => void;
  clearHistory: () => void;
}

// 搜索组件Props类型
export interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  onSearch: (query: string) => void;
  placeholder?: string;
  suggestions?: string[];
  isLoading?: boolean;
  disabled?: boolean;
}

export interface SearchResultsProps {
  results: SearchResult[];
  isLoading?: boolean;
  error?: string | null;
  onLoadMore?: () => void;
  hasMore?: boolean;
  emptyMessage?: string;
}

export interface SearchFiltersProps {
  filters: SearchFilters;
  availableFilters?: SearchFilters;
  onChange: (filters: SearchFilters) => void;
  onClear: () => void;
}

// 搜索建议类型
export interface SearchSuggestion {
  text: string;
  type: 'query' | 'filter' | 'history';
  category?: string;
  count?: number;
}

// 搜索分析类型
export interface SearchAnalytics {
  query: string;
  resultsCount: number;
  clickThroughRate?: number;
  averagePosition?: number;
  searchTime: number;
  filtersUsed: string[];
  timestamp: number;
}

// 热门搜索类型
export interface TrendingSearch {
  query: string;
  count: number;
  trend: 'up' | 'down' | 'stable';
  category?: string;
}

// 搜索配置类型
export interface SearchConfig {
  defaultLimit: number;
  maxLimit: number;
  debounceDelay: number;
  cacheTimeout: number;
  maxHistoryItems: number;
  enableSuggestions: boolean;
  enableAnalytics: boolean;
}
