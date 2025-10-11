#!/usr/bin/env python3
"""
CarGurus 主爬虫协调器
专注于协调和管理整个爬虫流程
"""

import asyncio
from datetime import datetime
from typing import List, Optional

from app.dao.config_dao import ConfigDAO
from app.models.schemas import (
    CarListing,
    ParsedQuery,
    ProgressEvent,
    ProgressEventType,
)
from app.utils.core.logger import logger

from .base_crawler_coordinator import BaseCrawlerCoordinator
from .cargurus_car_searcher import CargurusCarSearcher


class CargurusCrawlerCoordinator(BaseCrawlerCoordinator):
    """CarGurus 主爬虫协调器 - 重构版本"""

    def __init__(self, make_name: str, zip_code: str, profile_name: str = None):
        """初始化CarGurus爬虫协调器"""
        # 不调用super().__init__()，因为BaseCrawlerCoordinator没有__init__方法
        
        # 设置profile_name属性
        self.profile_name = profile_name
        
        # 配置参数
        self.distance = 100
        self.max_pages = 50
        self.per_page = 24

        # 初始化配置 DAO
        self.config_dao = ConfigDAO()

        # 存储品牌名称，在需要时异步获取代码
        self.make_name = make_name
        self.make_code = None

        # 初始化各个组件
        self.car_searcher = CargurusCarSearcher(self.profile_name)

        # 统计信息
        self.total_crawled = 0
        
        # 进度回调函数 - 用于实时进度更新
        self.progress_callback = None

        logger.log_result(
            "爬虫初始化", f"CarGurus爬虫已就绪，Profile: {self.profile_name}"
        )
        logger.log_result(
            "查询参数",
            f"品牌: {make_name}, ZIP: {zip_code}",
        )

    @property
    def source_name(self) -> str:
        """返回爬虫源名称"""
        return "cargurus"

    @property
    def display_name(self) -> str:
        """返回爬虫显示名称"""
        return "CarGurus"

    # ============================================================================
    # 公共接口方法
    # ============================================================================

    async def _ensure_make_code(self):
        """确保品牌代码已获取"""
        if self.make_code is None and self.make_name:
            self.make_code = await self.config_dao.get_make_code(
                self.make_name
            )
            logger.log_result(
                "获取品牌代码",
                f"品牌: {self.make_name} -> 代码: {self.make_code}",
            )

    def get_city_zip_codes(self, city_name: str) -> List[str]:
        """根据城市名称获取ZIP代码列表"""
        return self.config_dao.get_city_zip_codes(city_name)

    async def search_cars(self, parsed_query: ParsedQuery) -> List[CarListing]:
        """
        搜索车源

        Args:
            parsed_query: 解析后的查询参数

        Returns:
            车源列表
        """
        # 使用默认参数
        max_results = 50
        task_id = None
        
        if self.progress_callback and task_id:
            # 发送搜索开始事件
            await self._emit_progress_event(
                task_id=task_id,
                event_type=ProgressEventType.SOURCE_SEARCH_STARTED,
                message=f"开始搜索 CarGurus: {parsed_query.make} {parsed_query.model}",
                progress_percentage=0.0,
                data={"source": "cargurus", "display_name": "CarGurus"},
            )

        try:
            # 执行搜索
            cars = await self.car_searcher.search_cars(
                parsed_query, max_results
            )

            if self.progress_callback and task_id:
                # 发送搜索完成事件
                await self._emit_progress_event(
                    task_id=task_id,
                    event_type=ProgressEventType.SOURCE_SEARCH_COMPLETED,
                    message=f"CarGurus 搜索完成，找到 {len(cars)} 辆车",
                    progress_percentage=100.0,
                    data={
                        "source": "cargurus",
                        "cars_found": len(cars),
                        "cars_saved": len(cars),  # 假设都保存了
                    },
                )

            return cars

        except Exception as e:
            if self.progress_callback and task_id:
                # 发送搜索失败事件
                await self._emit_progress_event(
                    task_id=task_id,
                    event_type=ProgressEventType.SOURCE_SEARCH_FAILED,
                    message=f"CarGurus 搜索失败: {e}",
                    progress_percentage=0.0,
                    data={"source": "cargurus", "error": str(e)},
                )
            raise

    async def _emit_progress_event(
        self,
        task_id: str,
        event_type: ProgressEventType,
        message: str,
        progress_percentage: float,
        data: Optional[dict] = None,
    ):
        """发送进度事件"""
        if self.progress_callback:
            event = ProgressEvent(
                task_id=task_id,
                event_type=event_type,
                timestamp=datetime.now(),
                message=message,
                progress_percentage=progress_percentage,
                data=data,
            )

            if asyncio.iscoroutinefunction(self.progress_callback):
                await self.progress_callback(event)
            else:
                self.progress_callback(event)

    # 移除车型收集相关方法，因为车型数据已存储在数据库中

    async def get_car_details(self, car_url: str) -> Optional[CarListing]:
        """
        获取车源详细信息

        Args:
            car_url: 车源URL

        Returns:
            车源详细信息，如果获取失败返回None
        """
        # TODO: 实现车源详细信息获取
        logger.log_result("获取车源详情", f"URL: {car_url}")
        return None

    async def update_car_listings(self, make_name: str) -> int:
        """
        更新车源列表

        Args:
            make_name: 汽车品牌名称

        Returns:
            更新的车源数量
        """
        # TODO: 实现车源列表更新
        logger.log_result("更新车源列表", f"品牌: {make_name}")
        return 0
