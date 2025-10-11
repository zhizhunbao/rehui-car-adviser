#!/usr/bin/env python3
"""
CarGurus 车源搜索器 - 简化版本
专注于车源搜索功能，删除其他不必要功能
"""

import asyncio
import random
from typing import List

from selenium.webdriver.common.by import By

from app.models.schemas import CarListing, ParsedQuery
from app.utils.business.selector_utils import CarGurusSelectors
from app.utils.core.logger import logger
from app.utils.data.data_extractor_utils import (
    extract_listing_data,
    extract_year_from_title,
)
from app.utils.validation.page_detection_utils import (
    is_blocked_page,
    is_valid_vehicle_page,
)
from app.utils.web.behavior_simulator_utils import simulate_human_behavior
from app.utils.web.browser_utils import browser_utils
from app.utils.web.dead_link_utils import is_dead_link
from app.utils.web.url_builder_utils import build_cargurus_search_url


class CarGurusCarSearcher:
    """CarGurus 车源搜索器"""

    def __init__(self, profile_name: str):
        self.profile_name = profile_name

    async def search_cars(
        self, parsed_query: ParsedQuery, max_results: int
    ) -> List[CarListing]:
        """搜索车源"""
        try:
            logger.log_result(
                "搜索车源",
                f"开始搜索: {parsed_query.make} {parsed_query.model}",
            )

            # 构建搜索URL
            search_url = build_cargurus_search_url(
                parsed_query.make,
                parsed_query.model,
                parsed_query.location or "M5V",
                100,
            )
            logger.log_result("搜索URL", f"构建URL: {search_url}")

            # 使用browser_utils进行搜索
            async with browser_utils.get_driver(self.profile_name) as driver:
                # 访问搜索页面
                driver.get(search_url)
                await asyncio.sleep(random.uniform(2, 4))

                # 页面检测
                if is_blocked_page(driver.page_source):
                    logger.log_result("页面检测", "页面被封禁")
                    return []

                # 模拟人类行为
                simulate_human_behavior(driver)

                # 检查页面是否有效
                if not is_valid_vehicle_page(driver.page_source):
                    logger.log_result("页面检测", "页面无效")
                    return []

                # 获取车源列表选择器
                car_listing_selectors = (
                    CarGurusSelectors.get_car_listing_selectors()
                )
                listings = []
                for selector in car_listing_selectors:
                    try:
                        listings = driver.find_elements(By.XPATH, selector)
                        if listings:
                            logger.log_result(
                                "车源选择器",
                                f"使用选择器 {selector} 找到 {len(listings)} 个车源",
                            )
                            break
                    except Exception as e:
                        logger.log_result(
                            "车源选择器失败",
                            f"选择器 {selector} 失败: {str(e)}",
                        )
                        continue

                cars = []
                for listing in listings[:max_results]:
                    # 提取数据
                    data = extract_listing_data(listing)
                    if data.get("url"):
                        # 检查是否为死链
                        if is_dead_link(data.get("url")):
                            logger.log_result(
                                "死链检测", f"跳过死链: {data.get('url')}"
                            )
                            continue

                        car = CarListing(
                            id=f"cg_{hash(data.get('url', ''))}",
                            title=data.get("title", ""),
                            price=data.get("price", ""),
                            year=extract_year_from_title(
                                data.get("title", "")
                            ),
                            mileage=data.get("mileage", ""),
                            city=data.get("location", ""),
                            link=data.get("url", ""),
                        )
                        cars.append(car)

                logger.log_result("搜索完成", f"找到 {len(cars)} 辆车源")
                return cars

        except Exception as e:
            logger.log_result("搜索失败", f"搜索车源时出错: {e}")
            return []


# 使用示例
async def main():
    """主函数示例"""
    try:
        # 创建搜索器实例
        searcher = CarGurusCarSearcher("cargurus_profile")

        # 创建查询参数
        query = ParsedQuery(
            make="Honda",
            model="Civic",
            location="M5V",
            year_min=2020,
            year_max=2024,
            price_min=15000,
            price_max=30000,
            mileage_max=50000,
        )

        # 搜索车源
        cars = await searcher.search_cars(query)

        if cars:
            logger.log_result("搜索结果", f"成功找到 {len(cars)} 辆车源")
            for i, car in enumerate(cars[:3], 1):  # 显示前3个结果
                logger.log_result(
                    f"车源 {i}",
                    f"{car.year} {car.title} - {car.price} - {car.mileage} - {car.city}",
                )
        else:
            logger.log_result("搜索结果", "未找到符合条件的车源")

    except Exception as e:
        logger.log_result("任务失败", f"搜索任务执行失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
