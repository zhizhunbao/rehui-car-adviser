#!/usr/bin/env python3
"""
CarGurus 车型数据收集器
专注于收集指定品牌的车型数据
"""

import asyncio
import random
from typing import Dict, List

from selenium.webdriver.common.by import By

from app.utils.business.selector_utils import CarGurusSelectors
from app.utils.core.logger import logger
from app.utils.validation.page_detection_utils import (
    is_blocked_page,
    is_no_results_page,
)
from app.utils.validation.validation_utils import is_valid_model
from app.utils.web.behavior_simulator_utils import simulate_human_behavior
from app.utils.web.browser_utils import browser_utils
from app.utils.web.button_click_utils import (
    ButtonClickStrategy,
    ButtonClickUtils,
)
from app.utils.web.captcha_utils import has_captcha, solve_captcha
from app.utils.web.url_builder_utils import (
    build_cargurus_brand_url,
)


class CargurusModelCollector:
    """CarGurus 车型数据收集器"""

    def __init__(
        self,
        profile_name: str,
        zip_code: str,
        distance: int,
        date_str: str = None,
    ):
        self.profile_name = profile_name
        self.zip_code = zip_code
        self.distance = distance
        self.date_str = date_str or "models"

    # ============================================================================
    # 公共接口方法
    # ============================================================================

    async def collect_models_for_brand(
        self, brand_name: str, limit: int
    ) -> List[Dict[str, str]]:
        """收集指定品牌的车型数据"""
        try:
            logger.log_result("开始收集车型数据", f"品牌: {brand_name}")

            models = []

            async with browser_utils.get_driver(self.profile_name) as driver:
                models = await self.collect_models_for_brand_with_driver(
                    driver, brand_name, limit
                )

            logger.log_result("车型收集完成", f"成功收集 {len(models)} 个车型")
            return models

        except Exception as e:
            logger.log_result("车型收集失败", f"收集车型数据时出错: {str(e)}")
            return []

    async def collect_models_for_brand_with_driver(
        self, driver, brand_name: str, limit: int
    ) -> List[Dict[str, str]]:
        """使用已存在的driver收集指定品牌的车型数据"""
        try:
            logger.log_result("开始收集车型数据", f"品牌: {brand_name}")

            # 使用 utils 构建URL
            brand_url = build_cargurus_brand_url(
                brand_name, self.zip_code, self.distance
            )

            logger.log_result("访问品牌页面", f"URL: {brand_url}")
            driver.get(brand_url)
            await asyncio.sleep(random.uniform(3, 5))

            # 使用 utils 进行页面检测
            if is_blocked_page(driver.page_source):
                logger.log_result("页面检测", "页面被封禁")
                return []

            # 检测是否是无结果页面
            if is_no_results_page(driver.page_source):
                logger.log_result(
                    "页面检测", f"品牌 {brand_name} 无可用车辆，跳过此品牌"
                )
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

            # 从页面提取车型数据
            models = await self._extract_models_from_page(
                driver, brand_name, limit
            )

            return models

        except Exception as e:
            logger.log_result("车型收集失败", f"收集车型数据时出错: {str(e)}")
            return []

    # ============================================================================
    # 页面交互方法
    # ============================================================================

    async def _extract_models_from_page(
        self, driver, brand_name: str, limit: int
    ) -> List[Dict[str, str]]:
        """从页面提取车型数据 - 通过点击下拉按钮"""
        models = []

        try:
            # 等待页面完全加载
            await asyncio.sleep(3)

            # 首先尝试点击 Make & Model 下拉按钮来展开车型选择器
            button_clicked = await self._click_make_model_button(driver)
            if button_clicked:
                await asyncio.sleep(2)  # 等待下拉菜单展开

            # 使用 selector_utils 获取车型选择器
            model_selectors = CarGurusSelectors.get_model_selectors()

            # 尝试主要方案
            for selector in model_selectors:
                try:
                    # 统一处理所有车型元素
                    model_elements = driver.find_elements(By.XPATH, selector)
                    if model_elements:
                        logger.log_result(
                            "车型选项",
                            f"使用选择器 {selector} 找到 {len(model_elements)} 个车型选项",
                        )
                        models = self._process_model_elements(
                            model_elements, brand_name, limit
                        )

                    if models:
                        break
                except Exception as e:
                    logger.log_result(
                        "选择器失败", f"选择器 {selector} 失败: {str(e)}"
                    )
                    continue

            # 如果主要方案失败，记录错误并返回空列表
            if not models:
                logger.log_result(
                    "车型收集失败", f"无法从页面提取 {brand_name} 的车型数据"
                )

        except Exception as e:
            logger.log_result("车型提取失败", f"提取车型数据时出错: {str(e)}")

        return models

    async def _click_make_model_button(self, driver):
        """点击 Make & model 按钮来展开车型选择器"""
        try:
            # 使用新的按钮点击工具
            button_utils = ButtonClickUtils(driver)
            result = button_utils.click_model_button(
                strategy=ButtonClickStrategy.SCROLL_AND_CLICK
            )

            if result.success:
                logger.log_result(
                    "按钮点击",
                    f"成功点击 Make & model 按钮，使用策略: {result.strategy_used}",
                )
                await asyncio.sleep(2)  # 等待展开动画

                # 点击 "Show all models" 按钮
                if await self._click_show_all_models_button(driver):
                    return True
                else:
                    # 即使Show all models按钮点击失败，也返回True，因为Make & model按钮已经点击成功
                    return True
            else:
                logger.log_result(
                    "按钮点击失败",
                    f"未能点击 Make & model 按钮: {result.error}",
                )
                return False

        except Exception as e:
            logger.log_result(
                "按钮点击失败", f"点击 Make & model 按钮时出错: {str(e)}"
            )
            return False

    async def _click_show_all_models_button(self, driver) -> bool:
        """点击 'Show all models' 按钮"""
        try:
            # 等待一下让页面完全加载
            await asyncio.sleep(1)

            # 使用新的按钮点击工具
            button_utils = ButtonClickUtils(driver)
            result = button_utils.click_show_all_models_button(
                strategy=ButtonClickStrategy.SCROLL_AND_CLICK
            )

            if result.success:
                logger.log_result(
                    "按钮点击",
                    f"成功点击 Show all models 按钮，使用策略: {result.strategy_used}",
                )
                await asyncio.sleep(2)  # 等待展开动画
                return True
            else:
                logger.log_result(
                    "按钮点击失败",
                    f"未能点击 Show all models 按钮: {result.error}",
                )
                return False

        except Exception as e:
            logger.log_result(
                "按钮点击失败", f"点击 Show all models 按钮时出错: {str(e)}"
            )
            return False

    # ============================================================================
    # 数据处理方法
    # ============================================================================

    def _process_model_elements(
        self, model_elements, brand_name: str, limit: int
    ) -> List[Dict[str, str]]:
        """统一处理车型元素（select选项或按钮），返回简化的CSV格式数据"""
        models = []

        for i, element in enumerate(model_elements):
            if limit and i >= limit:
                break

            try:
                # 统一提取车型数据
                model_name, model_value = self._extract_model_info(element)

                if not model_value or not model_name:
                    continue

                # 验证车型数据
                if is_valid_model(model_name, model_value):
                    # 简化的CSV格式数据，只包含 model_name 和 model_code
                    model_data = {
                        "model_name": model_name,
                        "model_code": model_value,
                    }
                    models.append(model_data)

                    logger.log_result(
                        "车型收集", f"收集车型: {brand_name} {model_name}"
                    )

            except Exception as e:
                logger.log_result("车型解析", f"解析车型数据失败: {str(e)}")
                continue

        return models

    def _extract_model_info(self, element) -> tuple[str, str]:
        """使用 utils 提取车型名称和value值"""
        from app.utils.data.data_extractor_utils import clean_text, safe_attr
        from app.utils.validation.validation_utils import is_valid_model

        # 获取元素类型
        tag_name = element.tag_name.lower()

        if tag_name == "option":
            # 处理select选项 - 使用 utils
            model_name = clean_text(element.text)
            model_value = safe_attr(element, "value")

            # 使用 utils 验证车型数据
            if is_valid_model(model_name, model_value):
                return model_name, model_value

        else:
            # 处理按钮和其他元素 - 使用 utils
            # 1. 从元素文本获取
            element_text = clean_text(element.text)
            if element_text and len(element_text) > 1:
                model_name = element_text
                model_value = safe_attr(element, "value")
                if is_valid_model(model_name, model_value):
                    return model_name, model_value

            # 2. 从 aria-label 获取
            aria_label = safe_attr(element, "aria-label")
            if aria_label:
                model_name = clean_text(aria_label.split("(")[0])
                model_value = safe_attr(element, "value")
                if is_valid_model(model_name, model_value):
                    return model_name, model_value

        return "", ""
