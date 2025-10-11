import { logger } from "../../utils/logger";

/**
 * 连接管理器
 * 管理 WebSocket 连接状态和重连逻辑
 */
export class ConnectionManager {
  private isConnected = false;
  private reconnectAttempts = 0;
  private lastConnectTime: number | null = null;
  private lastDisconnectTime: number | null = null;

  /**
   * 设置连接状态
   */
  setConnected(connected: boolean): void {
    const wasConnected = this.isConnected;
    this.isConnected = connected;
    
    if (connected && !wasConnected) {
      this.lastConnectTime = Date.now();
      this.reconnectAttempts = 0;
      logger.logResult("连接状态", "已连接");
    } else if (!connected && wasConnected) {
      this.lastDisconnectTime = Date.now();
      logger.logResult("连接状态", "已断开");
    }
  }

  /**
   * 获取连接状态
   */
  getConnected(): boolean {
    return this.isConnected;
  }

  /**
   * 增加重连尝试次数
   */
  incrementReconnectAttempts(): void {
    this.reconnectAttempts++;
    logger.logResult("重连尝试", `第 ${this.reconnectAttempts} 次`);
  }

  /**
   * 获取重连尝试次数
   */
  getReconnectAttempts(): number {
    return this.reconnectAttempts;
  }

  /**
   * 重置重连尝试次数
   */
  resetReconnectAttempts(): void {
    this.reconnectAttempts = 0;
  }

  /**
   * 获取连接持续时间
   */
  getConnectionDuration(): number | null {
    if (!this.isConnected || !this.lastConnectTime) {
      return null;
    }
    return Date.now() - this.lastConnectTime;
  }

  /**
   * 获取断开持续时间
   */
  getDisconnectionDuration(): number | null {
    if (this.isConnected || !this.lastDisconnectTime) {
      return null;
    }
    return Date.now() - this.lastDisconnectTime;
  }

  /**
   * 获取连接统计信息
   */
  getConnectionStats(): {
    isConnected: boolean;
    reconnectAttempts: number;
    connectionDuration: number | null;
    disconnectionDuration: number | null;
    lastConnectTime: number | null;
    lastDisconnectTime: number | null;
  } {
    return {
      isConnected: this.isConnected,
      reconnectAttempts: this.reconnectAttempts,
      connectionDuration: this.getConnectionDuration(),
      disconnectionDuration: this.getDisconnectionDuration(),
      lastConnectTime: this.lastConnectTime,
      lastDisconnectTime: this.lastDisconnectTime,
    };
  }

  /**
   * 重置连接管理器
   */
  reset(): void {
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.lastConnectTime = null;
    this.lastDisconnectTime = null;
    logger.logResult("连接管理器", "已重置");
  }
}
