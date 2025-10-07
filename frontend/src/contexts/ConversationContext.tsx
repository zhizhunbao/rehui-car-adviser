import React, { createContext, useContext, useState, ReactNode } from 'react';
import { ConversationMessage, ConversationContextType } from '../types';
import { sendConversationMessage } from '../services/api';
import { logger } from '../utils/logger.js';

const ConversationContext = createContext<ConversationContextType | undefined>(undefined);

export const useConversation = () => {
  const context = useContext(ConversationContext);
  if (context === undefined) {
    throw new Error('useConversation must be used within a ConversationProvider');
  }
  return context;
};

interface ConversationProviderProps {
  children: ReactNode;
}

export const ConversationProvider: React.FC<ConversationProviderProps> = ({ children }) => {
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const sendMessage = async (message: string) => {
    // 关键部位日志：主要业务函数入口 - 子操作
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

    try {
      // 关键部位日志：外部调用 - API请求
      const response = await sendConversationMessage({
        message,
        session_id: sessionId || undefined,
        conversation_history: messages
      });
      
      if (response.success) {
        // 关键部位日志：状态变化 - 更新对话状态
        setSessionId(response.session_id);
        setMessages(response.conversation_history);
        logger.logResult("发送消息成功", `AI回复长度: ${response.message.length}`);
      } else {
        logger.logResult("发送消息失败", `错误: ${response.error}`);
        setError(response.error || '发送消息失败');
        
        // 添加错误消息到对话中
        const errorMessage: ConversationMessage = {
          role: 'assistant',
          content: response.message || '抱歉，我遇到了一些技术问题。',
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } catch (err) {
      // 关键部位日志：错误处理
      logger.logResult("发送消息失败", `未预期错误: ${err}`);
      setError('发送消息过程中发生错误');
      
      // 添加错误消息到对话中
      const errorMessage: ConversationMessage = {
        role: 'assistant',
        content: '抱歉，我遇到了一些技术问题，请稍后再试。',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const clearConversation = () => {
    // 关键部位日志：状态变化 - 清除对话
    logger.logResult("清除对话", "重置对话状态");
    setMessages([]);
    setSessionId(null);
    setError(null);
  };

  const value: ConversationContextType = {
    messages,
    isLoading,
    error,
    sessionId,
    sendMessage,
    clearConversation,
  };

  return (
    <ConversationContext.Provider value={value}>
      {children}
    </ConversationContext.Provider>
  );
};
