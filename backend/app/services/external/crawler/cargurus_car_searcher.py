#!/usr/bin/env python3
"""
CarGurus 车源搜索器
专注于搜索具体的车源信息
"""

import asyncio
import random
from typing import List

from selenium.webdriver.common.by import By

from app.dao.config_dao import ConfigDAO
from app.models.schemas import CarListing, ParsedQuery
from app.services.data.config_service import ConfigServiceRefactored
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
from app.utils.web.captcha_utils import has_captcha, solve_captcha
from app.utils.web.dead_link_utils import is_dead_link
from app.utils.web.url_builder_utils import build_cargurus_search_url


class CargurusCarSearcher:
    """CarGurus 车源搜索器"""

    def __init__(self, profile_name: str):
        self.profile_name = profile_name
        self.config_service = ConfigServiceRefactored()
        self.config_dao = ConfigDAO()

    # ============================================================================
    # 公共接口方法
    # ============================================================================

    async def search_cars(
        self, parsed_query: ParsedQuery, max_results: int
    ) -> List[CarListing]:
        """搜索车源 - 增强版本"""
        try:
            logger.log_result(
                "搜索车源",
                f"开始搜索: {parsed_query.make} {parsed_query.model}",
            )

            # 获取品牌和车型的代码 - 直接使用MCP工具查询数据库
            make_code = await self._get_make_code_from_db(parsed_query.make)
            model_code = await self._get_model_code_from_db(
                parsed_query.make, parsed_query.model
            )

            logger.log_result(
                "配置代码",
                f"品牌: {parsed_query.make} -> {make_code}, 车型: {parsed_query.model} -> {model_code}",
            )

            # 使用 utils 构建搜索URL，支持更多过滤选项，使用代码而不是名称
            search_url = build_cargurus_search_url(
                make=parsed_query.make,
                model=parsed_query.model,
                zip_code=parsed_query.location or "M5V",
                distance=100,
                year_min=parsed_query.year_min,
                year_max=parsed_query.year_max,
                price_min=parsed_query.price_min,
                price_max=parsed_query.price_max,
                mileage_max=parsed_query.mileage_max,
                make_code=make_code,
                model_code=model_code,
            )
            logger.log_result("搜索URL", f"构建URL: {search_url}")

            # 使用browser_utils进行搜索，只尝试一次
            async with browser_utils.get_driver(self.profile_name) as driver:
                # 访问搜索页面
                driver.get(search_url)
                await asyncio.sleep(random.uniform(2, 4))

                # 使用 utils 进行页面检测
                if is_blocked_page(driver.page_source):
                    logger.log_result("页面检测", "页面被封禁")
                    return []

                # 使用 utils 处理验证码
                if has_captcha(driver):
                    logger.log_result("验证码检测", "发现验证码，尝试处理")
                    success = await solve_captcha(driver, max_attempts=1)
                    if not success:
                        logger.log_result("验证码处理", "验证码处理失败")
                        return []

                # 使用 utils 模拟人类行为
                simulate_human_behavior(driver)

                # 检查页面是否有效
                if not is_valid_vehicle_page(driver.page_source):
                    # 检查是否有验证码
                    if has_captcha(driver):
                        logger.log_result(
                            "验证码检测", "检测到验证码，尝试解决"
                        )
                        captcha_solved = await solve_captcha(
                            driver, max_attempts=3
                        )
                        if captcha_solved:
                            logger.log_result(
                                "验证码解决", "验证码解决成功，重新检测页面"
                            )
                            # 等待页面重新加载
                            await asyncio.sleep(5)
                            if not is_valid_vehicle_page(driver.page_source):
                                logger.log_result(
                                    "页面检测", "验证码解决后页面仍无效"
                                )
                                return []
                        else:
                            logger.log_result("验证码解决", "验证码解决失败")
                            return []
                    else:
                        logger.log_result("页面检测", "页面无效")
                        return []

                # 使用 selector_utils 获取车源列表选择器
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

                for listing in listings:
                    # 使用 utils 提取数据
                    data = extract_listing_data(listing)
                    if data.get("url"):
                        # 检查是否为死链
                        if is_dead_link(data.get("url")):
                            logger.log_result(
                                "死链检测",
                                f"跳过死链: {data.get('url')}",
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

                # 使用智能选择算法选择最优车源
                from app.utils.business.car_selection_utils import (
                    CarSelectionUtils,
                )

                selected_cars = CarSelectionUtils.select_best_cars(
                    cars, max_results
                )

                logger.log_result(
                    "搜索完成",
                    f"从 {len(cars)} 辆车中智能选择了 {len(selected_cars)} 辆最优车源",
                )
                return selected_cars

        except Exception as e:
            logger.log_result("搜索失败", f"搜索车源时出错: {e}")
            return []

    async def _get_make_code_from_db(self, make_name: str) -> str:
        """从数据库获取品牌代码"""
        try:
            if not make_name:
                return ""

            # 使用 ConfigDAO 获取品牌代码
            make_code = await self.config_dao.get_make_code(make_name)
            logger.log_result(
                "获取品牌代码", f"品牌: {make_name} -> 代码: {make_code}"
            )
            return make_code

        except Exception as e:
            logger.log_result(f"获取品牌代码失败: {str(e)}")
            return make_name.lower().replace(" ", "-") if make_name else ""

    async def _get_model_code_from_db(
        self, make_name: str, model_name: str
    ) -> str:
        """从数据库获取车型代码"""
        try:
            if not make_name or not model_name:
                return ""

            # 使用 ConfigDAO 获取车型代码
            model_code = await self.config_dao.get_model_code(
                make_name, model_name
            )
            logger.log_result(
                "获取车型代码",
                f"品牌: {make_name}, 车型: {model_name} -> 代码: {model_code}",
            )
            return model_code

        except Exception as e:
            logger.log_result(f"获取车型代码失败: {str(e)}")
            return (
                model_name.lower().replace(" ", "-").replace("/", "-")
                if model_name
                else ""
            )
