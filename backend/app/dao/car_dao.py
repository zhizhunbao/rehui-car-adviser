#!/usr/bin/env python3
"""
车源 DAO - 处理车源相关的数据库操作
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, asc, desc
from sqlalchemy.orm import Session

from app.dao.base_dao import BaseDAO
from app.models.database_models import (
    CarListingDB,
    CarRecommendationLog,
    CarSearchHistory,
)
from app.models.schemas import CarListing, ParsedQuery
from app.utils.core.logger import get_logger

logger = get_logger(__name__)


class CarDAO(BaseDAO[CarListingDB]):
    """
    车源 DAO
    处理车源相关的数据库操作
    """

    def __init__(self):
        super().__init__(CarListingDB)

    def get_table_name(self) -> str:
        return "car_listings"

    def get_by_platform_and_id(
        self, platform: str, platform_id: str
    ) -> Optional[CarListingDB]:
        """
        根据平台和平台ID获取车源

        Args:
            platform: 平台名称
            platform_id: 平台内部ID

        Returns:
            车源记录或None
        """
        with self.get_session() as session:
            return (
                session.query(CarListingDB)
                .filter(
                    and_(
                        CarListingDB.platform == platform,
                        CarListingDB.platform_id == platform_id,
                    )
                )
                .first()
            )

    def get_by_link(self, link: str) -> Optional[CarListingDB]:
        """
        根据链接获取车源

        Args:
            link: 车源链接

        Returns:
            车源记录或None
        """
        with self.get_session() as session:
            return (
                session.query(CarListingDB)
                .filter(CarListingDB.link == link)
                .first()
            )

    def search_cars(
        self,
        make: Optional[str] = None,
        model: Optional[str] = None,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
        price_min: Optional[int] = None,
        price_max: Optional[int] = None,
        mileage_max: Optional[int] = None,
        city: Optional[str] = None,
        province: Optional[str] = None,
        platform: Optional[str] = None,
        is_active: bool = True,
        is_sold: bool = False,
        min_score: Optional[float] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "overall_score",
        order_direction: str = "desc",
    ) -> List[CarListingDB]:
        """
        搜索车源

        Args:
            make: 品牌
            model: 型号
            year_min: 最小年份
            year_max: 最大年份
            price_min: 最低价格
            price_max: 最高价格
            mileage_max: 最大里程
            city: 城市
            province: 省份
            platform: 平台
            is_active: 是否有效
            is_sold: 是否已售出
            min_score: 最低评分
            limit: 限制数量
            offset: 偏移量
            order_by: 排序字段
            order_direction: 排序方向

        Returns:
            车源列表
        """
        with self.get_session() as session:
            query = session.query(CarListingDB)

            # 基础过滤条件
            filters = [
                CarListingDB.is_active == is_active,
                CarListingDB.is_sold == is_sold,
            ]

            # 添加搜索条件
            if make:
                filters.append(CarListingDB.make.ilike(f"%{make}%"))
            if model:
                filters.append(CarListingDB.model.ilike(f"%{model}%"))
            if year_min:
                filters.append(CarListingDB.year >= year_min)
            if year_max:
                filters.append(CarListingDB.year <= year_max)
            if price_min:
                filters.append(CarListingDB.price >= price_min)
            if price_max:
                filters.append(CarListingDB.price <= price_max)
            if mileage_max:
                filters.append(CarListingDB.mileage <= mileage_max)
            if city:
                filters.append(CarListingDB.city.ilike(f"%{city}%"))
            if province:
                filters.append(CarListingDB.province.ilike(f"%{province}%"))
            if platform:
                filters.append(CarListingDB.platform == platform)
            if min_score:
                filters.append(CarListingDB.overall_score >= min_score)

            # 应用过滤条件
            if filters:
                query = query.filter(and_(*filters))

            # 排序
            order_column = getattr(
                CarListingDB, order_by, CarListingDB.overall_score
            )
            if order_direction.lower() == "desc":
                query = query.order_by(desc(order_column))
            else:
                query = query.order_by(asc(order_column))

            # 分页
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)

            return query.all()

    def search_cars_by_parsed_query(
        self, parsed_query: ParsedQuery, max_results: int = 100
    ) -> List[CarListingDB]:
        """
        根据解析后的查询条件搜索车源

        Args:
            parsed_query: 解析后的查询条件
            max_results: 最大结果数

        Returns:
            车源列表
        """
        return self.search_cars(
            make=parsed_query.make,
            model=parsed_query.model,
            year_min=parsed_query.year_min,
            year_max=parsed_query.year_max,
            price_max=parsed_query.price_max,
            mileage_max=parsed_query.mileage_max,
            city=parsed_query.location,
            limit=max_results,
        )

    def get_recommended_cars(
        self,
        parsed_query: ParsedQuery,
        max_candidates: int = 200,
        max_results: int = 20,
    ) -> List[CarListingDB]:
        """
        获取推荐车源

        Args:
            parsed_query: 解析后的查询条件
            max_candidates: 最大候选数量
            max_results: 最大结果数量

        Returns:
            推荐车源列表
        """
        # 获取候选车源
        candidates = self.search_cars_by_parsed_query(
            parsed_query, max_candidates
        )

        # 按评分排序并返回前N个
        candidates.sort(key=lambda x: x.overall_score or 0, reverse=True)
        return candidates[:max_results]

    def upsert_car_listing(
        self,
        car_listing: CarListing,
        platform: str,
        quality_scores: Optional[Dict[str, float]] = None,
    ) -> Tuple[CarListingDB, str]:
        """
        插入或更新车源

        Args:
            car_listing: 车源信息
            platform: 平台名称
            quality_scores: 质量评分

        Returns:
            (车源记录, 操作类型: 'inserted'/'updated'/'skipped')
        """
        with self.get_session() as session:
            # 检查是否已存在
            existing = (
                session.query(CarListingDB)
                .filter(
                    and_(
                        CarListingDB.platform == platform,
                        CarListingDB.link == car_listing.link,
                    )
                )
                .first()
            )

            if existing:
                # 更新现有记录
                return self._update_existing_car_listing(
                    session, existing, car_listing, quality_scores
                )
            else:
                # 插入新记录
                return self._insert_new_car_listing(
                    session, car_listing, platform, quality_scores
                )

    def _insert_new_car_listing(
        self,
        session: Session,
        car_listing: CarListing,
        platform: str,
        quality_scores: Optional[Dict[str, float]] = None,
    ) -> Tuple[CarListingDB, str]:
        """插入新的车源记录"""
        # 解析车源信息
        parsed_info = self._parse_car_listing(car_listing)

        # 创建数据库记录
        db_car = CarListingDB(
            platform=platform,
            platform_id=car_listing.id,
            title=car_listing.title,
            make=parsed_info["make"],
            model=parsed_info["model"],
            year=parsed_info["year"],
            price=parsed_info["price"],
            price_text=car_listing.price,
            mileage=parsed_info["mileage"],
            mileage_text=car_listing.mileage,
            city=car_listing.city,
            link=car_listing.link,
            image_url=car_listing.image,
            quality_score=(
                quality_scores.get("quality_score") if quality_scores else None
            ),
            price_score=(
                quality_scores.get("price_score") if quality_scores else None
            ),
            year_score=(
                quality_scores.get("year_score") if quality_scores else None
            ),
            mileage_score=(
                quality_scores.get("mileage_score") if quality_scores else None
            ),
            overall_score=(
                quality_scores.get("overall_score") if quality_scores else None
            ),
            extra_info=parsed_info.get("extra_info", {}),
        )

        session.add(db_car)
        session.flush()
        return db_car, "inserted"

    def _update_existing_car_listing(
        self,
        session: Session,
        existing: CarListingDB,
        car_listing: CarListing,
        quality_scores: Optional[Dict[str, float]] = None,
    ) -> Tuple[CarListingDB, str]:
        """更新现有的车源记录"""
        # 检查是否有实质性变化
        parsed_info = self._parse_car_listing(car_listing)

        # 如果价格或状态有变化，更新记录
        if (
            existing.price != parsed_info["price"]
            or existing.title != car_listing.title
        ):

            # 更新字段
            existing.title = car_listing.title
            existing.price = parsed_info["price"]
            existing.price_text = car_listing.price
            existing.mileage = parsed_info["mileage"]
            existing.mileage_text = car_listing.mileage
            existing.updated_at = datetime.utcnow()
            existing.last_seen_at = datetime.utcnow()

            # 更新评分
            if quality_scores:
                existing.quality_score = quality_scores.get("quality_score")
                existing.price_score = quality_scores.get("price_score")
                existing.year_score = quality_scores.get("year_score")
                existing.mileage_score = quality_scores.get("mileage_score")
                existing.overall_score = quality_scores.get("overall_score")

            return existing, "updated"
        else:
            # 只更新最后发现时间
            existing.last_seen_at = datetime.utcnow()
            return existing, "skipped"

    def _parse_car_listing(self, car_listing: CarListing) -> Dict[str, Any]:
        """解析车源信息，提取结构化数据"""
        import re

        # 解析价格
        price = 0.0
        if car_listing.price:
            price_match = re.search(
                r"[\d,]+", car_listing.price.replace(",", "")
            )
            if price_match:
                price = float(price_match.group().replace(",", ""))

        # 解析里程
        mileage = 0
        if car_listing.mileage:
            mileage_match = re.search(
                r"[\d,]+", car_listing.mileage.replace(",", "")
            )
            if mileage_match:
                mileage = int(mileage_match.group().replace(",", ""))

        # 解析品牌和型号 (从标题中提取)
        make, model = self._extract_make_model(car_listing.title)

        # 解析年份
        year = 0
        if car_listing.year:
            year = car_listing.year

        return {
            "make": make,
            "model": model,
            "year": year,
            "price": price,
            "mileage": mileage,
            "extra_info": {
                "original_title": car_listing.title,
                "original_price": car_listing.price,
                "original_mileage": car_listing.mileage,
            },
        }

    def _extract_make_model(
        self, title: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """从标题中提取品牌和型号"""
        # 常见的汽车品牌
        brands = [
            "Toyota",
            "Honda",
            "Nissan",
            "Mazda",
            "Subaru",
            "Mitsubishi",
            "BMW",
            "Mercedes-Benz",
            "Audi",
            "Volkswagen",
            "Porsche",
            "Ford",
            "Chevrolet",
            "Dodge",
            "Jeep",
            "Chrysler",
            "Hyundai",
            "Kia",
            "Genesis",
            "Lexus",
            "Infiniti",
            "Acura",
            "Cadillac",
            "Lincoln",
            "Volvo",
            "Saab",
            "Jaguar",
            "Land Rover",
            "Mini",
            "Tesla",
            "Ferrari",
            "Lamborghini",
            "Maserati",
            "Bentley",
            "Rolls-Royce",
            "Aston Martin",
            "McLaren",
        ]

        title_lower = title.lower()
        make = None
        model = None

        # 查找品牌
        for brand in brands:
            if brand.lower() in title_lower:
                make = brand
                break

        # 简单的型号提取逻辑
        if make:
            remaining = title.replace(make, "").strip()
            words = remaining.split()
            if words:
                model = words[0]

        return make, model

    def mark_as_sold(self, car_id: int) -> bool:
        """标记车源为已售出"""
        with self.get_session() as session:
            car = (
                session.query(CarListingDB)
                .filter(CarListingDB.id == car_id)
                .first()
            )

            if car:
                car.is_sold = True
                car.updated_at = datetime.utcnow()
                return True
            return False

    def mark_as_inactive(self, car_id: int) -> bool:
        """标记车源为无效"""
        with self.get_session() as session:
            car = (
                session.query(CarListingDB)
                .filter(CarListingDB.id == car_id)
                .first()
            )

            if car:
                car.is_active = False
                car.updated_at = datetime.utcnow()
                return True
            return False

    def cleanup_old_listings(self, days: int = 30) -> int:
        """
        清理过期的车源记录

        Args:
            days: 超过多少天未更新的记录将被标记为无效

        Returns:
            清理的记录数量
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        with self.get_session() as session:
            result = (
                session.query(CarListingDB)
                .filter(
                    and_(
                        CarListingDB.last_seen_at < cutoff_date,
                        CarListingDB.is_active == True,
                    )
                )
                .update({"is_active": False, "updated_at": datetime.utcnow()})
            )

            return result

    def get_statistics(self) -> Dict[str, Any]:
        """获取车源统计信息"""
        with self.get_session() as session:
            total = session.query(CarListingDB).count()
            active = (
                session.query(CarListingDB)
                .filter(CarListingDB.is_active == True)
                .count()
            )
            sold = (
                session.query(CarListingDB)
                .filter(CarListingDB.is_sold == True)
                .count()
            )

            # 按平台统计
            platform_stats = session.execute(
                """
                SELECT platform, COUNT(*) as count
                FROM car_listings
                WHERE is_active = true
                GROUP BY platform
            """
            ).fetchall()

            return {
                "total": total,
                "active": active,
                "sold": sold,
                "platforms": {row[0]: row[1] for row in platform_stats},
            }

    def bulk_upsert_car_listings(
        self,
        car_listings: List[CarListing],
        platform: str,
        quality_scores_list: Optional[List[Dict[str, float]]] = None,
    ) -> Dict[str, int]:
        """
        批量插入或更新车源

        Args:
            car_listings: 车源列表
            platform: 平台名称
            quality_scores_list: 质量评分列表

        Returns:
            操作统计
        """
        stats = {
            "total": len(car_listings),
            "inserted": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0,
        }

        for i, car_listing in enumerate(car_listings):
            try:
                quality_scores = (
                    quality_scores_list[i] if quality_scores_list else None
                )
                _, operation = self.upsert_car_listing(
                    car_listing, platform, quality_scores
                )
                stats[operation] += 1
            except Exception as e:
                logger.error(f"批量处理车源失败: {str(e)}")
                stats["errors"] += 1

        return stats


