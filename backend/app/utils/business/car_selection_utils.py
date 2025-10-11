#!/usr/bin/env python3
"""
车源选择工具 - 智能选择最优的20辆车源
实现多种排序和筛选策略，确保返回高质量、多样化的车源
"""

import re
from typing import Dict, List, Tuple

from app.models.schemas import CarListing
from app.utils.core.logger import logger


class CarSelectionUtils:
    """车源选择工具类"""

    @staticmethod
    def select_best_cars(
        cars: List[CarListing],
        max_results: int = 20,
        platform_weights: Dict[str, float] = None,
    ) -> List[CarListing]:
        """
        智能选择最优的车源

        Args:
            cars: 所有找到的车源列表
            max_results: 最大返回数量
            platform_weights: 平台权重字典，用于多平台车源评分

        Returns:
            经过智能筛选和排序的车源列表
        """
        if not cars:
            return []

        logger.log_result(
            "车源选择", f"开始从 {len(cars)} 辆车中选择最优的 {max_results} 辆"
        )

        # 1. 数据清洗和验证
        valid_cars = CarSelectionUtils._filter_valid_cars(cars)
        logger.log_result(
            "数据清洗", f"过滤后剩余 {len(valid_cars)} 辆有效车源"
        )

        if len(valid_cars) <= max_results:
            # 如果有效车源数量不足，直接返回并排序
            return CarSelectionUtils._sort_cars(valid_cars)

        # 2. 计算综合评分
        scored_cars = CarSelectionUtils._score_cars(
            valid_cars, platform_weights
        )

        # 3. 多样性保证 - 确保不同价格区间和年份分布
        selected_cars = CarSelectionUtils._ensure_diversity(
            scored_cars, max_results
        )

        # 4. 最终排序
        final_cars = CarSelectionUtils._sort_cars(selected_cars)

        logger.log_result(
            "车源选择完成", f"最终选择了 {len(final_cars)} 辆高质量车源"
        )
        return final_cars

    @staticmethod
    def _filter_valid_cars(cars: List[CarListing]) -> List[CarListing]:
        """过滤有效车源 - 排除异常数据"""
        valid_cars = []

        for car in cars:
            # 检查基本数据完整性
            if not car.title or not car.price or not car.year:
                continue

            # 解析价格
            price_value = CarSelectionUtils._parse_price(car.price)
            if price_value is None or price_value <= 0:
                continue

            # 解析里程
            mileage_value = CarSelectionUtils._parse_mileage(car.mileage)
            if mileage_value is None:
                continue

            # 价格合理性检查
            if not CarSelectionUtils._is_reasonable_price(
                car.year, price_value
            ):
                logger.log_result(
                    "价格异常", f"跳过异常价格车源: {car.title} - {car.price}"
                )
                continue

            # 里程合理性检查
            if not CarSelectionUtils._is_reasonable_mileage(
                car.year, mileage_value
            ):
                logger.log_result(
                    "里程异常",
                    f"跳过异常里程车源: {car.title} - {car.mileage}",
                )
                continue

            valid_cars.append(car)

        return valid_cars

    @staticmethod
    def _score_cars(
        cars: List[CarListing], platform_weights: Dict[str, float] = None
    ) -> List[Tuple[CarListing, float]]:
        """计算车源综合评分"""
        scored_cars = []

        for car in cars:
            score = 0.0

            # 价格评分 (40% 权重)
            price_score = CarSelectionUtils._calculate_price_score(car)
            score += price_score * 0.4

            # 年份评分 (25% 权重)
            year_score = CarSelectionUtils._calculate_year_score(car)
            score += year_score * 0.25

            # 里程评分 (25% 权重)
            mileage_score = CarSelectionUtils._calculate_mileage_score(car)
            score += mileage_score * 0.25

            # 数据完整性评分 (10% 权重)
            completeness_score = (
                CarSelectionUtils._calculate_completeness_score(car)
            )
            score += completeness_score * 0.1

            # 平台权重评分 (如果有平台信息)
            platform_score = CarSelectionUtils._calculate_platform_score(
                car, platform_weights
            )
            score += platform_score * 0.1  # 平台权重占10%

            scored_cars.append((car, score))

        return scored_cars

    @staticmethod
    def _ensure_diversity(
        scored_cars: List[Tuple[CarListing, float]], max_results: int
    ) -> List[CarListing]:
        """确保车源多样性 - 不同价格区间和年份分布"""
        # 按评分排序
        scored_cars.sort(key=lambda x: x[1], reverse=True)

        selected_cars = []
        price_ranges = {}  # 价格区间分布
        year_ranges = {}  # 年份区间分布

        for car, score in scored_cars:
            if len(selected_cars) >= max_results:
                break

            # 计算价格区间
            price_value = CarSelectionUtils._parse_price(car.price)
            price_range = CarSelectionUtils._get_price_range(price_value)

            # 计算年份区间
            year_range = CarSelectionUtils._get_year_range(car.year)

            # 检查多样性限制
            if (
                price_ranges.get(price_range, 0) < 3
                and year_ranges.get(year_range, 0) < 3
            ):

                selected_cars.append(car)
                price_ranges[price_range] = (
                    price_ranges.get(price_range, 0) + 1
                )
                year_ranges[year_range] = year_ranges.get(year_range, 0) + 1

        # 如果多样性限制导致选择不足，补充高分车源
        if len(selected_cars) < max_results:
            for car, score in scored_cars:
                if (
                    car not in selected_cars
                    and len(selected_cars) < max_results
                ):
                    selected_cars.append(car)

        return selected_cars

    @staticmethod
    def _sort_cars(
        cars: List[CarListing], platform_weights: Dict[str, float] = None
    ) -> List[CarListing]:
        """最终排序 - 按综合评分排序"""
        scored_cars = CarSelectionUtils._score_cars(cars, platform_weights)
        scored_cars.sort(key=lambda x: x[1], reverse=True)
        return [car for car, score in scored_cars]

    # ============================================================================
    # 评分计算方法
    # ============================================================================

    @staticmethod
    def _calculate_price_score(car: CarListing) -> float:
        """计算价格评分 (0-1)"""
        price_value = CarSelectionUtils._parse_price(car.price)
        if price_value is None:
            return 0.0

        # 基于年份和里程的合理价格范围
        base_price = CarSelectionUtils._get_base_price_for_year(car.year)
        mileage_factor = CarSelectionUtils._get_mileage_factor(car)
        expected_price = base_price * mileage_factor

        # 价格越接近预期价格，评分越高
        price_ratio = (
            price_value / expected_price if expected_price > 0 else 1.0
        )

        if 0.8 <= price_ratio <= 1.2:  # 合理价格区间
            return 1.0
        elif 0.6 <= price_ratio <= 1.4:  # 可接受价格区间
            return 0.8
        elif 0.4 <= price_ratio <= 1.6:  # 边缘价格区间
            return 0.6
        else:
            return 0.3

    @staticmethod
    def _calculate_year_score(car: CarListing) -> float:
        """计算年份评分 (0-1)"""
        current_year = 2024
        age = current_year - car.year

        if age <= 2:  # 2年内
            return 1.0
        elif age <= 5:  # 3-5年
            return 0.9
        elif age <= 8:  # 6-8年
            return 0.8
        elif age <= 12:  # 9-12年
            return 0.7
        else:  # 12年以上
            return 0.5

    @staticmethod
    def _calculate_mileage_score(car: CarListing) -> float:
        """计算里程评分 (0-1)"""
        mileage_value = CarSelectionUtils._parse_mileage(car.mileage)
        if mileage_value is None:
            return 0.0

        # 基于年份的合理里程
        age = 2024 - car.year
        expected_mileage = age * 15000  # 每年15000公里

        if expected_mileage == 0:
            return 0.5

        mileage_ratio = mileage_value / expected_mileage

        if mileage_ratio <= 0.8:  # 低里程
            return 1.0
        elif mileage_ratio <= 1.2:  # 正常里程
            return 0.9
        elif mileage_ratio <= 1.5:  # 稍高里程
            return 0.7
        else:  # 高里程
            return 0.4

    @staticmethod
    def _calculate_completeness_score(car: CarListing) -> float:
        """计算数据完整性评分 (0-1)"""
        score = 0.0

        if car.title and len(car.title.strip()) > 10:
            score += 0.3
        if car.price and car.price.strip():
            score += 0.3
        if car.year and car.year > 0:
            score += 0.2
        if car.mileage and car.mileage.strip():
            score += 0.1
        if car.location and car.location.strip():
            score += 0.1

        return score

    @staticmethod
    def _calculate_platform_score(
        car: CarListing, platform_weights: Dict[str, float] = None
    ) -> float:
        """计算平台权重评分 (0-1)"""
        if (
            not platform_weights
            or not hasattr(car, "platform")
            or not car.platform
        ):
            return 0.5  # 默认中等评分

        platform = car.platform.lower()
        weight = platform_weights.get(platform, 0.5)

        # 将权重转换为0-1评分
        return min(max(weight, 0.0), 1.0)

    # ============================================================================
    # 辅助方法
    # ============================================================================

    @staticmethod
    def _parse_price(price_str: str) -> float:
        """解析价格字符串"""
        if not price_str:
            return None

        # 移除货币符号和逗号
        price_clean = re.sub(r"[^\d.]", "", price_str)
        try:
            return float(price_clean)
        except ValueError:
            return None

    @staticmethod
    def _parse_mileage(mileage_str: str) -> float:
        """解析里程字符串"""
        if not mileage_str:
            return None

        # 移除单位和逗号
        mileage_clean = re.sub(r"[^\d.]", "", mileage_str)
        try:
            return float(mileage_clean)
        except ValueError:
            return None

    @staticmethod
    def _is_reasonable_price(year: int, price: float) -> bool:
        """检查价格是否合理"""
        if year < 2000 or year > 2024:
            return False

        # 基于年份的价格范围检查
        min_price = 1000  # 最低1000加元
        max_price = 100000  # 最高100000加元

        if year >= 2020:
            min_price = 15000
        elif year >= 2015:
            min_price = 8000
        elif year >= 2010:
            min_price = 3000

        return min_price <= price <= max_price

    @staticmethod
    def _is_reasonable_mileage(year: int, mileage: float) -> bool:
        """检查里程是否合理"""
        if year < 2000 or year > 2024:
            return False

        age = 2024 - year
        max_reasonable_mileage = age * 25000  # 每年最多25000公里
        min_reasonable_mileage = 0

        return min_reasonable_mileage <= mileage <= max_reasonable_mileage

    @staticmethod
    def _get_base_price_for_year(year: int) -> float:
        """获取某年份的基础价格"""
        if year >= 2022:
            return 35000
        elif year >= 2020:
            return 28000
        elif year >= 2018:
            return 22000
        elif year >= 2015:
            return 18000
        elif year >= 2012:
            return 12000
        else:
            return 8000

    @staticmethod
    def _get_mileage_factor(car: CarListing) -> float:
        """获取里程影响因子"""
        mileage_value = CarSelectionUtils._parse_mileage(car.mileage)
        if mileage_value is None:
            return 1.0

        age = 2024 - car.year
        if age == 0:
            return 1.0

        expected_mileage = age * 15000
        if expected_mileage == 0:
            return 1.0

        ratio = mileage_value / expected_mileage

        if ratio <= 0.5:
            return 1.2  # 低里程，价格可以高一些
        elif ratio <= 1.0:
            return 1.0  # 正常里程
        elif ratio <= 1.5:
            return 0.8  # 高里程，价格应该低一些
        else:
            return 0.6  # 很高里程

    @staticmethod
    def _get_price_range(price: float) -> str:
        """获取价格区间"""
        if price < 10000:
            return "under_10k"
        elif price < 20000:
            return "10k_20k"
        elif price < 30000:
            return "20k_30k"
        elif price < 50000:
            return "30k_50k"
        else:
            return "over_50k"

    @staticmethod
    def _get_year_range(year: int) -> str:
        """获取年份区间"""
        if year >= 2020:
            return "2020_plus"
        elif year >= 2015:
            return "2015_2019"
        elif year >= 2010:
            return "2010_2014"
        else:
            return "before_2010"
