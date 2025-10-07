import re
import asyncio
from typing import List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, WebDriverException
)
from app.models.schemas import CarListing, ParsedQuery
from app.utils.logger import logger


class CarGurusScraper:
    def __init__(self):
        self.base_url = "https://www.cargurus.ca"
        self.driver = None
        # 关键部位日志：服务初始化
        logger.log_result("爬虫服务初始化", "CarGurus爬虫已就绪")
    
    def _setup_driver(self):
        """设置Chrome WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(
            "--disable-blink-features=AutomationControlled"
        )
        chrome_options.add_experimental_option(
            "excludeSwitches", ["enable-automation"]
        )
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 "
            "Safari/537.36"
        )
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', "
                "{get: () => undefined})"
            )
            self.driver.implicitly_wait(20)
        except Exception as e:
            logger.log_result(
                "爬虫初始化失败", f"WebDriver设置失败: {str(e)}"
            )
            raise
    
    def _cleanup_driver(self):
        """清理WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def _build_search_url(self, parsed_query: ParsedQuery) -> str:
        """构建CarGurus搜索URL"""
        params = []
        
        # 品牌和型号
        if parsed_query.make:
            params.append(f"make={parsed_query.make}")
        if parsed_query.model:
            params.append(f"model={parsed_query.model}")
        
        # 年份范围
        if parsed_query.year_min:
            params.append(f"yearMin={parsed_query.year_min}")
        if parsed_query.year_max:
            params.append(f"yearMax={parsed_query.year_max}")
        
        # 价格范围
        if parsed_query.price_max:
            params.append(f"priceMax={int(parsed_query.price_max)}")
        
        # 里程范围
        if parsed_query.mileage_max:
            params.append(f"mileageMax={int(parsed_query.mileage_max)}")
        
        # 位置
        if parsed_query.location:
            params.append(f"location={parsed_query.location}")
        
        # 构建URL
        if params:
            base_path = (
                "/Cars/inventorylisting/"
                "viewDetailsFilterViewInventoryListing.action"
            )
            search_url = f"{self.base_url}{base_path}?{'&'.join(params)}"
        else:
            # 如果没有具体参数，使用关键词搜索
            keywords = " ".join(parsed_query.keywords)
            base_path = (
                "/Cars/inventorylisting/"
                "viewDetailsFilterViewInventoryListing.action"
            )
            search_url = (
                f"{self.base_url}{base_path}?"
                f"sourceContext=carGurusHomePageModel&"
                f"inventorySearchWidgetType=PRICE&searchText={keywords}"
            )
        
        return search_url
    
    def _extract_car_info(self, car_element) -> Optional[CarListing]:
        """从车源元素中提取信息"""
        try:
            # 提取标题
            title_element = car_element.find_element(
                By.CSS_SELECTOR, "h4 a, .cg-listing-title a"
            )
            title = title_element.text.strip()
            link = title_element.get_attribute("href")
            
            # 提取价格
            try:
                price_element = car_element.find_element(
                    By.CSS_SELECTOR, ".cg-listing-price, .price"
                )
                price = price_element.text.strip()
            except NoSuchElementException:
                price = "价格面议"
            
            # 提取年份、里程、城市等信息
            try:
                details_element = car_element.find_element(
                    By.CSS_SELECTOR, ".cg-listing-details, .listing-details"
                )
                details_text = details_element.text.strip()
                
                # 使用正则表达式提取年份
                year_match = re.search(r'(\d{4})', details_text)
                year = int(year_match.group(1)) if year_match else 2020
                
                # 提取里程
                mileage_match = re.search(
                    r'(\d{1,3}(?:,\d{3})*)\s*km', details_text, re.IGNORECASE
                )
                mileage = (
                    mileage_match.group(1) + " km"
                    if mileage_match else "里程未知"
                )
                
                # 提取城市
                city_match = re.search(
                    r'([A-Za-z\s]+),\s*[A-Z]{2}', details_text
                )
                city = (
                    city_match.group(1).strip()
                    if city_match else "位置未知"
                )
                
            except NoSuchElementException:
                year = 2020
                mileage = "里程未知"
                city = "位置未知"
            
            # 生成唯一ID
            car_id = f"cg_{hash(title + str(year) + price)}"
            
            return CarListing(
                id=car_id,
                title=title,
                price=price,
                year=year,
                mileage=mileage,
                city=city,
                link=(
                    link if link.startswith('http')
                    else f"{self.base_url}{link}"
                )
            )
            
        except Exception:
            return None
    
    async def search_cars(
        self, parsed_query: ParsedQuery, max_results: int = 20
    ) -> List[CarListing]:
        """搜索车源（带重试机制）"""
        # 关键部位日志：外部调用 - 爬虫搜索
        logger.log_result(
            "开始爬虫搜索", f"查询: {parsed_query.make} {parsed_query.model}"
        )
        
        max_retries = 3
        retry_delay = 2  # 秒
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    logger.log_result("爬虫重试", f"第{attempt + 1}次尝试")
                    await asyncio.sleep(retry_delay * attempt)
                
                self._setup_driver()
                cars = []
                
                search_url = self._build_search_url(parsed_query)
                logger.log_result("爬虫访问", f"URL: {search_url}")
                
                self.driver.get(search_url)
                
                # 等待页面加载，增加超时时间，使用多个选择器
                try:
                    WebDriverWait(self.driver, 30).until(
                        EC.presence_of_element_located((
                            By.CSS_SELECTOR,
                            ".cg-listing, .listing-item, "
                            "[data-cg-ft='listing'], .listing"
                        ))
                    )
                except TimeoutException:
                    # 如果主要选择器超时，尝试其他选择器
                    logger.log_result(
                        "爬虫搜索警告", "主要选择器超时，尝试备用选择器"
                    )
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, "body")
                        )
                    )
                
                # 获取车源元素，使用多个选择器
                car_elements = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    ".cg-listing, .listing-item, "
                    "[data-cg-ft='listing'], .listing"
                )
                
                if not car_elements:
                    logger.log_result(
                        "爬虫搜索警告", "未找到车源元素，尝试其他选择器"
                    )
                    # 尝试其他可能的选择器
                    car_elements = self.driver.find_elements(
                        By.CSS_SELECTOR,
                        ".listing, .car-listing, .vehicle-listing"
                    )
                
                for i, car_element in enumerate(car_elements[:max_results]):
                    car_info = self._extract_car_info(car_element)
                    if car_info:
                        cars.append(car_info)
                
                # 关键部位日志：状态变化 - 搜索结果
                logger.log_result("爬虫搜索完成", f"找到{len(cars)}辆车源")
                return cars
                
            except (TimeoutException, WebDriverException) as e:
                logger.log_result(
                    "爬虫搜索失败", f"第{attempt + 1}次尝试失败: {str(e)}"
                )
                if attempt == max_retries - 1:
                    logger.log_result(
                        "爬虫搜索失败", f"所有重试失败，最终错误: {str(e)}"
                    )
                    return []
            except Exception as e:
                logger.log_result(
                    "爬虫搜索失败", f"未预期错误: {str(e)}"
                )
                return []
            finally:
                self._cleanup_driver()
        
        return []