class CarSearchHistoryDAO(BaseDAO[CarSearchHistory]):
    """搜索历史 DAO"""

    def __init__(self):
        super().__init__(CarSearchHistory)

    def get_table_name(self) -> str:
        return "car_search_history"

    def log_search(
        self,
        session_id: str,
        user_query: str,
        parsed_query: Optional[Dict[str, Any]] = None,
        results_count: int = 0,
        search_duration: float = 0.0,
    ) -> CarSearchHistory:
        """记录搜索历史"""
        return self.create(
            session_id=session_id,
            user_query=user_query,
            parsed_query=parsed_query,
            search_results_count=results_count,
            search_duration=search_duration,
        )

    def get_search_history_by_session(
        self, session_id: str, limit: int = 10
    ) -> List[CarSearchHistory]:
        """获取会话的搜索历史"""
        with self.get_session() as session:
            return (
                session.query(CarSearchHistory)
                .filter(CarSearchHistory.session_id == session_id)
                .order_by(desc(CarSearchHistory.created_at))
                .limit(limit)
                .all()
            )


class CarRecommendationLogDAO(BaseDAO[CarRecommendationLog]):
    """推荐日志 DAO"""

    def __init__(self):
        super().__init__(CarRecommendationLog)

    def get_table_name(self) -> str:
        return "car_recommendation_logs"

    def log_recommendation(
        self,
        session_id: str,
        search_query: str,
        total_candidates: int,
        selected_count: int,
        selection_criteria: Optional[Dict[str, Any]] = None,
        execution_time: float = 0.0,
    ) -> CarRecommendationLog:
        """记录推荐日志"""
        return self.create(
            session_id=session_id,
            search_query=search_query,
            total_candidates=total_candidates,
            selected_count=selected_count,
            selection_criteria=selection_criteria,
            execution_time=execution_time,
        )
