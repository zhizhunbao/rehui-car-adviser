#!/usr/bin/env python3
"""
基于数据库的车源推荐服务 - 从数据库中智能选择最优车源
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.utils.data.db_utils import get_sync_db_util
from app.models.schemas import CarListing, ParsedQuery
from app.models.database_models import CarListingDB
from app.utils.business.car_selection_utils import CarSelectionUtils
from app.utils.core.logger import get_logger

logger = get_logger(__name__)


class DatabaseCarRecommendationService:
    """
    基于数据库的车源推荐服务
    """
    
    def __init__(self):
        self.db_util = get_sync_db_util()
        self.selection_utils = CarSelectionUtils()
    
    async def recommend_cars_from_database(
        self, 
        parsed_query: ParsedQuery, 
        max_results: int = 20
    ) -> List[CarListing]:
        """
        从数据库中推荐最优车源
        
        Args:
            parsed_query: 解析后的查询条件
            max_results: 最大返回结果数
            
        Returns:
            推荐的车源列表
        """
        logger.info(f"开始从数据库推荐车源: {parsed_query.make} {parsed_query.model}")
        
        try:
            # 从数据库推荐车源
            car_listings = await self._recommend_cars_from_db(
                parsed_query, max_results
            )
            logger.info(f"MCP 服务推荐了 {len(car_listings)} 个车源")
            
            # 3. 应用智能选择算法
            selected_cars = self.selection_utils.select_best_cars(
                car_listings, 
                max_results=max_results,
                ensure_diversity=True
            )
            
            logger.info(f"智能推荐选择了 {len(selected_cars)} 个最优车源")
            return selected_cars
            
        except Exception as e:
            logger.log_result(f"数据库推荐车源失败: {str(e)}")
            return []
    
    async def _recommend_cars_from_db(
        self, 
        parsed_query: ParsedQuery, 
        max_results: int = 20
    ) -> List[CarListing]:
        """
        从数据库推荐车源
        
        Args:
            parsed_query: 解析后的查询条件
            max_results: 最大返回结果数
            
        Returns:
            推荐的车源列表
        """
        try:
            # 获取候选车源
            candidate_cars = await self._get_candidate_cars_from_db(parsed_query, max_results * 3)
            
            # 转换为CarListing格式
            car_listings = []
            for db_car in candidate_cars:
                car_listing = self._db_car_to_car_listing(db_car)
                car_listings.append(car_listing)
            
            return car_listings
            
        except Exception as e:
            logger.log_result(f"从数据库推荐车源失败: {str(e)}")
            return []
    
    async def _get_candidate_cars_from_db(
        self, 
        parsed_query: ParsedQuery,
        max_candidates: int = 200
    ) -> List[CarListingDB]:
        """
        从数据库获取候选车源
        """
        session = self.db_util.get_session()
        try:
            # 构建查询
            query = session.query(CarListingDB).filter(
                CarListingDB.is_active == True,
                CarListingDB.is_sold == False
            )
            
            # 应用查询条件
            if parsed_query.make:
                query = query.filter(CarListingDB.make.ilike(f"%{parsed_query.make}%"))
            
            if parsed_query.model:
                query = query.filter(CarListingDB.model.ilike(f"%{parsed_query.model}%"))
            
            if parsed_query.year_min:
                query = query.filter(CarListingDB.year >= parsed_query.year_min)
            
            if parsed_query.year_max:
                query = query.filter(CarListingDB.year <= parsed_query.year_max)
            
            if parsed_query.price_max:
                query = query.filter(CarListingDB.price <= parsed_query.price_max)
            
            if parsed_query.mileage_max:
                query = query.filter(CarListingDB.mileage <= parsed_query.mileage_max)
            
            if parsed_query.location:
                query = query.filter(CarListingDB.city.ilike(f"%{parsed_query.location}%"))
            
            # 按质量评分排序，获取候选车源
            query = query.order_by(CarListingDB.overall_score.desc())
            candidates = query.limit(max_candidates).all()
            
            return candidates
            
        finally:
            session.close()
    
    def _db_car_to_car_listing(self, db_car: CarListingDB) -> CarListing:
        """
        将数据库车源转换为CarListing格式
        """
        return CarListing(
            id=f"{db_car.platform}_{db_car.platform_id}",
            title=db_car.title,
            price=db_car.price_text or f"${db_car.price:,.0f}" if db_car.price else "价格面议",
            year=db_car.year or 0,
            mileage=db_car.mileage_text or f"{db_car.mileage:,} km" if db_car.mileage else "里程未知",
            city=db_car.city or "位置未知",
            link=db_car.link,
            image=db_car.image_url
        )
    
    async def get_car_statistics(self) -> Dict[str, Any]:
        """
        获取车源统计信息
        """
        try:
            # 使用 MCP 服务获取统计信息
            stats = await self.db_manager.mcp_service.get_car_statistics()
            return stats
        except Exception as e:
            logger.log_result(f"获取车源统计信息失败: {str(e)}")
            return {"error": str(e)}
    
    async def update_car_quality_scores(self) -> int:
        """
        更新所有车源的质量评分
        """
        session = self.db_util.get_session()
        try:
            # 获取所有活跃车源
            cars = session.query(CarListingDB).filter(
                CarListingDB.is_active == True
            ).all()
            
            updated_count = 0
            for car in cars:
                if car.year and car.price and car.mileage:
                    # 重新计算质量评分
                    quality_scores = self.selection_utils.calculate_quality_scores(
                        car.year, car.price, car.mileage
                    )
                    
                    # 更新评分
                    car.quality_score = quality_scores['quality_score']
                    car.price_score = quality_scores['price_score']
                    car.year_score = quality_scores['year_score']
                    car.mileage_score = quality_scores['mileage_score']
                    car.overall_score = quality_scores['overall_score']
                    car.updated_at = datetime.utcnow()
                    
                    updated_count += 1
            
            session.commit()
            logger.info(f"更新了 {updated_count} 个车源的质量评分")
            return updated_count
            
        except Exception as e:
            session.rollback()
            logger.log_result(f"更新车源质量评分失败: {str(e)}")
            return 0
        finally:
            session.close()
    
    async def get_recommendation_analytics(
        self, 
        days: int = 7
    ) -> Dict[str, Any]:
        """
        获取推荐分析数据
        """
        try:
            # 使用 MCP 服务获取推荐分析数据
            analytics = await self.db_manager.mcp_service.get_recommendation_analytics()
            return analytics
        except Exception as e:
            logger.log_result(f"获取推荐分析数据失败: {str(e)}")
            return {"error": str(e)}
