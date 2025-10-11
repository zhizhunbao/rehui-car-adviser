import React, { useState, useEffect } from 'react';
import './RealtimeMessageDisplay.css';

export interface RealtimeMessage {
  id: string;
  type: 'progress' | 'status' | 'count' | 'error' | 'success';
  timestamp: Date;
  content: string;
  data?: any;
}

interface RealtimeMessageDisplayProps {
  messages: RealtimeMessage[];
  maxMessages?: number;
  autoScroll?: boolean;
  className?: string;
}

const RealtimeMessageDisplay: React.FC<RealtimeMessageDisplayProps> = ({
  messages,
  maxMessages = 50,
  autoScroll = true,
  className = ''
}) => {
  const [displayMessages, setDisplayMessages] = useState<RealtimeMessage[]>([]);
  const [isExpanded, setIsExpanded] = useState(false);

  // 限制消息数量并保持最新消息
  useEffect(() => {
    const limitedMessages = messages.slice(-maxMessages);
    setDisplayMessages(limitedMessages);
  }, [messages, maxMessages]);

  // 自动滚动到底部
  useEffect(() => {
    if (autoScroll && isExpanded) {
      const container = document.getElementById('realtime-messages-container');
      if (container) {
        container.scrollTop = container.scrollHeight;
      }
    }
  }, [displayMessages, autoScroll, isExpanded]);

  const getMessageIcon = (type: RealtimeMessage['type']) => {
    switch (type) {
      case 'progress':
        return '⏳';
      case 'status':
        return '📊';
      case 'count':
        return '🔢';
      case 'error':
        return '❌';
      case 'success':
        return '✅';
      default:
        return '📝';
    }
  };

  const getMessageClass = (type: RealtimeMessage['type']) => {
    return `realtime-message realtime-message--${type}`;
  };

  const formatTimestamp = (timestamp: Date) => {
    return timestamp.toLocaleTimeString('zh-CN', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const toggleExpanded = () => {
    setIsExpanded(!isExpanded);
  };

  const clearMessages = () => {
    setDisplayMessages([]);
  };

  const latestMessage = displayMessages[displayMessages.length - 1];
  const messageCount = displayMessages.length;

  return (
    <div className={`realtime-message-display ${className}`}>
      {/* 消息摘要栏 - 只有在有消息时才显示 */}
      {messageCount > 0 && (
        <div className="realtime-message-summary" onClick={toggleExpanded}>
          <div className="realtime-message-summary__content">
            <span className="realtime-message-summary__icon">
              {getMessageIcon(latestMessage.type)}
            </span>
            <span className="realtime-message-summary__text">
              {latestMessage.content}
            </span>
            <span className="realtime-message-summary__count">
              ({messageCount})
            </span>
          </div>
          <div className="realtime-message-summary__actions">
            <button
              className="realtime-message-summary__toggle"
              onClick={(e) => {
                e.stopPropagation();
                toggleExpanded();
              }}
            >
              {isExpanded ? '▲' : '▼'}
            </button>
          </div>
        </div>
      )}

      {/* 消息详情面板 */}
      {isExpanded && (
        <div className="realtime-message-panel">
          <div className="realtime-message-panel__header">
            <h3 className="realtime-message-panel__title">实时消息</h3>
            <div className="realtime-message-panel__actions">
              <button
                className="realtime-message-panel__clear"
                onClick={clearMessages}
                title="清空消息"
              >
                清空
              </button>
            </div>
          </div>
          
          <div 
            id="realtime-messages-container"
            className="realtime-message-panel__content"
          >
            {displayMessages.length === 0 ? (
              <div className="realtime-message-empty">
                <span className="realtime-message-empty__icon">📭</span>
                <span className="realtime-message-empty__text">暂无消息</span>
              </div>
            ) : (
              displayMessages.map((message) => (
                <div key={message.id} className={getMessageClass(message.type)}>
                  <div className="realtime-message__header">
                    <span className="realtime-message__icon">
                      {getMessageIcon(message.type)}
                    </span>
                    <span className="realtime-message__timestamp">
                      {formatTimestamp(message.timestamp)}
                    </span>
                  </div>
                  <div className="realtime-message__content">
                    {message.content}
                  </div>
                  {message.data && (
                    <div className="realtime-message__data">
                      <pre className="realtime-message__data-content">
                        {JSON.stringify(message.data, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default RealtimeMessageDisplay;
