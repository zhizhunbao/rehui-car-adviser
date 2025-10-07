import React from 'react';
import { SearchProvider } from './contexts/SearchContext';
import SearchForm from './components/SearchForm';
import CarList from './components/CarList';
import { logger } from './utils/logger';

const App: React.FC = () => {
  // 关键部位日志：应用启动
  logger.logResult("应用启动", "Rehui Car Adviser 前端应用初始化");

  return (
    <SearchProvider>
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="text-center">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Rehui Car Adviser
              </h1>
              <p className="text-gray-600">
                智能搜车顾问 - 用自然语言找到您的理想座驾
              </p>
            </div>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="space-y-8">
            <SearchForm />
            <CarList />
          </div>
        </main>

        <footer className="bg-white border-t mt-16">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="text-center text-gray-500 text-sm">
              <p>© 2024 Rehui Car Adviser. 为加拿大用户提供智能搜车服务。</p>
            </div>
          </div>
        </footer>
      </div>
    </SearchProvider>
  );
};

export default App;
