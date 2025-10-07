import React from 'react';
import { SearchProvider } from './contexts/SearchContext';
import { ConversationProvider } from './contexts/ConversationContext';
import ConversationSearch from './components/ConversationSearch';
import { logger } from './utils/logger';

const App: React.FC = () => {
  // 关键部位日志：应用启动
  logger.logResult("应用启动", "Rehui Car Adviser 前端应用初始化");

  return (
    <ConversationProvider>
      <SearchProvider>
        <div className="app-container">
          <ConversationSearch />
        </div>
        <style jsx="true" global="true">{`
          * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
          }
          
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            overflow: hidden;
            direction: ltr;
            writing-mode: horizontal-tb;
            text-orientation: mixed;
            unicode-bidi: normal;
          }
          
          .app-container {
            height: 100vh;
            width: 100vw;
            overflow: hidden;
            direction: ltr;
            writing-mode: horizontal-tb;
          }
          
          input, textarea, p, div, span {
            direction: ltr !important;
            writing-mode: horizontal-tb !important;
            text-orientation: mixed !important;
            unicode-bidi: normal !important;
          }
          
          .message-text, .message-text * {
            direction: ltr !important;
            writing-mode: horizontal-tb !important;
            text-orientation: mixed !important;
            unicode-bidi: normal !important;
          }
        `}</style>
      </SearchProvider>
    </ConversationProvider>
  );
};

export default App;
