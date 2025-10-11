import { logger } from "../../utils/logger";
import { WebSocketMessage } from "./websocketService";

/**
 * 消息处理器
 * 处理 WebSocket 消息的分发和订阅
 */
export class MessageHandler {
  private subscribers: Map<string, Set<(data: any) => void>> = new Map();

  /**
   * 处理接收到的消息
   */
  handleMessage(message: WebSocketMessage): void {
    const { type, data } = message;
    
    logger.logResult("收到消息", `类型: ${type}`);
    
    const callbacks = this.subscribers.get(type);
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          logger.logResult("消息处理错误", `${type}: ${error}`);
        }
      });
    }
  }

  /**
   * 订阅特定类型的消息
   */
  subscribe(type: string, callback: (data: any) => void): () => void {
    if (!this.subscribers.has(type)) {
      this.subscribers.set(type, new Set());
    }
    
    this.subscribers.get(type)!.add(callback);
    
    logger.logResult("订阅消息", `类型: ${type}`);
    
    // 返回取消订阅函数
    return () => {
      this.unsubscribe(type, callback);
    };
  }

  /**
   * 取消订阅
   */
  unsubscribe(type: string, callback: (data: any) => void): void {
    const callbacks = this.subscribers.get(type);
    if (callbacks) {
      callbacks.delete(callback);
      
      // 如果没有订阅者了，删除该类型
      if (callbacks.size === 0) {
        this.subscribers.delete(type);
      }
      
      logger.logResult("取消订阅", `类型: ${type}`);
    }
  }

  /**
   * 取消所有订阅
   */
  unsubscribeAll(): void {
    this.subscribers.clear();
    logger.logResult("消息处理器", "已清除所有订阅");
  }

  /**
   * 获取订阅统计
   */
  getSubscriptionStats(): { [type: string]: number } {
    const stats: { [type: string]: number } = {};
    this.subscribers.forEach((callbacks, type) => {
      stats[type] = callbacks.size;
    });
    return stats;
  }

  /**
   * 销毁消息处理器
   */
  destroy(): void {
    this.unsubscribeAll();
  }
}
