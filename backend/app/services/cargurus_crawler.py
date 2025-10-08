#!/usr/bin/env python3
"""
CarGurus 爬虫 - 重构版本
按职责拆分的模块化设计，每个类专注于单一职责
"""

import asyncio
import json
import random
import time
import uuid
from typing import List, Dict
from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

from app.utils.browser_utils import browser_utils
from app.utils.logger import logger
from app.utils.path_util import get_cargurus_data_dir
from app.models.schemas import CarListing, ParsedQuery


# =============================================================================
# 配置管理类
# =============================================================================

class CarGurusConfig:
    """CarGurus 配置管理类"""
    
    # 主要城市及其ZIP代码
    MAJOR_CITIES = {
        'toronto': ['M5V', 'M6G', 'M4Y', 'M5A', 'M5H', 'M5B', 'M5C', 'M5E'],
        'vancouver': ['V6B', 'V6Z', 'V6E', 'V6H', 'V6J', 'V6K', 'V6L', 'V6M'],
        'montreal': ['H3A', 'H3B', 'H3G', 'H3H', 'H3J', 'H3K', 'H3L', 'H3M'],
        'calgary': ['T2P', 'T2R', 'T2S', 'T2T', 'T2V', 'T2W', 'T2X', 'T2Y'],
        'ottawa': ['K1P', 'K1R', 'K1S', 'K1T', 'K1V', 'K1W', 'K1X', 'K1Y'],
        'edmonton': ['T5J', 'T5K', 'T5L', 'T5M', 'T5N', 'T5P', 'T5R', 'T5S'],
        'winnipeg': ['R3B', 'R3C', 'R3E', 'R3G', 'R3H', 'R3J', 'R3K', 'R3L'],
        'halifax': ['B3H', 'B3J', 'B3K', 'B3L', 'B3M', 'B3N', 'B3P', 'B3R']
    }
    
    # 品牌代码映射
    MAKE_CODES = {
        # 日系品牌
        'toyota': 'm7', 'honda': 'm6', 'nissan': 'm12', 'mazda': 'm42', 
        'subaru': 'm53', 'mitsubishi': 'm46', 'infiniti': 'm84', 'acura': 'm4', 
        'lexus': 'm37',
        
        # 德系品牌
        'bmw': 'm3', 'mercedes-benz': 'm43', 'mercedes': 'm43', 'audi': 'm19', 
        'volkswagen': 'm55', 'porsche': 'm48', 'volvo': 'm56',
        
        # 美系品牌
        'ford': 'm2', 'chevrolet': 'm1', 'jeep': 'm32', 'cadillac': 'm22', 
        'buick': 'm21', 'gmc': 'm25', 'lincoln': 'm36', 'dodge': 'm26', 
        'chrysler': 'm23', 'ram': 'm49',
        
        # 韩系品牌
        'hyundai': 'm28', 'kia': 'm33', 'genesis': 'm203',
        
        # 其他品牌
        'tesla': 'm112', 'jaguar': 'm31', 'land rover': 'm35', 'mini': 'm45',
        'alfa romeo': 'm5', 'fiat': 'm27', 'maserati': 'm41', 'bentley': 'm20',
        'ferrari': 'm29', 'lamborghini': 'm34', 'mclaren': 'm40', 'rolls-royce': 'm50',
        'aston martin': 'm18', 'lotus': 'm38', 'morgan': 'm47', 'noble': 'm51'
    }
    
    @classmethod
    def get_city_zip_codes(cls, city_name: str) -> List[str]:
        """根据城市名称获取ZIP代码列表"""
        city_lower = city_name.lower().strip()
        
        # 直接匹配
        if city_lower in cls.MAJOR_CITIES:
            return cls.MAJOR_CITIES[city_lower]
        
        # 部分匹配
        for city_key, zip_codes in cls.MAJOR_CITIES.items():
            if city_lower in city_key or city_key in city_lower:
                logger.log_result("城市匹配", f"部分匹配: {city_name} -> {city_key}")
                return zip_codes
        
        # 默认返回多伦多ZIP代码
        logger.log_result("城市查找", f"未找到城市 {city_name} 的ZIP代码，使用默认值")
        return ['M5V']
    
    @classmethod
    def get_make_code(cls, make_name: str) -> str:
        """根据品牌名称获取品牌代码"""
        make_lower = make_name.lower().strip()
        
        # 精确匹配
        if make_lower in cls.MAKE_CODES:
            return cls.MAKE_CODES[make_lower]
        
        # 部分匹配
        for key, code in cls.MAKE_CODES.items():
            if make_lower in key or key in make_lower:
                logger.log_result("品牌匹配", f"部分匹配: {make_name} -> {key} ({code})")
                return code
                    
        # 默认返回小写品牌名
        logger.log_result("品牌查找", f"未找到品牌 {make_name} 的代码，使用默认值: {make_lower}")
        return make_lower


