import React from 'react';
import { CarListing } from '../types';
import { logger } from '../utils/logger';

interface CarCardProps {
  car: CarListing;
}

const CarCard: React.FC<CarCardProps> = ({ car }) => {
  const handleClick = () => {
    logger.logResult(`用户点击车源卡片: ${car.title} (${car.price})`, `年份=${car.year}, 里程=${car.mileage}, 城市=${car.city}`);
    window.open(car.link, '_blank', 'noopener,noreferrer');
  };

  return (
    <div 
      className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow cursor-pointer border border-gray-200"
      onClick={handleClick}
    >
      <div className="p-6">
        <div className="flex justify-between items-start mb-4">
          <h3 className="text-lg font-semibold text-gray-900 line-clamp-2">
            {car.title}
          </h3>
          <span className="text-xl font-bold text-green-600 ml-4">
            {car.price}
          </span>
        </div>
        
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div className="flex items-center space-x-2">
            <span className="text-gray-500">年份:</span>
            <span className="font-medium">{car.year}</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-gray-500">里程:</span>
            <span className="font-medium">{car.mileage}</span>
          </div>
        </div>
        
        <div className="flex items-center space-x-2 mb-4">
          <span className="text-gray-500">城市:</span>
          <span className="font-medium">{car.city}</span>
        </div>
        
        <div className="flex justify-end">
          <span className="text-blue-600 hover:text-blue-800 text-sm font-medium">
            查看详情 →
          </span>
        </div>
      </div>
    </div>
  );
};

export default CarCard;
