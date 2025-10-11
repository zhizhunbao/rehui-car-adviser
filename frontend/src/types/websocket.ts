// WebSocket 相关类型定义

// WebSocket 消息类型
export interface WebSocketMessage {
  id: string;
  type: "conversation" | "search" | "notification" | "heartbeat" | "error";
  action: "start" | "stream" | "end" | "error" | "ping" | "pong";
  data: any;
  timestamp: string;
  sessionId?: string;
  conversationId?: string;
  messageId?: string;
}

// 流式响应类型
export interface StreamResponse {
  type: "content" | "metadata" | "done" | "error";
  data: any;
  conversationId: string;
  messageId: string;
  chunkIndex?: number;
  totalChunks?: number;
  isComplete?: boolean;
}

// 对话流类型
export interface ConversationStream {
  sessionId: string;
  messageId: string;
  content: string;
  isComplete: boolean;
  metadata?: {
    model?: string;
    tokens?: number;
    processingTime?: number;
  };
}

// WebSocket 连接状态
export type WebSocketStatus = 
  | "connecting" 
  | "connected" 
  | "disconnected" 
  | "reconnecting" 
  | "error";

// WebSocket 配置类型
export interface WebSocketConfig {
  url: string;
  protocols?: string[];
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
  timeout?: number;
  debug?: boolean;
}

// WebSocket 事件类型
export interface WebSocketEvents {
  onOpen?: (event: Event) => void;
  onClose?: (event: CloseEvent) => void;
  onError?: (event: Event) => void;
  onMessage?: (message: WebSocketMessage) => void;
  onReconnect?: (attempt: number) => void;
  onReconnectFailed?: () => void;
}

// WebSocket 服务接口
export interface WebSocketServiceInterface {
  connect(): Promise<void>;
  disconnect(): void;
  send(message: WebSocketMessage): void;
  subscribe(event: string, callback: (data: any) => void): void;
  unsubscribe(event: string, callback?: (data: any) => void): void;
  getStatus(): WebSocketStatus;
  isConnected(): boolean;
}

// 消息处理器接口
export interface MessageHandlerInterface {
  handleMessage(message: WebSocketMessage): void;
  registerHandler(type: string, handler: (data: any) => void): void;
  unregisterHandler(type: string): void;
}

// 连接管理器接口
export interface ConnectionManagerInterface {
  connect(): Promise<void>;
  disconnect(): void;
  reconnect(): Promise<void>;
  getConnectionState(): WebSocketStatus;
  setConfig(config: Partial<WebSocketConfig>): void;
}

// 心跳配置类型
export interface HeartbeatConfig {
  interval: number;
  timeout: number;
  message: string;
  enabled: boolean;
}

// 重连配置类型
export interface ReconnectConfig {
  maxAttempts: number;
  interval: number;
  backoffMultiplier: number;
  maxInterval: number;
  enabled: boolean;
}

// WebSocket 错误类型
export interface WebSocketError {
  code: number;
  reason: string;
  wasClean: boolean;
  timestamp: number;
}

// 订阅管理类型
export interface Subscription {
  id: string;
  event: string;
  callback: (data: any) => void;
  createdAt: number;
}

// WebSocket 统计信息
export interface WebSocketStats {
  connectionCount: number;
  messageCount: number;
  errorCount: number;
  reconnectCount: number;
  lastConnected?: number;
  lastDisconnected?: number;
  averageLatency?: number;
}

// 消息队列类型
export interface MessageQueue {
  messages: WebSocketMessage[];
  maxSize: number;
  add(message: WebSocketMessage): void;
  flush(): WebSocketMessage[];
  clear(): void;
}

// WebSocket 连接池类型
export interface ConnectionPool {
  connections: Map<string, WebSocket>;
  maxConnections: number;
  addConnection(id: string, ws: WebSocket): void;
  removeConnection(id: string): void;
  getConnection(id: string): WebSocket | undefined;
  getAllConnections(): WebSocket[];
  clear(): void;
}