# =============================================================================
# URL构建类
# =============================================================================

class CarGurusURLBuilder:
    """CarGurus URL构建器"""
    
    BASE_URL = "https://www.cargurus.ca/Cars/inventorylisting/viewDetailsFilterViewInventoryListing.action"
    
    @classmethod
    def build_search_url(cls, parsed_query: ParsedQuery, distance: int = 100) -> str:
        """构建车源搜索URL"""
        location = parsed_query.location or "M5V"
        make_code = CarGurusConfig.get_make_code(parsed_query.make or "Toyota")
        search_id = str(uuid.uuid4())
        
        url = (f"{cls.BASE_URL}?searchId={search_id}&zip={location}&distance={distance}"
               f"&sourceContext=carGurusHomePageModel&sortDir=ASC&sortType=DEAL_SCORE"
               f"&makeModelTrimPaths={make_code}&srpVariation=DEFAULT_SEARCH"
               f"&isDeliveryEnabled=true&nonShippableBaseline=1852")
        
        return url
    
    @classmethod
    def build_brand_url(cls, brand_code: str, zip_code: str, distance: int = 100) -> str:
        """构建品牌页面URL"""
        return f"{cls.BASE_URL}?makeModelTrimPaths={brand_code}&zip={zip_code}&distance={distance}"
    
    @classmethod
    def build_model_url(cls, model_code: str, zip_code: str, distance: int = 100) -> str:
        """构建车型页面URL"""
        return f"{cls.BASE_URL}?makeModelTrimPaths={model_code}&zip={zip_code}&distance={distance}"


# =============================================================================
# 数据提取类
# =============================================================================

