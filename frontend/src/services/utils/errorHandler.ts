import { logger } from "../../utils/logger";

export interface ErrorInfo {
  type: string;
  message: string;
  code?: string | number;
  details?: any;
  timestamp: number;
  stack?: string;
}

export interface ErrorHandlerOptions {
  showNotification?: boolean;
  logError?: boolean;
  fallbackMessage?: string;
}

/**
 * 统一错误处理器
 * 提供错误处理、日志记录和用户通知功能
 */
export class ErrorHandler {
  private static instance: ErrorHandler;
  private errorCallbacks: Set<(error: ErrorInfo) => void> = new Set();

  /**
   * 获取单例实例
   */
  static getInstance(): ErrorHandler {
    if (!ErrorHandler.instance) {
      ErrorHandler.instance = new ErrorHandler();
    }
    return ErrorHandler.instance;
  }

  /**
   * 处理错误
   */
  handleError(
    error: any,
    context?: string,
    options: ErrorHandlerOptions = {}
  ): ErrorInfo {
    const {
      showNotification = true,
      logError = true,
      fallbackMessage = "操作失败，请稍后重试"
    } = options;

    const errorInfo = this.createErrorInfo(error, context);

    // 记录错误日志
    if (logError) {
      this.logError(errorInfo);
    }

    // 显示用户通知
    if (showNotification) {
      this.showNotification(errorInfo, fallbackMessage);
    }

    // 触发错误回调
    this.notifyErrorCallbacks(errorInfo);

    return errorInfo;
  }

  /**
   * 创建错误信息对象
   */
  private createErrorInfo(error: any, context?: string): ErrorInfo {
    const timestamp = Date.now();
    
    if (error instanceof Error) {
      return {
        type: "Error",
        message: error.message,
        code: (error as any).code,
        details: (error as any).details,
        timestamp,
        stack: error.stack,
      };
    }

    if (typeof error === "string") {
      return {
        type: "StringError",
        message: error,
        timestamp,
      };
    }

    if (error && typeof error === "object") {
      return {
        type: error.type || "ObjectError",
        message: error.message || error.error || "未知错误",
        code: error.code || error.status,
        details: error.details || error.data,
        timestamp,
        stack: error.stack,
      };
    }

    return {
      type: "UnknownError",
      message: "未知错误",
      timestamp,
    };
  }

  /**
   * 记录错误日志
   */
  private logError(errorInfo: ErrorInfo): void {
    const logMessage = `错误 [${errorInfo.type}]: ${errorInfo.message}`;
    
    if (errorInfo.code) {
      logger.logResult(logMessage, `代码: ${errorInfo.code}`);
    } else {
      logger.logResult(logMessage, "");
    }

    if (errorInfo.stack) {
      logger.logResult("错误堆栈", errorInfo.stack);
    }

    if (errorInfo.details) {
      logger.logResult("错误详情", JSON.stringify(errorInfo.details));
    }
  }

  /**
   * 显示用户通知
   */
  private showNotification(errorInfo: ErrorInfo, fallbackMessage: string): void {
    const message = errorInfo.message || fallbackMessage;
    
    // 这里可以集成通知组件，比如 toast 或 modal
    console.warn("用户通知:", message);
    
    // 实际项目中可以这样使用：
    // toast.error(message);
    // 或者
    // notification.error({
    //   message: "错误",
    //   description: message,
    // });
  }

  /**
   * 通知错误回调
   */
  private notifyErrorCallbacks(errorInfo: ErrorInfo): void {
    this.errorCallbacks.forEach(callback => {
      try {
        callback(errorInfo);
      } catch (callbackError) {
        logger.logResult("错误回调失败", callbackError.toString());
      }
    });
  }

  /**
   * 注册错误回调
   */
  onError(callback: (error: ErrorInfo) => void): () => void {
    this.errorCallbacks.add(callback);
    
    // 返回取消注册函数
    return () => {
      this.errorCallbacks.delete(callback);
    };
  }

  /**
   * 处理 HTTP 错误
   */
  handleHttpError(error: any, context?: string): ErrorInfo {
    let message = "网络请求失败";
    let type = "HttpError";

    if (error.response) {
      // 服务器响应了错误状态码
      const status = error.response.status;
      const statusText = error.response.statusText;
      
      switch (status) {
        case 400:
          message = "请求参数错误";
          break;
        case 401:
          message = "未授权，请重新登录";
          break;
        case 403:
          message = "权限不足";
          break;
        case 404:
          message = "请求的资源不存在";
          break;
        case 500:
          message = "服务器内部错误";
          break;
        default:
          message = `请求失败 (${status} ${statusText})`;
      }
      
      type = `HttpError_${status}`;
    } else if (error.request) {
      // 请求已发出但没有收到响应
      message = "网络连接失败，请检查网络设置";
      type = "NetworkError";
    } else {
      // 其他错误
      message = error.message || "请求失败";
      type = "RequestError";
    }

    return this.handleError(
      { type, message, code: error.response?.status },
      context,
      { showNotification: true, logError: true }
    );
  }

  /**
   * 处理 WebSocket 错误
   */
  handleWebSocketError(error: any, context?: string): ErrorInfo {
    return this.handleError(
      {
        type: "WebSocketError",
        message: error.message || "WebSocket 连接失败",
        code: error.code,
      },
      context,
      { showNotification: true, logError: true }
    );
  }

  /**
   * 处理验证错误
   */
  handleValidationError(errors: any[], context?: string): ErrorInfo {
    const message = errors.length === 1 
      ? errors[0].message 
      : `发现 ${errors.length} 个验证错误`;

    return this.handleError(
      {
        type: "ValidationError",
        message,
        details: errors,
      },
      context,
      { showNotification: true, logError: true }
    );
  }

  /**
   * 清除所有错误回调
   */
  clearErrorCallbacks(): void {
    this.errorCallbacks.clear();
  }
}

// 导出单例实例
export const errorHandler = ErrorHandler.getInstance();
