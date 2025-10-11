import React, { createContext, useContext, useState, ReactNode } from 'react';
import { CarListing, SearchContextType } from '../../types';
import { searchCars } from '../../services/api';
import { logger } from '../../utils/logger.js';

const SearchContext = createContext<SearchContextType | undefined>(undefined);

export const useSearch = () => {
  const context = useContext(SearchContext);
  if (context === undefined) {
    throw new Error('useSearch must be used within a SearchProvider');
  }
  return context;
};

interface SearchProviderProps {
  children: ReactNode;
}

export const SearchProvider: React.FC<SearchProviderProps> = ({ children }) => {
  const [searchResults, setSearchResults] = useState<CarListing[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const searchCarsHandler = async (query: string) => {
    // 关键部位日志：主要业务函数入口 - 子操作
    logger.logResult("开始搜索流程", `查询: ${query}`);
    
    if (!query.trim()) {
      logger.logResult("搜索失败", "查询内容为空");
      setError('请输入搜索内容');
      return;
    }

    setIsLoading(true);
    setError(null);
    setSearchResults([]);

    try {
      // 关键部位日志：外部调用 - API请求
      const response = await searchCars(query);
      
      if (response.success && response.data) {
        // 关键部位日志：状态变化 - 更新搜索结果
        setSearchResults(response.data);
        logger.logResult("搜索成功", `返回${response.data.length}条结果`);
      } else {
        logger.logResult("搜索失败", `错误: ${response.error}`);
        setError(response.error || '搜索失败');
      }
    } catch (err) {
      // 关键部位日志：错误处理
      logger.logResult("搜索失败", `未预期错误: ${err}`);
      setError('搜索过程中发生错误');
    } finally {
      setIsLoading(false);
    }
  };

  const value: SearchContextType = {
    searchResults,
    isLoading,
    error,
    searchCars: searchCarsHandler,
  };

  return (
    <SearchContext.Provider value={value}>
      {children}
    </SearchContext.Provider>
  );
};