class CarGurusDataExtractor:
    """CarGurus 数据提取器"""
    
    @staticmethod
    def extract_listing_data(listing) -> Dict[str, str]:
        """提取单个listing的数据"""
        def safe_text(element, xpath: str) -> str:
            try:
                elem = element.find_element(By.XPATH, xpath)
                return elem.text.strip()
            except Exception:
                return ""
        
        def safe_attr(element, attr: str) -> str:
            try:
                return element.get_attribute(attr) or ""
            except Exception:
                return ""
        
        return {
            'title': safe_text(listing, './/h4'),
            'price': safe_text(listing, './/h4[contains(@class,"_priceText")]').replace('$', '').replace(',', ''),
            'mileage': safe_text(listing, './/p[contains(@data-testid,"mileage")]').replace(' km', '').replace(',', ''),
            'location': safe_text(listing, './/p[@data-testid="srp-tile-bucket-text"]'),
            'deal_rating': safe_text(listing, './/span[contains(text(),"Deal")]'),
            'url': safe_attr(listing, 'href'),
            'data_timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    @staticmethod
    def extract_year_from_title(title: str) -> int:
        """从标题中提取年份"""
        import re
        year_match = re.search(r'(\d{4})', title)
        return int(year_match.group(1)) if year_match else 2020


# =============================================================================
# 数据保存类
# =============================================================================

class CarGurusDataSaver:
    """CarGurus 数据保存器"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def save_models_data(self, models: List[Dict[str, str]], brand_name: str, date_str: str, 
                              city: str = "toronto", zip_code: str = "M5V", distance: int = 100):
        """保存车型数据到文件 - 简化格式"""
        try:
            if not models:
                logger.log_result("保存车型数据", "没有车型数据需要保存")
                return
            
            # 创建输出文件路径 - 去掉时间戳，直接覆盖
            output_file = self.output_dir / f"models_{brand_name.lower()}.json"
            
            # 构建简化的数据结构
            make_code = CarGurusConfig.get_make_code(brand_name)
            simplified_models = []
            
            for model in models:
                model_data = {
                    "make": brand_name.title(),
                    "make_code": make_code,
                    "model": model.get("name", ""),
                    "model_code": model.get("value", "")
                }
                simplified_models.append(model_data)
            
            # 构建最终数据结构
            data = {
                brand_name.lower(): simplified_models
            }
            
            # 保存为JSON格式
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.log_result("车型数据保存", f"已保存到: {output_file}")
            
        except Exception as e:
            logger.log_result("保存车型数据失败", f"保存时出错: {str(e)}")
            raise


# =============================================================================
# 车型收集器
# =============================================================================

class CarGurusModelCollector:
    """CarGurus 车型数据收集器"""
    
    def __init__(self, profile_name: str, zip_code: str, distance: int = 100):
        self.profile_name = profile_name
        self.zip_code = zip_code
        self.distance = distance
    
    async def collect_models_for_brand(self, brand_name: str, limit: int = None) -> List[Dict[str, str]]:
        """收集指定品牌的车型数据"""
        try:
            logger.log_result("开始收集车型数据", f"品牌: {brand_name}")
            
            models = []
            
            async with browser_utils.get_driver(self.profile_name) as driver:
                models = await self.collect_models_for_brand_with_driver(driver, brand_name, limit)
            
            logger.log_result("车型收集完成", f"成功收集 {len(models)} 个车型")
            return models
            
        except Exception as e:
            logger.log_result("车型收集失败", f"收集车型数据时出错: {str(e)}")
            return []
    
    async def collect_models_for_brand_with_driver(self, driver, brand_name: str, limit: int = None) -> List[Dict[str, str]]:
        """使用已存在的driver收集指定品牌的车型数据"""
        try:
            logger.log_result("开始收集车型数据", f"品牌: {brand_name}")
            
            # 直接访问品牌页面URL
            brand_code = CarGurusConfig.get_make_code(brand_name)
            brand_url = CarGurusURLBuilder.build_brand_url(brand_code, self.zip_code, self.distance)
            
            logger.log_result("访问品牌页面", f"URL: {brand_url}")
            driver.get(brand_url)
            await asyncio.sleep(random.uniform(3, 5))
            
            # 跳过验证码处理
            
            # 模拟人类行为
            self._simulate_human_behavior(driver)
            
            # 直接从页面提取车型数据
            models = await self._extract_models_from_page(driver, brand_name, limit)
            
            return models
            
        except Exception as e:
            logger.log_result("车型收集失败", f"收集车型数据时出错: {str(e)}")
            return []
    
    async def _extract_models_from_page(self, driver, brand_name: str, limit: int = None) -> List[Dict[str, str]]:
        """从页面提取车型数据 - 通过点击下拉按钮"""
        models = []
        
        try:
            # 等待页面完全加载
            await asyncio.sleep(3)
            
            # 首先尝试点击 Make & Model 下拉按钮来展开车型选择器
            button_clicked = await self._click_make_model_button(driver)
            if button_clicked:
                await asyncio.sleep(2)  # 等待下拉菜单展开
            
            # 车型选择器策略 - 针对展开后的车型选择器
            model_selectors = [
                # 主要的车型选择器 - 展开后的选项
                "//select[@name='makeModelTrimPaths']//option[contains(@value, '/')]",
                "//select[contains(@name, 'model')]//option[contains(@value, '/')]",
                "//select[contains(@id, 'model')]//option[contains(@value, '/')]",
                
                # 展开后的按钮形式的车型选择器
                "//div[@id='MakeAndModel-accordion-content']//button[contains(@value, '/')]",
                "//div[contains(@class, '_accordionContent_')]//button[contains(@value, '/')]",
                "//div[contains(@data-testid, 'checkbox-container')]//button[contains(@value, '/')]",
                "//li[contains(@class, '_option_')]//button[contains(@value, '/')]",
                
                # 链接形式的车型选择器
                "//a[contains(@href, 'makeModelTrimPaths') and contains(@href, '/')]",
                "//a[contains(@href, 'model=')]",
                
                # 其他可能的车型选择器
                "//button[contains(@value, '/')]",
                "//button[contains(@data-testid, 'FILTER.MAKE_MODEL')]"
            ]
            
            # 尝试主要方案
            for selector in model_selectors:
                try:
                    if "option" in selector:
                        # 处理select选项
                        model_elements = driver.find_elements(By.XPATH, selector)
                        if model_elements:
                            logger.log_result("车型选项", f"使用选择器 {selector} 找到 {len(model_elements)} 个车型选项")
                            models = self._process_model_options(model_elements, brand_name, limit)
                    else:
                        # 处理按钮和链接
                        model_elements = driver.find_elements(By.XPATH, selector)
                        if model_elements:
                            logger.log_result("车型选项", f"使用选择器 {selector} 找到 {len(model_elements)} 个车型选项")
                            models = self._process_model_buttons(model_elements, brand_name, limit)
                    
                    if models:
                        break
                except Exception as e:
                    logger.log_result("选择器失败", f"选择器 {selector} 失败: {str(e)}")
                    continue
            
            # 如果主要方案失败，尝试备用方案
            if not models:
                models = self._get_hardcoded_models(brand_name, limit)
                
        except Exception as e:
            logger.log_result("车型提取失败", f"提取车型数据时出错: {str(e)}")
        
        return models
    
    def _process_model_options(self, model_options, brand_name: str, limit: int = None) -> List[Dict[str, str]]:
        """处理车型选项（select元素）"""
        models = []
        
        for i, option in enumerate(model_options):
            if limit and i >= limit:
                break
            
            try:
                # 提取车型数据
                model_value = option.get_attribute("value")
                model_name = option.text.strip()
                
                if model_name and model_value and model_name not in ["Any Model", "Select Model", "All Models", "Reset"]:
                    # 构建车型URL
                    model_url = CarGurusURLBuilder.build_model_url(model_value, self.zip_code, self.distance)
                    
                    model_data = {
                        "name": model_name,
                        "value": model_value,
                        "url": model_url,
                        "count": 0,  # select选项通常没有数量信息
                        "brand": brand_name
                    }
                    models.append(model_data)
                    
                    logger.log_result("车型收集", f"收集车型: {brand_name} {model_name}")
                    
            except Exception as e:
                logger.log_result("车型解析", f"解析车型数据失败: {str(e)}")
                continue
        
        return models
    
    async def _click_make_model_button(self, driver):
        """点击 Make & model 按钮来展开车型选择器"""
        try:
            # 尝试多种选择器来找到 Make & model 按钮
            button_selectors = [
                "//button[@id='MakeAndModel-accordion-trigger']",
                "//button[contains(@aria-controls, 'MakeAndModel')]",
                "//button[contains(text(), 'Make & model')]",
                "//button[contains(text(), 'Make')]",
                "//legend[contains(text(), 'Make & model')]/..",
                "//button[contains(@class, '_accordionTrigger_')]"
            ]
            
            for selector in button_selectors:
                try:
                    button = driver.find_element(By.XPATH, selector)
                    if button.is_displayed() and button.is_enabled():
                        # 滚动到按钮位置
                        driver.execute_script("arguments[0].scrollIntoView(true);", button)
                        await asyncio.sleep(1)
                        
                        # 点击按钮
                        button.click()
                        logger.log_result("按钮点击", f"成功点击 Make & model 按钮: {selector}")
                        await asyncio.sleep(2)  # 等待展开动画
                        
                        # 点击 "Show all models" 按钮
                        if await self._click_show_all_models_button(driver):
                            return True
                        else:
                            # 即使Show all models按钮点击失败，也返回True，因为Make & model按钮已经点击成功
                            return True
                except Exception:
                    continue
            
            logger.log_result("按钮点击失败", "未能找到或点击 Make & model 按钮")
            return False
            
        except Exception as e:
            logger.log_result("按钮点击失败", f"点击 Make & model 按钮时出错: {str(e)}")
            return False
    
    async def _click_show_all_models_button(self, driver) -> bool:
        """点击 'Show all models' 按钮"""
        try:
            # 等待一下让页面完全加载
            await asyncio.sleep(1)
            
            # 多种选择器策略来找到 "Show all models" 按钮
            selectors = [
                "//button[contains(@class, '_toggleShowAllButton_')]",
                "//button[contains(@class, 'lOGaE') and contains(@class, 'vDDxh')]",
                "//button[contains(text(), 'Show all models')]",
                "//button[contains(@class, '_toggleShowAllButton_') and contains(@class, '_inset_')]",
                "//button[contains(@class, 'lOGaE') and contains(@class, 'vDDxh') and contains(@class, '_toggleShowAllButton_')]"
            ]
            
            for selector in selectors:
                try:
                    buttons = driver.find_elements(By.XPATH, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            # 滚动到按钮位置
                            driver.execute_script("arguments[0].scrollIntoView(true);", button)
                            await asyncio.sleep(0.5)
                            
                            # 点击按钮
                            button.click()
                            logger.log_result("按钮点击", f"成功点击 Show all models 按钮: {selector}")
                            await asyncio.sleep(2)  # 等待展开动画
                            return True
                except Exception:
                    continue
            
            logger.log_result("按钮点击失败", "未能找到或点击 Show all models 按钮")
            return False
            
        except Exception as e:
            logger.log_result("按钮点击失败", f"点击 Show all models 按钮时出错: {str(e)}")
            return False
    
    def _process_model_buttons(self, model_buttons, brand_name: str, limit: int = None) -> List[Dict[str, str]]:
        """处理车型按钮"""
        models = []
        
        for i, button in enumerate(model_buttons):
            if limit and i >= limit:
                break
            
            try:
                # 提取车型数据
                model_value = button.get_attribute("value")
                model_name = ""
                model_count = 0
                
                # 从aria-label或label中提取车型名称和数量
                aria_label = button.get_attribute("aria-label")
                if aria_label:
                    # 解析 "ADX (5)" 格式
                    import re
                    match = re.match(r'([^(]+)\s*\((\d+)\)', aria_label)
                    if match:
                        model_name = match.group(1).strip()
                        model_count = int(match.group(2))
                
                # 如果aria-label解析失败，尝试从label元素获取
                if not model_name:
                    try:
                        # 尝试多种方式获取车型名称
                        label_selectors = [
                            "./following-sibling::label",
                            "./parent::*/label",
                            "./../label",
                            ".//label"
                        ]
                        
                        for label_selector in label_selectors:
                            try:
                                label = button.find_element(By.XPATH, label_selector)
                                span = label.find_element(By.XPATH, ".//span")
                                em = label.find_element(By.XPATH, ".//em")
                                
                                model_name = span.text.strip()
                                count_text = em.text.strip()
                                count_match = re.search(r'\((\d+)\)', count_text)
                                if count_match:
                                    model_count = int(count_match.group(1))
                                break
                            except Exception:
                                continue
                        
                        # 如果还是没找到，尝试直接从按钮文本获取
                        if not model_name:
                            button_text = button.text.strip()
                            if button_text and len(button_text) > 1:
                                model_name = button_text
                                
                    except Exception:
                        pass
                
                # 如果仍然没有车型名称，尝试从按钮的其他属性获取
                if not model_name:
                    try:
                        # 尝试从data属性获取
                        data_name = button.get_attribute("data-name")
                        if data_name:
                            model_name = data_name
                        
                        # 尝试从title属性获取
                        if not model_name:
                            title = button.get_attribute("title")
                            if title:
                                model_name = title
                    except Exception:
                        pass
                
                if model_name and model_value and model_name not in ["Any Model", "Select Model", "All Models", "Reset"]:
                    # 构建车型URL
                    model_url = CarGurusURLBuilder.build_model_url(model_value, self.zip_code, self.distance)
                    
                    model_data = {
                        "name": model_name,
                        "value": model_value,
                        "url": model_url,
                        "count": model_count,
                        "brand": brand_name
                    }
                    models.append(model_data)
                    
                    logger.log_result("车型收集", f"收集车型: {brand_name} {model_name} ({model_count})")
                    
            except Exception as e:
                logger.log_result("车型解析", f"解析车型数据失败: {str(e)}")
                continue
        
        return models
    
    def _get_hardcoded_models(self, brand_name: str, limit: int = None) -> List[Dict[str, str]]:
        """获取硬编码的常见车型列表"""
        logger.log_result("车型收集失败", "无法找到车型选择器，使用硬编码车型列表")
        
        common_models = {
            'acura': [
                {"name": "ILX", "value": "m4/d2137", "count": 45},
                {"name": "Integra", "value": "m4/d36", "count": 22},
                {"name": "MDX", "value": "m4/d16", "count": 169},
                {"name": "RDX", "value": "m4/d921", "count": 172},
                {"name": "TLX", "value": "m4/d2278", "count": 113}
            ],
            'toyota': [
                {"name": "Camry", "value": "m7/t1", "count": 200},
                {"name": "Corolla", "value": "m7/t2", "count": 150},
                {"name": "RAV4", "value": "m7/t3", "count": 180},
                {"name": "Highlander", "value": "m7/t4", "count": 120}
            ]
        }
        
        models = []
        brand_lower = brand_name.lower()
        if brand_lower in common_models:
            logger.log_result("备用方案", f"使用硬编码 {brand_name} 车型列表")
            for i, model in enumerate(common_models[brand_lower]):
                if limit and i >= limit:
                    break
                
                model["url"] = CarGurusURLBuilder.build_model_url(model['value'], self.zip_code, self.distance)
                model["brand"] = brand_name
                models.append(model)
                logger.log_result("车型收集", f"硬编码车型: {brand_name} {model['name']}")
        
        return models

    def _simulate_human_behavior(self, driver):
        """模拟人类浏览行为"""
        try:
            # 随机滚动
            scroll_amount = random.randint(100, 500)
            driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(random.uniform(0.5, 1.5))
            
            # 安全的鼠标移动
            try:
                # 获取body元素作为移动基准
                body = driver.find_element(By.TAG_NAME, "body")
                body_rect = body.rect
                
                # 计算安全的移动范围（在body元素内部）
                safe_width = max(100, body_rect['width'] - 100)  # 留出边距
                safe_height = max(100, body_rect['height'] - 100)
                
                # 计算安全的偏移量
                max_x_offset = min(30, safe_width // 4)
                max_y_offset = min(30, safe_height // 4)
                
                x_offset = random.randint(-max_x_offset, max_x_offset)
                y_offset = random.randint(-max_y_offset, max_y_offset)
                
                # 计算目标位置（相对于body元素的左上角）
                target_x = body_rect['width'] // 2 + x_offset
                target_y = body_rect['height'] // 2 + y_offset
                
                # 确保目标位置在body元素范围内
                target_x = max(10, min(target_x, body_rect['width'] - 10))
                target_y = max(10, min(target_y, body_rect['height'] - 10))
                
                # 使用move_to_element_with_offset
                actions = ActionChains(driver)
                actions.move_to_element_with_offset(
                    body, target_x, target_y
                ).perform()
                time.sleep(random.uniform(0.3, 0.8))
            except Exception as mouse_e:
                logger.log_result("行为模拟", f"鼠标移动失败，跳过: {str(mouse_e)}")
            
        except Exception as e:
            logger.log_result("行为模拟", f"模拟行为失败: {str(e)}")


# =============================================================================
# 车源搜索器
# =============================================================================

class CarGurusCarSearcher:
    """CarGurus 车源搜索器"""
    
    def __init__(self, profile_name: str):
        self.profile_name = profile_name
    
    async def search_cars(self, parsed_query: ParsedQuery, max_results: int = 20) -> List[CarListing]:
        """搜索车源"""
        try:
            logger.log_result("搜索车源", f"开始搜索: {parsed_query.make} {parsed_query.model}")
            
            # 构建搜索URL
            search_url = CarGurusURLBuilder.build_search_url(parsed_query)
            logger.log_result("搜索URL", f"构建URL: {search_url}")
            
            # 使用browser_utils进行搜索
            async with browser_utils.get_driver(self.profile_name) as driver:
                # 访问搜索页面
                driver.get(search_url)
                await asyncio.sleep(random.uniform(2, 4))
                
                # 处理验证码
                await self._handle_captcha(driver)
                
                # 模拟人类行为
                self._simulate_human_behavior(driver)
                
                # 提取车源数据
                listings = driver.find_elements(By.XPATH, '//a[@data-testid="car-blade-link"]')
                cars = []
                
                for listing in listings[:max_results]:
                    data = CarGurusDataExtractor.extract_listing_data(listing)
                    if data.get('url'):
                        car = CarListing(
                            id=f"cg_{hash(data.get('url', ''))}",
                            title=data.get('title', ''),
                            price=data.get('price', ''),
                            year=CarGurusDataExtractor.extract_year_from_title(data.get('title', '')),
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
    
    async def _handle_captcha(self, driver) -> bool:
        """处理滑块验证码"""
        if browser_utils.has_slider_captcha(driver):
            logger.log_result("验证码检测", "发现滑块验证码，尝试自动处理")
            success = await browser_utils.solve_slider_captcha(driver)
            if success:
                logger.log_result("验证码处理", "滑块验证码处理成功")
                await asyncio.sleep(2)
                return True
        else:
                logger.log_result("验证码处理", "滑块验证码处理失败")
        return False


# =============================================================================
# 主爬虫协调器
# =============================================================================

class CarGurusCrawler:
    """CarGurus 主爬虫协调器 - 重构版本"""
    
    def __init__(self, date_str: str, make_name: str, zip_code: str, profile_name: str = None):
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
        self.profile_name = profile_name or browser_utils.generate_daily_profile_name("cargurus")
        
        # 配置参数
        self.output_dir = get_cargurus_data_dir() / date_str
        self.distance = 100
        self.max_pages = 50
        self.per_page = 24
        
        # 获取品牌代码
        self.make_code = CarGurusConfig.get_make_code(make_name)
        
        # 初始化各个组件
        self.data_saver = CarGurusDataSaver(self.output_dir)
        self.model_collector = CarGurusModelCollector(self.profile_name, zip_code, self.distance)
        self.car_searcher = CarGurusCarSearcher(self.profile_name)
        
        # 统计信息
        self.total_crawled = 0
        
        logger.log_result("爬虫初始化", f"CarGurus爬虫已就绪，Profile: {self.profile_name}")
        logger.log_result("查询参数", f"品牌: {make_name} ({self.make_code}), ZIP: {zip_code}")
    
    def get_city_zip_codes(self, city_name: str) -> List[str]:
        """根据城市名称获取ZIP代码列表"""
        return CarGurusConfig.get_city_zip_codes(city_name)
    
    async def search_cars(self, parsed_query: ParsedQuery, max_results: int = 20) -> List[CarListing]:
        """
        搜索车源 - 与CarGurusScraper兼容的接口
        
        Args:
            parsed_query: 解析后的查询参数
            max_results: 最大结果数量
            
        Returns:
            车源列表
        """
        return await self.car_searcher.search_cars(parsed_query, max_results)

    async def collect_models_for_brand(self, brand_name: str, limit: int = None) -> List[Dict[str, str]]:
        """收集指定品牌的车型数据"""
        return await self.model_collector.collect_models_for_brand(brand_name, limit)
    
    async def save_models_data(self, models: List[Dict[str, str]], brand_name: str, city: str = "toronto"):
        """保存车型数据到文件"""
        await self.data_saver.save_models_data(models, brand_name, self.date_str, city, self.zip_code, self.distance)


# 使用示例
async def main():
    """主函数示例"""
    try:
        # 创建爬虫实例
        date_str = "models"  # 去掉时间戳，使用固定名称
        make_name = "Toyota"
        zip_code = "M5V"
        
        crawler = CarGurusCrawler(date_str, make_name, zip_code)
        
        # 展示配置
        logger.log_result("配置展示", "支持的品牌: Toyota, Honda, BMW, Mercedes, Ford等")
        logger.log_result("配置展示", "支持的城市: Toronto, Vancouver, Montreal, Calgary等")
        
        # 获取城市ZIP代码示例
        city_zips = crawler.get_city_zip_codes("Toronto")
        logger.log_result("城市ZIP", f"Toronto的ZIP代码: {city_zips}")
        
        # 收集车型数据示例
        models = await crawler.collect_models_for_brand(make_name, limit=5)
        if models:
            await crawler.save_models_data(models, make_name)
        
        logger.log_result("任务完成", "CarGurus爬虫任务执行完成")
        
    except Exception as e:
        logger.log_result("任务失败", f"爬虫任务执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
