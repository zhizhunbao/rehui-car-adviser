import React, { useState, useRef, useEffect } from 'react';
import { useConversation } from '../../contexts';
import { logger } from '../../utils/logger.js';
import RealtimeMessageDisplay from './RealtimeMessageDisplay';
import '../../styles/components.css';

const ConversationSearch: React.FC = () => {
  const { messages, isLoading, error, sendMessage, realtimeMessages } = useConversation();
  const [inputMessage, setInputMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 快速问题示例
  const quickQuestions = [
    "我想买一辆2020年左右的丰田凯美瑞，预算3万加元",
    "帮我找一辆本田雅阁，2018-2022年，里程不超过10万公里",
    "寻找宝马X3，价格在4万加元以下，在多伦多",
    "3万预算能买什么车？",
    "2020年的丰田车有哪些选择？",
    "10万公里以内的二手车推荐"
  ];

  // 自动滚动到底部
  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  };

  // 消息变化时自动滚动到底部
  useEffect(() => {
    if (messages.length > 0) {
      scrollToBottom();
    }
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;

    // 记录用户交互日志
    logger.logResult("用户发送消息", `消息: ${inputMessage.substring(0, 50)}...`);
    
    // 发送消息
    await sendMessage(inputMessage);
    setInputMessage('');
  };

  const handleQuickQuestion = async (question: string) => {
    if (isLoading) return;

    // 记录用户交互日志
    logger.logResult("用户点击快速问题", `问题: ${question.substring(0, 50)}...`);
    
    // 发送快速问题
    await sendMessage(question);
  };

  return (
    <div className="conversation-search">
      {/* 主内容区域 */}
      <div className="main-content">
        {/* 消息区域 */}
        <div className="chat-area">
          {messages.length === 0 ? (
            <div className="welcome-screen">
              <div className="welcome-content">
                <h1 className="welcome-title">What can I help you find?</h1>
                <p className="welcome-subtitle">告诉我您的购车需求，我会帮您找到合适的车源</p>
                
                {/* 快速问题示例 */}
                <div className="quick-questions">
                  <h3 className="quick-questions-title">快速开始：</h3>
                  <div className="quick-questions-grid">
                    {quickQuestions.map((question, index) => (
                      <button
                        key={index}
                        className="quick-question-btn"
                        onClick={() => handleQuickQuestion(question)}
                        disabled={isLoading}
                      >
                        {question}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="messages-container">
              {/* 实时消息显示 - 移动到消息容器内部 */}
              <RealtimeMessageDisplay 
                messages={realtimeMessages}
                maxMessages={20}
                autoScroll={true}
                className="conversation-realtime-messages"
              />
              
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`message ${message.role === 'user' ? 'user' : 'assistant'}`}
                >
                  <div className="message-avatar">
                    {message.role === 'user' ? (
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                        <circle cx="12" cy="7" r="4"/>
                      </svg>
                    ) : (
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                      </svg>
                    )}
                  </div>
                  <div className="message-content">
                    <div className="message-text" dir="ltr">
                      {message.content.split('\n').map((line, lineIndex) => (
                        <p key={lineIndex} dir="ltr">{line}</p>
                      ))}
                    </div>
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="message assistant">
                  <div className="message-avatar">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                    </svg>
                  </div>
                  <div className="message-content">
                    <div className="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
              )}

              {error && (
                <div className="error-message">
                  <div className="error-content">
                    <span className="error-icon">❌</span>
                    <span>{error}</span>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* 输入区域 */}
        <div className="input-section">
          <form onSubmit={handleSubmit} className="input-form">
            <div className="input-container">
              {/* 输入框 */}
              <div className="input-primary">
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder="Ask anything"
                  disabled={isLoading}
                  className="message-input"
                  dir="ltr"
                />
              </div>
              
              {/* 右侧按钮 */}
              <div className="input-trailing">
                <div className="input-actions">
                  <button 
                    type="submit" 
                    className="send-button"
                    disabled={!inputMessage.trim() || isLoading}
                    title="发送消息"
                  >
                    {isLoading ? (
                      <div className="loading-spinner"></div>
                    ) : (
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <line x1="22" y1="2" x2="11" y2="13"/>
                        <polygon points="22,2 15,22 11,13 2,9 22,2"/>
                      </svg>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ConversationSearch;