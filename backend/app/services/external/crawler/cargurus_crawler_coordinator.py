#!/usr/bin/env python3
"""
CarGurus 主爬虫协调器
专注于协调和管理整个爬虫流程
"""

from typing import Dict, List

from app.dao.config_dao import ConfigDAO
from app.models.schemas import CarListing, ParsedQuery
from app.utils.core.logger import logger
from app.utils.core.path_util import get_cargurus_data_dir
from app.utils.data.data_saver_utils import save_models_data

from .cargurus_car_searcher import CargurusCarSearcher
from .cargurus_model_collector import CargurusModelCollector


class CargurusCrawlerCoordinator:
    """CarGurus 主爬虫协调器 - 重构版本"""

    def __init__(
        self, date_str: str, make_name: str, zip_code: str, profile_name: str
    ):
        """
        初始化爬虫协调器

        Args:
            date_str: 日期字符串
            make_name: 品牌名称
            zip_code: ZIP代码
            profile_name: 可选的profile名称
        """
        self.date_str = date_str
        self.make_name = make_name
        self.zip_code = zip_code
        self.profile_name = profile_name

        # 配置参数
        self.output_dir = get_cargurus_data_dir() / date_str
        self.distance = 100
        self.max_pages = 50
        self.per_page = 24

        # 初始化配置 DAO
        self.config_dao = ConfigDAO()

        # 存储品牌名称，在需要时异步获取代码
        self.make_name = make_name
        self.make_code = None

        # 初始化各个组件
        self.model_collector = CargurusModelCollector(
            self.profile_name, zip_code, self.distance, self.date_str
        )
        self.car_searcher = CargurusCarSearcher(self.profile_name)

        # 统计信息
        self.total_crawled = 0

        logger.log_result(
            "爬虫初始化", f"CarGurus爬虫已就绪，Profile: {self.profile_name}"
        )
        logger.log_result(
            "查询参数",
            f"品牌: {make_name}, ZIP: {zip_code}",
        )

    # ============================================================================
    # 公共接口方法
    # ============================================================================

    async def _ensure_make_code(self):
        """确保品牌代码已获取"""
        if self.make_code is None and self.make_name:
            self.make_code = await self.config_dao.get_make_code(self.make_name)
            logger.log_result(
                "获取品牌代码", f"品牌: {self.make_name} -> 代码: {self.make_code}"
            )

    def get_city_zip_codes(self, city_name: str) -> List[str]:
        """根据城市名称获取ZIP代码列表"""
        return self.config_dao.get_city_zip_codes(city_name)

    async def search_cars(
        self, parsed_query: ParsedQuery, max_results: int
    ) -> List[CarListing]:
        """
        搜索车源 - 与CarGurusScraper兼容的接口

        Args:
            parsed_query: 解析后的查询参数
            max_results: 最大结果数量

        Returns:
            车源列表
        """
        return await self.car_searcher.search_cars(parsed_query, max_results)

    async def collect_models_for_brand(
        self, brand_name: str, limit: int
    ) -> List[Dict[str, str]]:
        """收集指定品牌的车型数据"""
        return await self.model_collector.collect_models_for_brand(
            brand_name, limit
        )

    async def save_models_data(
        self,
        models: List[Dict[str, str]],
        brand_name: str,
        city: str = "toronto",
    ):
        """保存车型数据到文件"""
        # 使用 utils 保存数据
        await save_models_data(
            models,
            brand_name,
            self.output_dir,
            self.date_str,
            city,
            self.zip_code,
            self.distance,
        )
