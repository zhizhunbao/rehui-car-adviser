#!/usr/bin/env python3
"""
CarGurus 爬虫 - 重构版本
按职责拆分的模块化设计，每个类专注于单一职责
"""

import asyncio
import random
from typing import List, Dict

from selenium.webdriver.common.by import By

# 导入所有需要的 utils
from app.utils.cargurus_config_utils import get_city_zip_codes, get_make_code
from app.utils.url_builder_utils import (
    build_cargurus_search_url, build_cargurus_brand_url
)
from app.utils.data_extractor_utils import (
    extract_listing_data, extract_year_from_title
)
from app.utils.data_saver_utils import save_models_data
from app.utils.behavior_simulator_utils import simulate_human_behavior
from app.utils.captcha_utils import has_captcha, solve_captcha
from app.utils.page_detection_utils import (
    is_valid_vehicle_page, is_blocked_page, is_no_results_page
)
from app.utils.dead_link_utils import is_dead_link
from app.utils.browser_utils import browser_utils
from app.utils.logger import logger
from app.utils.path_util import get_cargurus_data_dir
from app.utils.selector_utils import CarGurusSelectors
from app.utils.button_click_utils import ButtonClickUtils, ButtonClickStrategy
from app.utils.validation_utils import is_valid_model
# 简化的跳过品牌管理
from app.models.schemas import CarListing, ParsedQuery


# =============================================================================
# 车型收集器
# =============================================================================

class CarGurusModelCollector:
    """CarGurus 车型数据收集器"""
    
    def __init__(self, profile_name: str, zip_code: str, distance: int, date_str: str = None):
        self.profile_name = profile_name
        self.zip_code = zip_code
        self.distance = distance
        self.date_str = date_str or "models"
    
    # =============================================================================
    # 公共接口方法
    # =============================================================================
    
    async def collect_models_for_brand(
        self, brand_name: str, limit: int
    ) -> List[Dict[str, str]]:
        """收集指定品牌的车型数据"""
        try:
            logger.log_result("开始收集车型数据", f"品牌: {brand_name}")
            
            models = []
            
            async with browser_utils.get_driver(
                self.profile_name
            ) as driver:
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
                logger.log_result("页面检测", f"品牌 {brand_name} 无可用车辆，跳过此品牌")
                return []
            
            # 使用 utils 处理验证码
            if has_captcha(driver):
                logger.log_result("验证码检测", "发现验证码，尝试处理")
                success = await solve_captcha(driver, max_attempts=3)
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
    
    # =============================================================================
    # 页面交互方法
    # =============================================================================
    
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
                            f"使用选择器 {selector} 找到 {len(model_elements)} 个车型选项"
                        )
                        models = self._process_model_elements(
                            model_elements, brand_name, limit
                        )
                    
                    if models:
                        break
                except Exception as e:
                    logger.log_result("选择器失败", f"选择器 {selector} 失败: {str(e)}")
                    continue
            
            # 如果主要方案失败，记录错误并返回空列表
            if not models:
                logger.log_result("车型收集失败", f"无法从页面提取 {brand_name} 的车型数据")
                
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
                    f"成功点击 Make & model 按钮，使用策略: {result.strategy_used}"
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
                    f"未能点击 Make & model 按钮: {result.error}"
                )
                return False
            
        except Exception as e:
            logger.log_result("按钮点击失败", f"点击 Make & model 按钮时出错: {str(e)}")
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
                    f"成功点击 Show all models 按钮，使用策略: {result.strategy_used}"
                )
                await asyncio.sleep(2)  # 等待展开动画
                return True
            else:
                logger.log_result(
                    "按钮点击失败", 
                    f"未能点击 Show all models 按钮: {result.error}"
                )
                return False
            
        except Exception as e:
            logger.log_result("按钮点击失败", f"点击 Show all models 按钮时出错: {str(e)}")
            return False
    
    # =============================================================================
    # 数据处理方法
    # =============================================================================
    
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
                        "model_code": model_value
                    }
                    models.append(model_data)
                    
                    logger.log_result(
                        "车型收集", 
                        f"收集车型: {brand_name} {model_name}"
                    )
                    
            except Exception as e:
                logger.log_result("车型解析", f"解析车型数据失败: {str(e)}")
                continue
        
        return models
    
    def _extract_model_info(self, element) -> tuple[str, str]:
        """使用 utils 提取车型名称和value值"""
        from app.utils.data_extractor_utils import safe_attr, clean_text
        from app.utils.validation_utils import is_valid_model
        
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
                model_name = clean_text(aria_label.split('(')[0])
                model_value = safe_attr(element, "value")
                if is_valid_model(model_name, model_value):
                    return model_name, model_value
        
        return "", ""


# =============================================================================
# 车源搜索器
# =============================================================================


