export interface CarListing {
  id: string;
  title: string;
  price: string;
  year: number;
  mileage: string;
  city: string;
  link: string;
  image?: string;
}

export interface SearchRequest {
  query: string;
}

export interface SearchResponse {
  success: boolean;
  data?: CarListing[];
  total_count?: number;
  error?: string;
  message?: string;
}

export interface SearchContextType {
  searchResults: CarListing[];
  isLoading: boolean;
  error: string | null;
  searchCars: (query: string) => Promise<void>;
}

// 对话式搜索相关类型
export interface ConversationMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface ConversationRequest {
  message: string;
  session_id?: string;
  conversation_history?: ConversationMessage[];
}

export interface ConversationResponse {
  success: boolean;
  message: string;
  session_id: string;
  conversation_history: ConversationMessage[];
  should_search: boolean;
  search_params?: ParsedQuery;
  error?: string;
}

export interface ParsedQuery {
  make?: string;
  model?: string;
  year_min?: number;
  year_max?: number;
  price_max?: number;
  mileage_max?: number;
  location?: string;
  keywords: string[];
}

export interface ConversationContextType {
  messages: ConversationMessage[];
  isLoading: boolean;
  error: string | null;
  sessionId: string | null;
  sendMessage: (message: string) => Promise<void>;
  clearConversation: () => void;
}