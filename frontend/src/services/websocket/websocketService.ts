import { logger } from "../../utils/logger";
import { MessageHandler } from "./messageHandler";
import { ConnectionManager } from "./connectionManager";

export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: number;
}

export interface WebSocketConfig {
  url: string;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  heartbeatInterval?: number;
}

/**
 * WebSocket 服务类
 * 提供实时通信功能
 */
export class WebSocketService {
  private ws: WebSocket | null = null;
  private config: WebSocketConfig;
  private messageHandler: MessageHandler;
  private connectionManager: ConnectionManager;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private isConnecting = false;
  private isDestroyed = false;

  constructor(config: WebSocketConfig) {
    this.config = {
      reconnectInterval: 5000,
      maxReconnectAttempts: 5,
      heartbeatInterval: 30000,
      ...config,
    };
    
    this.messageHandler = new MessageHandler();
    this.connectionManager = new ConnectionManager();
  }

  /**
   * 连接 WebSocket
   */
  async connect(): Promise<void> {
    if (this.isConnecting || this.isDestroyed) {
      return;
    }

    this.isConnecting = true;
    
    try {
      await this.establishConnection();
      this.isConnecting = false;
    } catch (error) {
      this.isConnecting = false;
      throw error;
    }
  }

  /**
   * 建立 WebSocket 连接
   */
  private async establishConnection(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.config.url);

        this.ws.onopen = () => {
          logger.logResult("WebSocket连接", "连接成功");
          this.connectionManager.setConnected(true);
          this.startHeartbeat();
          resolve();
        };

        this.ws.onmessage = (event) => {
          this.handleMessage(event);
        };

        this.ws.onclose = (event) => {
          logger.logResult("WebSocket连接", `连接关闭: ${event.code} ${event.reason}`);
          this.connectionManager.setConnected(false);
          this.stopHeartbeat();
          this.handleReconnect();
        };

        this.ws.onerror = (error) => {
          logger.logResult("WebSocket错误", error.toString());
          this.connectionManager.setConnected(false);
          reject(error);
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * 处理接收到的消息
   */
  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      this.messageHandler.handleMessage(message);
    } catch (error) {
      logger.logResult("消息解析错误", error.toString());
    }
  }

  /**
   * 发送消息
   */
  sendMessage(type: string, data: any): boolean {
    if (!this.isConnected()) {
      logger.logResult("发送消息失败", "WebSocket 未连接");
      return false;
    }

    const message: WebSocketMessage = {
      type,
      data,
      timestamp: Date.now(),
    };

    try {
      this.ws!.send(JSON.stringify(message));
      logger.logResult("发送消息", `类型: ${type}`);
      return true;
    } catch (error) {
      logger.logResult("发送消息错误", error.toString());
      return false;
    }
  }

  /**
   * 订阅消息
   */
  subscribe(type: string, callback: (data: any) => void): () => void {
    return this.messageHandler.subscribe(type, callback);
  }

  /**
   * 检查连接状态
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * 获取连接状态
   */
  getConnectionState(): string {
    if (!this.ws) return "DISCONNECTED";
    
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING:
        return "CONNECTING";
      case WebSocket.OPEN:
        return "CONNECTED";
      case WebSocket.CLOSING:
        return "CLOSING";
      case WebSocket.CLOSED:
        return "CLOSED";
      default:
        return "UNKNOWN";
    }
  }

  /**
   * 开始心跳检测
   */
  private startHeartbeat(): void {
    this.stopHeartbeat();
    
    this.heartbeatTimer = setInterval(() => {
      if (this.isConnected()) {
        this.sendMessage("heartbeat", { timestamp: Date.now() });
      }
    }, this.config.heartbeatInterval);
  }

  /**
   * 停止心跳检测
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  /**
   * 处理重连逻辑
   */
  private handleReconnect(): void {
    if (this.isDestroyed) return;

    const attempts = this.connectionManager.getReconnectAttempts();
    
    if (attempts < this.config.maxReconnectAttempts!) {
      logger.logResult("WebSocket重连", `尝试 ${attempts + 1}/${this.config.maxReconnectAttempts}`);
      
      this.reconnectTimer = setTimeout(() => {
        this.connectionManager.incrementReconnectAttempts();
        this.connect().catch(() => {
          // 重连失败，继续重试
        });
      }, this.config.reconnectInterval);
    } else {
      logger.logResult("WebSocket重连", "达到最大重连次数，停止重连");
    }
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    this.isDestroyed = true;
    this.stopHeartbeat();
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.ws) {
      this.ws.close(1000, "主动断开连接");
      this.ws = null;
    }

    this.connectionManager.setConnected(false);
    logger.logResult("WebSocket连接", "已断开");
  }

  /**
   * 销毁服务
   */
  destroy(): void {
    this.disconnect();
    this.messageHandler.destroy();
    this.connectionManager.reset();
  }
}
