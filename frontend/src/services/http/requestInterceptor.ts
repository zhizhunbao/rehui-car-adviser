import { InternalAxiosRequestConfig } from "axios";
import { logger } from "../../utils/logger";

/**
 * 请求拦截器
 * 处理请求前的统一逻辑
 */
export class RequestInterceptor {
  /**
   * 请求拦截器
   */
  onRequest(config: InternalAxiosRequestConfig): InternalAxiosRequestConfig {
    // 添加请求时间戳
    config.metadata = { startTime: Date.now() };

    // 记录请求日志
    logger.logResult(
      "HTTP请求",
      `${config.method?.toUpperCase()} ${config.url}`
    );

    // 添加请求 ID 用于追踪
    const requestId = this.generateRequestId();
    config.headers.set("X-Request-ID", requestId);

    // 添加时间戳防止缓存
    if (config.method === "get") {
      const separator = config.url?.includes("?") ? "&" : "?";
      config.url = `${config.url}${separator}_t=${Date.now()}`;
    }

    return config;
  }

  /**
   * 请求错误拦截器
   */
  onRequestError(error: any): Promise<any> {
    logger.logResult("请求错误", error.message);
    return Promise.reject(error);
  }

  /**
   * 生成请求 ID
   */
  private generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}
