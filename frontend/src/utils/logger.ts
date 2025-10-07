/**
 * 基于 loglevel 的增强日志器
 * 满足设计文档要求：时间戳 | 执行序号 | 包名.方法名:行号 | 结论 - 原因
 */

import log from 'loglevel';

interface LogEntry {
  timestamp: string;
  sequence: string;
  callStack: string;
  message: string;
  level: string;
}

class EnhancedLogger {
  private globalSequence: number = 0;
  private loggedMessages: Set<string> = new Set();
  private isDevelopment: boolean = import.meta.env.DEV;
  private apiBaseUrl: string = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  constructor() {
    // 设置日志级别
    log.setLevel(this.isDevelopment ? 'debug' : 'info');
    
    // 自定义日志格式
    this.setupCustomFormat();
  }

  private setupCustomFormat(): void {
    const originalFactory = log.methodFactory;
    
    log.methodFactory = (methodName, logLevel, loggerName) => {
      const rawMethod = originalFactory(methodName, logLevel, loggerName);
      
      return (...args: any[]) => {
        const timestamp = this.getTimestamp();
        const sequence = this.getNextSequence();
        const callStack = this.getCallStack();
        
        // 格式化消息
        const message = args.join(' ');
        const formattedMessage = `${timestamp} | ${sequence} | ${callStack} | ${message}`;
        
        // 调用原始方法，使用格式化后的消息
        rawMethod(formattedMessage);
        
        // 发送到后端（异步）
        this.sendToBackend({
          timestamp,
          sequence,
          callStack,
          message,
          level: methodName
        });
      };
    };
    
    // 重新应用日志级别设置
    log.setLevel(this.isDevelopment ? 'debug' : 'info');
  }

  private getCallStack(): string {
    const stack = new Error().stack;
    if (!stack) return 'unknown:0';
    
    const lines = stack.split('\n');
    
    // 查找第一个不是日志器内部的调用
    for (let i = 1; i < lines.length; i++) {
      const line = lines[i];
      if (!line) continue;
      
      // 跳过日志器内部的方法
      if (line.includes('logger.ts') || 
          line.includes('EnhancedLogger') ||
          line.includes('loglevel') ||
          line.includes('methodFactory')) {
        continue;
      }
      
      // 解析调用栈
      const patterns = [
        /at\s+(.+?)\s+\((.+?):(\d+):\d+\)/,
        /at\s+(.+?):(\d+):\d+/,
        /at\s+\((.+?):(\d+):\d+\)/
      ];
      
      for (const pattern of patterns) {
        const match = line.match(pattern);
        if (match) {
          let functionName = '';
          let filePath = '';
          let lineNumber = '';
          
          if (pattern === patterns[0]) {
            [, functionName, filePath, lineNumber] = match;
          } else if (pattern === patterns[1]) {
            [, filePath, lineNumber] = match;
            functionName = 'anonymous';
          } else if (pattern === patterns[2]) {
            [, filePath, lineNumber] = match;
            functionName = 'anonymous';
          }
          
          // 清理函数名
          functionName = functionName
            .replace(/^Object\./, '')
            .replace(/^\./, '')
            .replace(/\[as\s+\w+\]/, '')
            .trim();
          
          // 转换为包名.方法名:行号格式
          const packagePath = filePath
            .replace(/\\/g, '/')
            .replace(/.*\/src\//, 'src.')
            .replace(/\.tsx?$/, '')
            .replace(/\//g, '.')
            .replace(/\?t=\d+/g, '');
          
          const result = `${packagePath}.${functionName}:${lineNumber}`;
          
          // 在开发环境下输出调试信息
          if (this.isDevelopment) {
            console.debug('Call stack parsed:', { line, result });
          }
          
          return result;
        }
      }
    }
    
    return 'unknown:0';
  }

  private getNextSequence(): string {
    this.globalSequence++;
    return this.globalSequence.toString();
  }

  private getTimestamp(): string {
    const now = new Date();
    return now.toISOString().replace('T', ' ').substring(0, 19);
  }

  private async sendToBackend(entry: LogEntry): Promise<void> {
    try {
      await fetch(`${this.apiBaseUrl}/api/logs/frontend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(entry)
      });
    } catch (error) {
      // 静默处理网络错误，避免日志发送失败影响业务
      console.warn('Failed to send log to backend:', error);
    }
  }

  // 关键部位日志方法
  logResult(conclusion: string, reason: string = ''): void {
    const message = reason ? `${conclusion} - ${reason}` : conclusion;
    
    // 防止重复日志 - 使用简单的消息作为key，避免重复调用getCallStack
    if (this.loggedMessages.has(message)) {
      return;
    }
    this.loggedMessages.add(message);
    
    log.info(message);
  }

  // 标准日志方法
  debug(message: string, ...args: any[]): void {
    log.debug(message, ...args);
  }

  info(message: string, ...args: any[]): void {
    log.info(message, ...args);
  }

  warn(message: string, ...args: any[]): void {
    log.warn(message, ...args);
  }

  error(message: string, ...args: any[]): void {
    log.error(message, ...args);
  }

  // 工具方法
  clearLoggedMessages(): void {
    this.loggedMessages.clear();
  }

  getLogStats(): { totalLogged: number; currentSequence: number } {
    return {
      totalLogged: this.loggedMessages.size,
      currentSequence: this.globalSequence
    };
  }

  setLevel(level: string): void {
    log.setLevel(level as any);
  }
}

// 创建全局实例
const enhancedLogger = new EnhancedLogger();

// 导出
export { enhancedLogger as logger };
export default enhancedLogger;

// 在开发环境下暴露到全局对象
if (import.meta.env.DEV) {
  (window as any).logger = enhancedLogger;
  (window as any).clearLogs = () => enhancedLogger.clearLoggedMessages();
  (window as any).logStats = () => enhancedLogger.getLogStats();
}
