import React, { ReactNode, useState, useCallback, useEffect, useRef } from 'react';
import { ConversationContext } from './ConversationContext';
import { 
  ConversationMessage, 
  ConversationContextType, 
  WebSocketMessage, 
  StreamResponse,
  ConversationStream 
} from '../../types';
import { apiService } from '../../services/api';
import { WebSocketService } from '../../services/websocket/websocketService';
import { logger } from '../../utils/logger';

interface ConversationProviderProps {
  children: ReactNode;
}

export const ConversationProvider: React.FC<ConversationProviderProps> = ({ children }) => {
  // 状态管理
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentMessageId, setCurrentMessageId] = useState<string | null>(null);
  
  // WebSocket 服务引用
  const wsServiceRef = useRef<WebSocketService | null>(null);
  const streamingMessageRef = useRef<string>('');

  // 初始化 WebSocket 连接
  useEffect(() => {
    const initWebSocket = async () => {
      try {
        const wsService = new WebSocketService({
          url: process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws',
          reconnectInterval: 5000,
          maxReconnectAttempts: 5,
          heartbeatInterval: 30000,
        });

        // 订阅对话消息
        wsService.subscribe('conversation', (data: ConversationStream) => {
          handleStreamingMessage(data);
        });

        // 订阅错误消息
        wsService.subscribe('error', (data: any) => {
          logger.logResult("WebSocket错误", data.message || "未知错误");
          setError(data.message || "连接出现错误");
          setIsStreaming(false);
        });

        await wsService.connect();
        wsServiceRef.current = wsService;
        
        logger.logResult("WebSocket初始化", "对话服务连接成功");
      } catch (error) {
        logger.logResult("WebSocket初始化失败", error.toString());
        // WebSocket 连接失败不影响基本功能，继续使用 HTTP API
      }
    };

    initWebSocket();

    // 清理函数
    return () => {
      if (wsServiceRef.current) {
        wsServiceRef.current.destroy();
        wsServiceRef.current = null;
      }
    };
  }, []);

  // 处理流式消息
  const handleStreamingMessage = useCallback((data: ConversationStream) => {
    if (data.messageId === currentMessageId) {
      streamingMessageRef.current += data.content;
      
      // 更新最后一条消息的内容
      setMessages(prev => {
        const newMessages = [...prev];
        const lastMessage = newMessages[newMessages.length - 1];
        if (lastMessage && lastMessage.role === 'assistant') {
          lastMessage.content = streamingMessageRef.current;
        }
        return newMessages;
      });

      if (data.isComplete) {
        setIsStreaming(false);
        setCurrentMessageId(null);
        streamingMessageRef.current = '';
        
        // 更新会话ID
        if (data.sessionId) {
          setSessionId(data.sessionId);
        }
        
        logger.logResult("流式消息完成", `消息长度: ${streamingMessageRef.current.length}`);
      }
    }
  }, [currentMessageId]);

  // 发送消息
  const sendMessage = useCallback(async (message: string) => {
    logger.logResult("开始发送消息", `消息: ${message.substring(0, 50)}...`);
    
    if (!message.trim()) {
      logger.logResult("发送消息失败", "消息内容为空");
      setError('请输入消息内容');
      return;
    }

    setIsLoading(true);
    setError(null);

    // 添加用户消息到本地状态
    const userMessage: ConversationMessage = {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);

    // 添加空的助手消息占位符
    const assistantMessage: ConversationMessage = {
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, assistantMessage]);

    try {
      // 优先使用 WebSocket 流式传输
      if (wsServiceRef.current?.isConnected()) {
        const messageId = `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        setCurrentMessageId(messageId);
        setIsStreaming(true);
        streamingMessageRef.current = '';

        // 通过 WebSocket 发送消息
        const wsMessage: WebSocketMessage = {
          id: messageId,
          type: 'conversation',
          action: 'start',
          data: {
            message,
            sessionId: sessionId || undefined,
            conversationHistory: messages
          },
          timestamp: new Date().toISOString(),
          sessionId: sessionId || undefined,
          messageId
        };

        wsServiceRef.current.sendMessage('conversation', wsMessage);
        logger.logResult("WebSocket发送", `消息ID: ${messageId}`);
      } else {
        // 回退到 HTTP API
        logger.logResult("WebSocket未连接", "使用HTTP API发送消息");
        
        const response = await apiService.sendConversationMessage({
          message,
          session_id: sessionId || undefined,
          conversation_history: messages
        });
        
        if (response.success) {
          setSessionId(response.session_id);
          setMessages(response.conversation_history);
          logger.logResult("HTTP发送成功", `AI回复长度: ${response.message.content.length}`);
        } else {
          throw new Error(response.error || '发送消息失败');
        }
      }
    } catch (err: any) {
      logger.logResult("发送消息失败", `错误: ${err.message}`);
      setError(err.message || '发送消息过程中发生错误');
      
      // 移除空的助手消息
      setMessages(prev => prev.slice(0, -1));
      
      // 添加错误消息
      const errorMessage: ConversationMessage = {
        role: 'assistant',
        content: '抱歉，我遇到了一些技术问题，请稍后再试。',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, [messages, sessionId]);

  // 清除对话
  const clearConversation = useCallback(() => {
    logger.logResult("清除对话", "重置对话状态");
    setMessages([]);
    setSessionId(null);
    setError(null);
    setIsStreaming(false);
    setCurrentMessageId(null);
    streamingMessageRef.current = '';
  }, []);

  // 重试最后一条消息
  const retryLastMessage = useCallback(async () => {
    const lastUserMessage = messages
      .slice()
      .reverse()
      .find(msg => msg.role === 'user');
    
    if (lastUserMessage) {
      // 移除最后一条助手消息（如果有的话）
      setMessages(prev => {
        const newMessages = [...prev];
        if (newMessages[newMessages.length - 1]?.role === 'assistant') {
          newMessages.pop();
        }
        return newMessages;
      });
      
      await sendMessage(lastUserMessage.content);
    }
  }, [messages, sendMessage]);

  const value: ConversationContextType = {
    messages,
    isLoading,
    error,
    sessionId,
    isStreaming,
    sendMessage,
    clearConversation,
    retryLastMessage,
  };

  return (
    <ConversationContext.Provider value={value}>
      {children}
    </ConversationContext.Provider>
  );
};
