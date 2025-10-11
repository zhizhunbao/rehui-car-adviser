#!/usr/bin/env python3
"""
基础爬虫协调器
定义爬虫协调器的通用接口和基础功能
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.models.schemas import CarListing, ParsedQuery


class BaseCrawlerCoordinator(ABC):
    """基础爬虫协调器抽象类"""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """返回爬虫源名称"""
        pass

    @abstractmethod
    async def search_cars(self, parsed_query: ParsedQuery) -> List[CarListing]:
        """
        搜索车源

        Args:
            parsed_query: 解析后的查询参数

        Returns:
            车源列表
        """
        pass

    @abstractmethod
    async def get_car_details(self, car_url: str) -> Optional[CarListing]:
        """
        获取车源详细信息

        Args:
            car_url: 车源URL

        Returns:
            车源详细信息，如果获取失败返回None
        """
        pass

    @abstractmethod
    async def update_car_listings(self, make_name: str) -> int:
        """
        更新车源列表

        Args:
            make_name: 汽车品牌名称

        Returns:
            更新的车源数量
        """
        pass
