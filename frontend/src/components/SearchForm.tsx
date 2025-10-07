import React, { useState } from 'react';
import { useSearch } from '../contexts/SearchContext';
import { logger } from '../utils/logger';

const SearchForm: React.FC = () => {
  const [query, setQuery] = useState('');
  const { searchCars, isLoading } = useSearch();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // 关键部位日志：用户交互入口点 - 主操作
    logger.logResult("用户提交搜索", `查询: ${query}`);
    
    if (query.trim() && !isLoading) {
      await searchCars(query.trim());
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setQuery(newValue);
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={handleInputChange}
            placeholder="请输入您的购车需求，例如：2020年后的丰田凯美瑞，预算3万加元"
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !query.trim()}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? '搜索中...' : '搜索'}
          </button>
        </div>
        <p className="text-sm text-gray-600">
          支持中英文查询，例如：Toyota Camry under $30,000 或 2020年后本田雅阁
        </p>
      </form>
    </div>
  );
};

export default SearchForm;