class CarGurusCarSearcher:
    """CarGurus 车源搜索器"""
    
    def __init__(self, profile_name: str):
        self.profile_name = profile_name
    
    # =============================================================================
    # 公共接口方法
    # =============================================================================
    
    async def search_cars(
        self, parsed_query: ParsedQuery, max_results: int
    ) -> List[CarListing]:
        """搜索车源"""
        try:
            logger.log_result(
                "搜索车源", 
                f"开始搜索: {parsed_query.make} {parsed_query.model}"
            )
            
            # 使用 utils 构建搜索URL
            search_url = build_cargurus_search_url(
                parsed_query.make or "Toyota",
                parsed_query.model or "Camry",
                parsed_query.location or "M5V",
                100
            )
            logger.log_result("搜索URL", f"构建URL: {search_url}")
            
            # 使用browser_utils进行搜索
            async with browser_utils.get_driver(
                self.profile_name
            ) as driver:
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
                    success = await solve_captcha(driver, max_attempts=3)
                    if not success:
                        logger.log_result("验证码处理", "验证码处理失败")
                        return []
                
                # 使用 utils 模拟人类行为
                simulate_human_behavior(driver)
                
                # 检查页面是否有效
                if not is_valid_vehicle_page(driver.page_source):
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
                                f"使用选择器 {selector} 找到 {len(listings)} 个车源"
                            )
                            break
                    except Exception as e:
                        logger.log_result(
                            "车源选择器失败", 
                            f"选择器 {selector} 失败: {str(e)}"
                        )
                        continue
                cars = []
                
                for listing in listings[:max_results]:
                    # 使用 utils 提取数据
                    data = extract_listing_data(listing)
                    if data.get('url'):
                        # 检查是否为死链
                        if is_dead_link(data.get('url')):
                            logger.log_result(
                                "死链检测", f"跳过死链: {data.get('url')}"
                            )
                            continue
                        
                        car = CarListing(
                            id=f"cg_{hash(data.get('url', ''))}",
                            title=data.get('title', ''),
                            price=data.get('price', ''),
                            year=extract_year_from_title(
                                data.get('title', '')
                            ),
                            mileage=data.get('mileage', ''),
                            city=data.get('location', ''),
                            link=data.get('url', '')
                        )
                        cars.append(car)
                
                logger.log_result("搜索完成", f"找到 {len(cars)} 辆车源")
                return cars
                
        except Exception as e:
            logger.log_result("搜索失败", f"搜索车源时出错: {e}")
            return []


# =============================================================================
# 主爬虫协调器
# =============================================================================

class CarGurusCrawler:
    """CarGurus 主爬虫协调器 - 重构版本"""
    
    def __init__(
        self, date_str: str, make_name: str, zip_code: str, 
        profile_name: str
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
        
        # 使用 utils 获取品牌代码
        self.make_code = get_make_code(make_name)
        
        # 初始化各个组件
        self.model_collector = CarGurusModelCollector(
            self.profile_name, zip_code, self.distance, self.date_str
        )
        self.car_searcher = CarGurusCarSearcher(self.profile_name)
        
        # 统计信息
        self.total_crawled = 0
        
        logger.log_result(
            "爬虫初始化", f"CarGurus爬虫已就绪，Profile: {self.profile_name}"
        )
        logger.log_result(
            "查询参数", f"品牌: {make_name} ({self.make_code}), ZIP: {zip_code}"
        )
    
    # =============================================================================
    # 公共接口方法
    # =============================================================================
    
    def get_city_zip_codes(self, city_name: str) -> List[str]:
        """根据城市名称获取ZIP代码列表"""
        return get_city_zip_codes(city_name)
    
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
        self, models: List[Dict[str, str]], brand_name: str, 
        city: str = "toronto"
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
            self.distance
        )
    
    # 简化的跳过品牌管理 - 如果需要可以在这里添加简单的集合来跟踪跳过的品牌


# 使用示例
async def main():
    """主函数示例"""
    try:
        # 创建爬虫实例
        date_str = "models"  # 去掉时间戳，使用固定名称
        make_name = "Toyota"
        zip_code = "M5V"
        
        crawler = CarGurusCrawler(
            date_str, make_name, zip_code, "cargurus_profile"
        )
        
        # 展示配置
        logger.log_result(
            "配置展示", 
            "支持的品牌: Toyota, Honda, BMW, Mercedes, Ford等"
        )
        logger.log_result(
            "配置展示", 
            "支持的城市: Toronto, Vancouver, Montreal, Calgary等"
        )
        
        # 使用 utils 获取城市ZIP代码示例
        city_zips = crawler.get_city_zip_codes("Toronto")
        logger.log_result("城市ZIP", f"Toronto的ZIP代码: {city_zips}")
        
        # 收集车型数据示例
        models = await crawler.collect_models_for_brand(make_name, 5)
        if models:
            await crawler.save_models_data(models, make_name)
        
        logger.log_result("任务完成", "CarGurus爬虫任务执行完成")
        
    except Exception as e:
        logger.log_result("任务失败", f"爬虫任务执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
