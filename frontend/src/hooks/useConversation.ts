import { useState, useCallback, useEffect } from 'react';
import { useConversationContext } from '../contexts/conversation/ConversationContext';

// 对话相关的Hook
export const useConversation = () => {
  const context = useConversationContext();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 发送消息
  const sendMessage = useCallback(async (message: string) => {
    if (!message.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      // 调用context中的发送消息方法
      await context.sendMessage(message);
    } catch (err) {
      setError(err instanceof Error ? err.message : '发送消息失败');
    } finally {
      setIsLoading(false);
    }
  }, [context]);

  // 清除对话
  const clearConversation = useCallback(() => {
    context.clearConversation();
    setError(null);
  }, [context]);

  // 重试最后一条消息
  const retryLastMessage = useCallback(async () => {
    if (!context.messages.length) return;

    const lastUserMessage = context.messages
      .slice()
      .reverse()
      .find(msg => msg.role === 'user');

    if (lastUserMessage) {
      await sendMessage(lastUserMessage.content);
    }
  }, [context.messages, sendMessage]);

  // 获取对话统计
  const getConversationStats = useCallback(() => {
    const userMessages = context.messages.filter(msg => msg.role === 'user');
    const assistantMessages = context.messages.filter(msg => msg.role === 'assistant');
    
    return {
      totalMessages: context.messages.length,
      userMessages: userMessages.length,
      assistantMessages: assistantMessages.length,
      lastMessageTime: context.messages.length > 0 
        ? context.messages[context.messages.length - 1].timestamp 
        : null,
    };
  }, [context.messages]);

  return {
    // 状态
    messages: context.messages,
    isLoading,
    error,
    
    // 方法
    sendMessage,
    clearConversation,
    retryLastMessage,
    getConversationStats,
    
    // 工具方法
    setIsLoading,
    setError,
  };
};
