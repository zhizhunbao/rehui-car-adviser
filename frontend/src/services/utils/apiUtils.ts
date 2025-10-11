import { logger } from "../../utils/logger";

/**
 * API 工具函数
 * 提供 API 调用相关的辅助功能
 */
export class ApiUtils {
  /**
   * 构建查询参数
   */
  static buildQueryParams(params: Record<string, any>): string {
    const searchParams = new URLSearchParams();
    
    Object.entries(params).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== "") {
        searchParams.append(key, String(value));
      }
    });
    
    return searchParams.toString();
  }

  /**
   * 构建 URL
   */
  static buildUrl(baseUrl: string, path: string, params?: Record<string, any>): string {
    const url = new URL(path, baseUrl);
    
    if (params) {
      const queryString = this.buildQueryParams(params);
      if (queryString) {
        url.search = queryString;
      }
    }
    
    return url.toString();
  }

  /**
   * 格式化错误消息
   */
  static formatErrorMessage(error: any): string {
    if (typeof error === "string") {
      return error;
    }
    
    if (error && typeof error === "object") {
      return error.message || error.error || error.detail || "未知错误";
    }
    
    return "请求失败";
  }

  /**
   * 检查响应是否成功
   */
  static isSuccessResponse(response: any): boolean {
    return response && response.success === true;
  }

  /**
   * 提取错误信息
   */
  static extractError(response: any): string {
    if (this.isSuccessResponse(response)) {
      return "";
    }
    
    return this.formatErrorMessage(response?.error || response);
  }

  /**
   * 重试机制
   */
  static async retry<T>(
    fn: () => Promise<T>,
    maxAttempts: number = 3,
    delay: number = 1000
  ): Promise<T> {
    let lastError: any;
    
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        return await fn();
      } catch (error) {
        lastError = error;
        
        if (attempt === maxAttempts) {
          logger.logResult("重试失败", `已尝试 ${maxAttempts} 次`);
          break;
        }
        
        logger.logResult("重试", `第 ${attempt} 次失败，${delay}ms 后重试`);
        await this.delay(delay);
      }
    }
    
    throw lastError;
  }

  /**
   * 延迟函数
   */
  static delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * 防抖函数
   */
  static debounce<T extends (...args: any[]) => any>(
    func: T,
    wait: number
  ): (...args: Parameters<T>) => void {
    let timeout: NodeJS.Timeout;
    
    return (...args: Parameters<T>) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => func(...args), wait);
    };
  }

  /**
   * 节流函数
   */
  static throttle<T extends (...args: any[]) => any>(
    func: T,
    limit: number
  ): (...args: Parameters<T>) => void {
    let inThrottle: boolean;
    
    return (...args: Parameters<T>) => {
      if (!inThrottle) {
        func(...args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  }

  /**
   * 生成请求 ID
   */
  static generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * 验证 API 响应格式
   */
  static validateResponse(response: any, requiredFields: string[]): boolean {
    if (!response || typeof response !== "object") {
      return false;
    }
    
    return requiredFields.every(field => field in response);
  }

  /**
   * 清理敏感数据
   */
  static sanitizeData(data: any): any {
    if (!data || typeof data !== "object") {
      return data;
    }
    
    const sensitiveFields = ["password", "token", "secret", "key"];
    const sanitized = { ...data };
    
    sensitiveFields.forEach(field => {
      if (field in sanitized) {
        sanitized[field] = "***";
      }
    });
    
    return sanitized;
  }
}
