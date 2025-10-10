#!/usr/bin/env python3
"""
车源存储服务 - 负责将爬取的车源数据存储到数据库
"""

import logging
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.utils.data.db_utils import get_sync_db_util
from app.models.schemas import CarListing
from app.models.database_models import CarListingDB
from app.utils.business.car_selection_utils import CarSelectionUtils
from app.utils.core.logger import get_logger

logger = get_logger(__name__)


class CarStorageService:
    """
    车源存储服务 - 处理车源数据的入库、更新和查询
    """
    
    def __init__(self):
        self.db_util = get_sync_db_util()
        self.selection_utils = CarSelectionUtils()
    
    async def store_car_listings(
        self, 
        car_listings: List[CarListing], 
        platform: str
    ) -> Dict[str, Any]:
        """
        批量存储车源数据到数据库
        
        Args:
            car_listings: 车源列表
            platform: 平台名称
            
        Returns:
            存储结果统计
        """
        logger.info(f"开始存储 {len(car_listings)} 个车源到数据库 (平台: {platform})")
        
        # 使用 MCP 服务存储数据
        try:
            # 将 CarListing 对象转换为字典格式
            car_data = []
            for car in car_listings:
                car_dict = {
                    'platform': platform,
                    'platform_id': car.id,
                    'title': car.title,
                    'price': car.price,
                    'mileage': car.mileage,
                    'city': car.city,
                    'link': car.link,
                    'image_url': car.image,
                    'year': car.year
                }
                car_data.append(car_dict)
            
            # 使用传统数据库存储
            stats = await self._store_car_listings_to_db(car_data, platform)
            logger.info(f"车源存储完成: {stats}")
            return stats
            
        except Exception as e:
            logger.log_result(f"批量存储车源失败: {str(e)}")
            return {
                'total': len(car_listings),
                'inserted': 0,
                'updated': 0,
                'skipped': 0,
                'errors': len(car_listings),
                'errors_detail': [str(e)]
            }
    
    async def _store_car_listings_to_db(
        self, 
        car_data: List[Dict[str, Any]], 
        platform: str
    ) -> Dict[str, Any]:
        """
        将车源数据存储到数据库
        
        Args:
            car_data: 车源数据列表
            platform: 平台名称
            
        Returns:
            存储结果统计
        """
        session = self.db_util.get_session()
        stats = {
            'total': len(car_data),
            'inserted': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0,
            'errors_detail': []
        }
        
        try:
            for car_dict in car_data:
                try:
                    # 检查是否已存在
                    existing = session.query(CarListingDB).filter(
                        CarListingDB.platform == platform,
                        CarListingDB.url == car_dict.get('link')
                    ).first()
                    
                    if existing:
                        # 更新现有记录
                        existing.title = car_dict.get('title', existing.title)
                        existing.price = car_dict.get('price', existing.price)
                        existing.mileage = car_dict.get('mileage', existing.mileage)
                        existing.city = car_dict.get('city', existing.city)
                        existing.updated_at = datetime.utcnow()
                        stats['updated'] += 1
                    else:
                        # 插入新记录
                        new_car = CarListingDB(
                            platform=platform,
                            platform_id=car_dict.get('platform_id'),
                            title=car_dict.get('title'),
                            price=car_dict.get('price'),
                            mileage=car_dict.get('mileage'),
                            city=car_dict.get('city'),
                            url=car_dict.get('link'),
                            image_url=car_dict.get('image_url'),
                            year=car_dict.get('year')
                        )
                        session.add(new_car)
                        stats['inserted'] += 1
                        
                except Exception as e:
                    stats['errors'] += 1
                    stats['errors_detail'].append(f"存储车源失败: {str(e)}")
                    logger.log_result(f"存储单个车源失败: {str(e)}")
            
            session.commit()
            logger.info(f"车源存储完成: 总计{stats['total']}, 新增{stats['inserted']}, 更新{stats['updated']}, 错误{stats['errors']}")
            
        except Exception as e:
            session.rollback()
            logger.log_result(f"批量存储车源到数据库失败: {str(e)}")
            stats['errors'] = stats['total']
            stats['errors_detail'].append(str(e))
        finally:
            session.close()
        
        return stats
    
    async def _store_single_car_listing(
        self, 
        session: Session, 
        car_listing: CarListing, 
        platform: str
    ) -> str:
        """
        存储单个车源到数据库
        
        Returns:
            'inserted', 'updated', 或 'skipped'
        """
        # 检查是否已存在 (基于平台和链接)
        existing = session.query(CarListingDB).filter(
            CarListingDB.platform == platform,
            CarListingDB.link == car_listing.link
        ).first()
        
        if existing:
            # 更新现有记录
            return await self._update_existing_car_listing(
                session, existing, car_listing
            )
        else:
            # 插入新记录
            return await self._insert_new_car_listing(
                session, car_listing, platform
            )
    
    async def _insert_new_car_listing(
        self, 
        session: Session, 
        car_listing: CarListing, 
        platform: str
    ) -> str:
        """插入新的车源记录"""
        # 解析车源信息
        parsed_info = self._parse_car_listing(car_listing)
        
        # 计算质量评分
        quality_scores = self.selection_utils.calculate_quality_scores(
            parsed_info['year'], 
            parsed_info['price'], 
            parsed_info['mileage']
        )
        
        # 创建数据库记录
        db_car = CarListingDB(
            platform=platform,
            platform_id=car_listing.id,
            title=car_listing.title,
            make=parsed_info['make'],
            model=parsed_info['model'],
            year=parsed_info['year'],
            price=parsed_info['price'],
            price_text=car_listing.price,
            mileage=parsed_info['mileage'],
            mileage_text=car_listing.mileage,
            city=car_listing.city,
            link=car_listing.link,
            image_url=car_listing.image,
            quality_score=quality_scores['quality_score'],
            price_score=quality_scores['price_score'],
            year_score=quality_scores['year_score'],
            mileage_score=quality_scores['mileage_score'],
            overall_score=quality_scores['overall_score'],
            extra_info=json.dumps(parsed_info.get('extra_info', {}), ensure_ascii=False)
        )
        
        session.add(db_car)
        return 'inserted'
    
    async def _update_existing_car_listing(
        self, 
        session: Session, 
        existing: CarListingDB, 
        car_listing: CarListing
    ) -> str:
        """更新现有的车源记录"""
        # 检查是否有实质性变化
        parsed_info = self._parse_car_listing(car_listing)
        
        # 如果价格或状态有变化，更新记录
        if (existing.price != parsed_info['price'] or 
            existing.title != car_listing.title):
            
            # 重新计算质量评分
            quality_scores = self.selection_utils.calculate_quality_scores(
                parsed_info['year'], 
                parsed_info['price'], 
                parsed_info['mileage']
            )
            
            # 更新字段
            existing.title = car_listing.title
            existing.price = parsed_info['price']
            existing.price_text = car_listing.price
            existing.mileage = parsed_info['mileage']
            existing.mileage_text = car_listing.mileage
            existing.quality_score = quality_scores['quality_score']
            existing.price_score = quality_scores['price_score']
            existing.year_score = quality_scores['year_score']
            existing.mileage_score = quality_scores['mileage_score']
            existing.overall_score = quality_scores['overall_score']
            existing.updated_at = datetime.utcnow()
            existing.last_seen_at = datetime.utcnow()
            
            return 'updated'
        else:
            # 只更新最后发现时间
            existing.last_seen_at = datetime.utcnow()
            return 'skipped'
    
    def _parse_car_listing(self, car_listing: CarListing) -> Dict[str, Any]:
        """
        解析车源信息，提取结构化数据
        """
        import re
        
        # 解析价格
        price = 0.0
        if car_listing.price:
            price_match = re.search(r'[\d,]+', car_listing.price.replace(',', ''))
            if price_match:
                price = float(price_match.group().replace(',', ''))
        
        # 解析里程
        mileage = 0
        if car_listing.mileage:
            mileage_match = re.search(r'[\d,]+', car_listing.mileage.replace(',', ''))
            if mileage_match:
                mileage = int(mileage_match.group().replace(',', ''))
        
        # 解析品牌和型号 (从标题中提取)
        make, model = self._extract_make_model(car_listing.title)
        
        # 解析年份
        year = 0
        if car_listing.year:
            year = car_listing.year
        
        return {
            'make': make,
            'model': model,
            'year': year,
            'price': price,
            'mileage': mileage,
            'extra_info': {
                'original_title': car_listing.title,
                'original_price': car_listing.price,
                'original_mileage': car_listing.mileage
            }
        }
    
    def _extract_make_model(self, title: str) -> tuple:
        """
        从标题中提取品牌和型号
        """
        # 常见的汽车品牌
        brands = [
            'Toyota', 'Honda', 'Nissan', 'Mazda', 'Subaru', 'Mitsubishi',
            'BMW', 'Mercedes-Benz', 'Audi', 'Volkswagen', 'Porsche',
            'Ford', 'Chevrolet', 'Dodge', 'Jeep', 'Chrysler',
            'Hyundai', 'Kia', 'Genesis',
            'Lexus', 'Infiniti', 'Acura', 'Cadillac', 'Lincoln',
            'Volvo', 'Saab', 'Jaguar', 'Land Rover', 'Mini',
            'Tesla', 'Ferrari', 'Lamborghini', 'Maserati', 'Bentley',
            'Rolls-Royce', 'Aston Martin', 'McLaren'
        ]
        
        title_lower = title.lower()
        make = None
        model = None
        
        # 查找品牌
        for brand in brands:
            if brand.lower() in title_lower:
                make = brand
                break
        
        # 简单的型号提取逻辑 (可以后续优化)
        if make:
            # 移除品牌名称，提取可能的型号
            remaining = title.replace(make, '').strip()
            words = remaining.split()
            if words:
                model = words[0]
        
        return make, model
    
    async def get_car_listings_by_query(
        self, 
        make: Optional[str] = None,
        model: Optional[str] = None,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
        price_max: Optional[float] = None,
        mileage_max: Optional[int] = None,
        city: Optional[str] = None,
        limit: int = 100
    ) -> List[CarListingDB]:
        """
        根据查询条件从数据库获取车源
        """
        session = self.db_manager.get_session()
        try:
            query = session.query(CarListingDB).filter(
                CarListingDB.is_active == True,
                CarListingDB.is_sold == False
            )
            
            # 应用过滤条件
            if make:
                query = query.filter(CarListingDB.make.ilike(f"%{make}%"))
            if model:
                query = query.filter(CarListingDB.model.ilike(f"%{model}%"))
            if year_min:
                query = query.filter(CarListingDB.year >= year_min)
            if year_max:
                query = query.filter(CarListingDB.year <= year_max)
            if price_max:
                query = query.filter(CarListingDB.price <= price_max)
            if mileage_max:
                query = query.filter(CarListingDB.mileage <= mileage_max)
            if city:
                query = query.filter(CarListingDB.city.ilike(f"%{city}%"))
            
            # 按质量评分排序
            query = query.order_by(CarListingDB.overall_score.desc())
            
            # 限制结果数量
            results = query.limit(limit).all()
            
            logger.info(f"数据库查询返回 {len(results)} 个车源")
            return results
            
        finally:
            session.close()
    
    async def mark_car_as_sold(self, car_id: int) -> bool:
        """标记车源为已售出"""
        session = self.db_manager.get_session()
        try:
            car = session.query(CarListingDB).filter(CarListingDB.id == car_id).first()
            if car:
                car.is_sold = True
                car.updated_at = datetime.utcnow()
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.log_result(f"标记车源为已售出失败: {str(e)}")
            return False
        finally:
            session.close()
    
    async def cleanup_old_listings(self, days: int = 30) -> int:
        """
        清理过期的车源记录
        
        Args:
            days: 超过多少天未更新的记录将被标记为无效
            
        Returns:
            清理的记录数量
        """
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        session = self.db_manager.get_session()
        try:
            # 标记过期的车源为无效
            result = session.query(CarListingDB).filter(
                CarListingDB.last_seen_at < cutoff_date,
                CarListingDB.is_active == True
            ).update({
                'is_active': False,
                'updated_at': datetime.utcnow()
            })
            
            session.commit()
            logger.info(f"清理了 {result} 个过期车源记录")
            return result
            
        except Exception as e:
            session.rollback()
            logger.log_result(f"清理过期车源失败: {str(e)}")
            return 0
        finally:
            session.close()
