import { AxiosResponse, AxiosError } from "axios";
import { logger } from "../../utils/logger";

/**
 * 响应拦截器
 * 处理响应后的统一逻辑
 */
export class ResponseInterceptor {
  /**
   * 响应拦截器
   */
  onResponse(response: AxiosResponse): AxiosResponse {
    // 计算请求耗时
    const startTime = response.config.metadata?.startTime;
    if (startTime) {
      const duration = Date.now() - startTime;
      logger.logResult(
        "HTTP响应",
        `${response.config.method?.toUpperCase()} ${response.config.url} - ${response.status} (${duration}ms)`
      );
    }

    // 记录响应数据大小
    const dataSize = JSON.stringify(response.data).length;
    logger.logResult("响应数据", `大小: ${dataSize} bytes`);

    return response;
  }

  /**
   * 响应错误拦截器
   */
  onResponseError(error: AxiosError): Promise<any> {
    const { response, request, message } = error;

    if (response) {
      // 服务器响应了错误状态码
      const errorMessage = this.getErrorMessage(response);
      logger.logResult(
        "HTTP错误",
        `${response.status} ${response.statusText}: ${errorMessage}`
      );
    } else if (request) {
      // 请求已发出但没有收到响应
      logger.logResult("网络错误", "请求超时或网络不可用");
    } else {
      // 其他错误
      logger.logResult("请求错误", message);
    }

    // 统一错误格式
    const unifiedError = this.createUnifiedError(error);
    return Promise.reject(unifiedError);
  }

  /**
   * 获取错误消息
   */
  private getErrorMessage(response: AxiosResponse): string {
    const data = response.data;
    
    if (typeof data === "string") {
      return data;
    }
    
    if (data && typeof data === "object") {
      return data.message || data.error || data.detail || "未知错误";
    }
    
    return response.statusText || "请求失败";
  }

  /**
   * 创建统一错误格式
   */
  private createUnifiedError(error: AxiosError): any {
    const { response, request, message } = error;

    if (response) {
      return {
        type: "HTTP_ERROR",
        status: response.status,
        statusText: response.statusText,
        message: this.getErrorMessage(response),
        data: response.data,
        url: response.config.url,
        method: response.config.method,
      };
    }

    if (request) {
      return {
        type: "NETWORK_ERROR",
        message: "网络连接失败，请检查网络设置",
        url: request.responseURL,
      };
    }

    return {
      type: "REQUEST_ERROR",
      message: message || "请求失败",
    };
  }
}

// 扩展 AxiosRequestConfig 类型
declare module "axios" {
  interface AxiosRequestConfig {
    metadata?: {
      startTime: number;
    };
  }
}
