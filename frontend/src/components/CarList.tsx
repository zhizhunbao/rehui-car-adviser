import React from 'react';
import { useSearch } from '../contexts/SearchContext';
import CarCard from './CarCard';
import { logger } from '../utils/logger';

const CarList: React.FC = () => {
  const { searchResults, isLoading, error } = useSearch();

  // 记录状态变化
  React.useEffect(() => {
    if (isLoading) {
      logger.logResult("显示加载状态", "用户等待搜索结果");
    } else if (error) {
      logger.logResult("显示错误状态", `错误: ${error}`);
    } else if (searchResults.length === 0) {
      logger.logResult("显示空结果状态", "没有找到匹配的车源");
    } else {
      logger.logResult("显示搜索结果", `找到${searchResults.length}辆车源`);
    }
  }, [isLoading, searchResults.length, error]);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">正在搜索车源...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
        <div className="text-red-600 font-medium mb-2">搜索失败</div>
        <div className="text-red-500 text-sm">{error}</div>
      </div>
    );
  }

  if (searchResults.length === 0 && !isLoading) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-500 text-lg mb-2">暂无搜索结果</div>
        <div className="text-gray-400 text-sm">请尝试其他搜索条件</div>
      </div>
    );
  }
  
  return (
    <div className="space-y-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          找到 {searchResults.length} 辆车源
        </h2>
        <p className="text-gray-600">点击车源卡片查看详细信息</p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {searchResults.map((car) => (
          <CarCard key={car.id} car={car} />
        ))}
      </div>
    </div>
  );
};

export default CarList;
