import React from 'react';
import { Card } from '../ui/Card';
import './SearchResults.css';

interface CarData {
  id: string;
  brand: string;
  model: string;
  year: number;
  price: number;
  mileage: number;
  location: string;
  image?: string;
  features?: string[];
}

interface SearchResultsProps {
  results: CarData[];
  isLoading?: boolean;
  onCarSelect?: (car: CarData) => void;
  className?: string;
}

const SearchResults: React.FC<SearchResultsProps> = ({
  results,
  isLoading = false,
  onCarSelect,
  className = ''
}) => {
  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(price);
  };

  const formatMileage = (mileage: number) => {
    return `${(mileage / 10000).toFixed(1)}万公里`;
  };

  if (isLoading) {
    return (
      <div className={`search-results loading ${className}`}>
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p className="loading-text">正在搜索车源...</p>
        </div>
      </div>
    );
  }

  if (!results || results.length === 0) {
    return (
      <div className={`search-results empty ${className}`}>
        <div className="empty-container">
          <div className="empty-icon">🚗</div>
          <h3 className="empty-title">暂无搜索结果</h3>
          <p className="empty-description">
            请尝试调整搜索条件或稍后再试
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={`search-results ${className}`}>
      <div className="results-header">
        <h2 className="results-title">
          找到 {results.length} 个车源
        </h2>
        <div className="results-filters">
          <button className="filter-button active">全部</button>
          <button className="filter-button">价格</button>
          <button className="filter-button">里程</button>
          <button className="filter-button">年份</button>
        </div>
      </div>
      
      <div className="results-grid">
        {results.map((car) => (
          <Card
            key={car.id}
            className="car-result-card"
            onClick={() => onCarSelect?.(car)}
          >
            <div className="car-image-container">
              {car.image ? (
                <img 
                  src={car.image} 
                  alt={`${car.brand} ${car.model}`}
                  className="car-image"
                />
              ) : (
                <div className="car-image-placeholder">
                  <span className="placeholder-icon">🚗</span>
                </div>
              )}
            </div>
            
            <div className="car-info">
              <h3 className="car-title">
                {car.brand} {car.model}
              </h3>
              
              <div className="car-details">
                <div className="car-detail-item">
                  <span className="detail-label">年份</span>
                  <span className="detail-value">{car.year}年</span>
                </div>
                <div className="car-detail-item">
                  <span className="detail-label">里程</span>
                  <span className="detail-value">{formatMileage(car.mileage)}</span>
                </div>
                <div className="car-detail-item">
                  <span className="detail-label">地区</span>
                  <span className="detail-value">{car.location}</span>
                </div>
              </div>
              
              <div className="car-price">
                <span className="price-label">售价</span>
                <span className="price-value">{formatPrice(car.price)}</span>
              </div>
              
              {car.features && car.features.length > 0 && (
                <div className="car-features">
                  {car.features.slice(0, 3).map((feature, index) => (
                    <span key={index} className="feature-tag">
                      {feature}
                    </span>
                  ))}
                  {car.features.length > 3 && (
                    <span className="feature-tag more">
                      +{car.features.length - 3}
                    </span>
                  )}
                </div>
              )}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default SearchResults;
