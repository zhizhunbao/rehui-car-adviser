// 对话相关类型定义

// 导入实时消息类型
import { RealtimeMessage } from '../components/features/RealtimeMessageDisplay';

// 消息角色类型
export type MessageRole = 'user' | 'assistant' | 'system';

// 消息类型
export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: number;
  metadata?: {
    model?: string;
    tokens?: number;
    processingTime?: number;
    [key: string]: any;
  };
}

// 对话消息类型（用于Context）
export interface ConversationMessage {
  role: MessageRole;
  content: string;
  timestamp: string;
}

// 对话类型
export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: number;
  updatedAt: number;
  metadata?: {
    model?: string;
    totalTokens?: number;
    [key: string]: any;
  };
}

// 发送消息请求类型
export interface SendMessageRequest {
  message: string;
  conversationId?: string;
  model?: string;
  temperature?: number;
  maxTokens?: number;
  stream?: boolean;
  context?: {
    previousMessages?: number;
    includeMetadata?: boolean;
  };
}

// 发送消息响应类型
export interface SendMessageResponse {
  message: Message;
  conversationId: string;
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
  model?: string;
  finishReason?: string;
}

// 流式响应类型
export interface StreamResponse {
  type: 'content' | 'metadata' | 'done' | 'error';
  data: any;
  conversationId: string;
  messageId: string;
}

// 对话状态类型
export interface ConversationState {
  conversations: Conversation[];
  currentConversation: Conversation | null;
  isLoading: boolean;
  error: string | null;
  isStreaming: boolean;
}

// 对话操作类型
export interface ConversationActions {
  sendMessage: (request: SendMessageRequest) => Promise<void>;
  createConversation: (title?: string) => Promise<string>;
  deleteConversation: (conversationId: string) => Promise<void>;
  updateConversation: (conversationId: string, updates: Partial<Conversation>) => Promise<void>;
  clearConversation: () => void;
  retryLastMessage: () => Promise<void>;
  setCurrentConversation: (conversationId: string) => void;
}

// 对话上下文类型
export interface ConversationContextType {
  messages: ConversationMessage[];
  isLoading: boolean;
  error: string | null;
  sessionId: string | null;
  isStreaming?: boolean;
  realtimeMessages: RealtimeMessage[];
  sendMessage: (message: string) => Promise<void>;
  clearConversation: () => void;
  retryLastMessage?: () => Promise<void>;
  addRealtimeMessage: (message: RealtimeMessage) => void;
  clearRealtimeMessages: () => void;
}

// 消息组件Props类型
export interface MessageProps {
  message: Message;
  isStreaming?: boolean;
  onRetry?: () => void;
  onCopy?: () => void;
  onEdit?: (newContent: string) => void;
  onDelete?: () => void;
}

// 对话列表Props类型
export interface ConversationListProps {
  conversations: Conversation[];
  currentConversationId?: string;
  onSelectConversation: (conversationId: string) => void;
  onDeleteConversation: (conversationId: string) => void;
  onRenameConversation: (conversationId: string, newTitle: string) => void;
}

// 对话搜索Props类型
export interface ConversationSearchProps {
  onSendMessage: (message: string) => void;
  isLoading?: boolean;
  disabled?: boolean;
  placeholder?: string;
  maxLength?: number;
  autoFocus?: boolean;
}

// 对话统计类型
export interface ConversationStats {
  totalConversations: number;
  totalMessages: number;
  totalTokens: number;
  averageMessagesPerConversation: number;
  averageTokensPerMessage: number;
  mostUsedModel?: string;
  lastActivityTime?: number;
}
