#!/usr/bin/env python3
"""
多平台车源聚合器 - 统一管理多个汽车交易平台的车源搜索
支持CarGurus、Kijiji、AutoTrader等平台的并行搜索和智能聚合
"""

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List

from app.models.schemas import CarListing, ParsedQuery
from app.services.external.crawler.cargurus_crawler_coordinator import (
    CargurusCrawlerCoordinator,
)
from app.utils.business.car_selection_utils import CarSelectionUtils
from app.utils.business.profile_utils import generate_daily_profile_name
from app.utils.core.logger import logger


class PlatformType(Enum):
    """支持的平台类型"""

    CARGURUS = "cargurus"
    KIJIJI = "kijiji"
    AUTOTRADER = "autotrader"
    CARS_COM = "cars_com"
    EDMUNDS = "edmunds"


@dataclass
class PlatformConfig:
    """平台配置"""

    name: str
    enabled: bool
    weight: float  # 平台权重 (0.0-1.0)
    max_results: int
    priority: int  # 优先级 (数字越小优先级越高)


class MultiPlatformCarAggregator:
    """多平台车源聚合器"""

    def __init__(self):
        self.platform_configs = self._initialize_platform_configs()
        self.platform_adapters = self._initialize_platform_adapters()

    def _initialize_platform_configs(
        self,
    ) -> Dict[PlatformType, PlatformConfig]:
        """初始化平台配置"""
        return {
            PlatformType.CARGURUS: PlatformConfig(
                name="CarGurus",
                enabled=True,
                weight=1.0,  # 最高权重
                max_results=15,
                priority=1,
            ),
            PlatformType.KIJIJI: PlatformConfig(
                name="Kijiji",
                enabled=True,
                weight=0.8,
                max_results=10,
                priority=2,
            ),
            PlatformType.AUTOTRADER: PlatformConfig(
                name="AutoTrader",
                enabled=False,  # 待实现
                weight=0.9,
                max_results=10,
                priority=3,
            ),
            PlatformType.CARS_COM: PlatformConfig(
                name="Cars.com",
                enabled=False,  # 待实现
                weight=0.7,
                max_results=8,
                priority=4,
            ),
            PlatformType.EDMUNDS: PlatformConfig(
                name="Edmunds",
                enabled=False,  # 待实现
                weight=0.6,
                max_results=5,
                priority=5,
            ),
        }

    def _initialize_platform_adapters(self) -> Dict[PlatformType, any]:
        """初始化平台适配器"""
        adapters = {}

        # CarGurus适配器 - 延迟初始化，避免在构造函数中需要参数
        if self.platform_configs[PlatformType.CARGURUS].enabled:
            adapters[PlatformType.CARGURUS] = None  # 延迟初始化

        # 其他平台适配器待实现
        # adapters[PlatformType.KIJIJI] = KijijiCrawlerCoordinator()
        # adapters[PlatformType.AUTOTRADER] = AutoTraderCrawlerCoordinator()

        return adapters

    def _get_cargurus_adapter(
        self, make_name: str = "Toyota", zip_code: str = "M5V"
    ) -> CargurusCrawlerCoordinator:
        """获取或创建 CarGurus 适配器实例"""
        if self.platform_adapters[PlatformType.CARGURUS] is None:
            # 生成带时间戳的profile名称
            profile_name = generate_daily_profile_name(
                "multi_platform_profile"
            )
            self.platform_adapters[PlatformType.CARGURUS] = (
                CargurusCrawlerCoordinator(
                    date_str="search",
                    make_name=make_name,
                    zip_code=zip_code,
                    profile_name=profile_name,
                )
            )
        return self.platform_adapters[PlatformType.CARGURUS]

    async def search_cars_multi_platform(
        self, parsed_query: ParsedQuery, max_total_results: int = 20
    ) -> List[CarListing]:
        """
        多平台并行搜索车源

        Args:
            parsed_query: 解析后的查询条件
            max_total_results: 最大总结果数

        Returns:
            聚合后的最优车源列表
        """
        logger.log_result(
            "多平台搜索开始",
            f"查询: {parsed_query.make} {parsed_query.model}, 目标结果数: {max_total_results}",
        )

        # 1. 并行搜索所有启用的平台
        platform_results = await self._search_all_platforms(parsed_query)

        # 2. 聚合所有平台结果
        all_cars = self._aggregate_platform_results(platform_results)

        # 3. 去重处理
        unique_cars = self._remove_duplicates(all_cars)

        # 4. 智能选择最优车源
        final_cars = CarSelectionUtils.select_best_cars(
            unique_cars, max_total_results
        )

        # 5. 添加平台信息
        final_cars = self._add_platform_info(final_cars, platform_results)

        logger.log_result(
            "多平台搜索完成",
            f"从 {len(unique_cars)} 辆去重车源中选择了 {len(final_cars)} 辆最优车源",
        )

        return final_cars

    async def _search_all_platforms(
        self, parsed_query: ParsedQuery
    ) -> Dict[PlatformType, List[CarListing]]:
        """并行搜索所有启用的平台"""
        tasks = []
        platform_types = []

        # 创建搜索任务
        for platform_type, config in self.platform_configs.items():
            if config.enabled and platform_type in self.platform_adapters:
                task = self._search_single_platform(
                    platform_type, parsed_query
                )
                tasks.append(task)
                platform_types.append(platform_type)

        # 并行执行所有搜索任务
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        platform_results = {}
        for i, result in enumerate(results):
            platform_type = platform_types[i]
            if isinstance(result, Exception):
                logger.log_result(
                    f"{platform_type.value}搜索失败",
                    f"平台 {platform_type.value} 搜索出错: {str(result)}",
                )
                platform_results[platform_type] = []
            else:
                platform_results[platform_type] = result
                logger.log_result(
                    f"{platform_type.value}搜索完成",
                    f"找到 {len(result)} 辆车源",
                )

        return platform_results

    async def _search_single_platform(
        self, platform_type: PlatformType, parsed_query: ParsedQuery
    ) -> List[CarListing]:
        """搜索单个平台"""
        config = self.platform_configs[platform_type]

        # 获取平台适配器，对于CarGurus使用延迟初始化
        if platform_type == PlatformType.CARGURUS:
            adapter = self._get_cargurus_adapter(
                make_name=parsed_query.make,
                zip_code=parsed_query.location or "M5V",
            )
        else:
            adapter = self.platform_adapters[platform_type]

        try:
            logger.log_result(
                f"{platform_type.value}搜索开始",
                f"平台: {config.name}, 最大结果数: {config.max_results}",
            )

            # 调用平台适配器搜索
            cars = await adapter.search_cars(parsed_query, config.max_results)

            # 为每个车源添加平台标识
            for car in cars:
                car.platform = platform_type.value
                car.platform_weight = config.weight

            return cars

        except Exception as e:
            logger.log_result(
                f"{platform_type.value}搜索异常",
                f"平台 {platform_type.value} 搜索异常: {str(e)}",
            )
            return []

    def _aggregate_platform_results(
        self, platform_results: Dict[PlatformType, List[CarListing]]
    ) -> List[CarListing]:
        """聚合所有平台结果"""
        all_cars = []

        for platform_type, cars in platform_results.items():
            config = self.platform_configs[platform_type]

            # 按平台权重调整车源评分
            for car in cars:
                # 应用平台权重到车源评分
                if hasattr(car, "platform_weight"):
                    car.platform_weight = config.weight

            all_cars.extend(cars)

        logger.log_result("平台结果聚合", f"总共聚合了 {len(all_cars)} 辆车源")
        return all_cars

    def _remove_duplicates(self, cars: List[CarListing]) -> List[CarListing]:
        """去除重复车源"""
        seen_urls = set()
        seen_titles = set()
        unique_cars = []

        for car in cars:
            # 基于URL去重
            if car.link and car.link in seen_urls:
                continue

            # 基于标题相似度去重
            if car.title:
                title_key = self._normalize_title(car.title)
                if title_key in seen_titles:
                    continue
                seen_titles.add(title_key)

            if car.link:
                seen_urls.add(car.link)

            unique_cars.append(car)

        removed_count = len(cars) - len(unique_cars)
        if removed_count > 0:
            logger.log_result("去重处理", f"移除了 {removed_count} 个重复车源")

        return unique_cars

    def _normalize_title(self, title: str) -> str:
        """标准化标题用于去重比较"""
        import re

        # 移除特殊字符，转换为小写
        normalized = re.sub(r"[^\w\s]", "", title.lower())

        # 移除多余空格
        normalized = " ".join(normalized.split())

        return normalized

    def _add_platform_info(
        self,
        cars: List[CarListing],
        platform_results: Dict[PlatformType, List[CarListing]],
    ) -> List[CarListing]:
        """为最终结果添加平台信息"""
        for car in cars:
            if not hasattr(car, "platform") or not car.platform:
                car.platform = "unknown"

            if not hasattr(car, "platform_weight") or not car.platform_weight:
                car.platform_weight = 0.5

        return cars

    def get_platform_statistics(self) -> Dict[str, any]:
        """获取平台统计信息"""
        stats = {
            "total_platforms": len(self.platform_configs),
            "enabled_platforms": sum(
                1
                for config in self.platform_configs.values()
                if config.enabled
            ),
            "platforms": {},
        }

        for platform_type, config in self.platform_configs.items():
            stats["platforms"][platform_type.value] = {
                "name": config.name,
                "enabled": config.enabled,
                "weight": config.weight,
                "max_results": config.max_results,
                "priority": config.priority,
            }

        return stats

    def update_platform_config(
        self, platform_type: PlatformType, **kwargs
    ) -> bool:
        """更新平台配置"""
        if platform_type not in self.platform_configs:
            return False

        config = self.platform_configs[platform_type]

        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)

        logger.log_result(
            "平台配置更新", f"更新了 {platform_type.value} 的配置: {kwargs}"
        )

        return True

    def enable_platform(self, platform_type: PlatformType) -> bool:
        """启用平台"""
        return self.update_platform_config(platform_type, enabled=True)

    def disable_platform(self, platform_type: PlatformType) -> bool:
        """禁用平台"""
        return self.update_platform_config(platform_type, enabled=False)
