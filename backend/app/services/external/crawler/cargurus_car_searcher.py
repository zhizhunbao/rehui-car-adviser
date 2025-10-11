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

                # 调试：记录页面标题和URL
                logger.log_result("页面调试", f"当前页面标题: {driver.title}")
                logger.log_result(
                    "页面调试", f"当前页面URL: {driver.current_url}"
                )

                # 使用 utils 进行页面检测
                if is_blocked_page(driver.page_source):
                    logger.log_result("页面检测", "页面被封禁")
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
                            location=data.get("location", ""),
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

            # 先尝试中文品牌名称转换
            english_make_name = self._convert_chinese_brand_to_english(
                make_name
            )
            logger.log_result(
                "品牌名称转换",
                f"中文: {make_name} -> 英文: {english_make_name}",
            )

            # 使用 ConfigDAO 获取品牌代码
            make_code = await self.config_dao.get_make_code(english_make_name)
            logger.log_result(
                "获取品牌代码",
                f"品牌: {english_make_name} -> 代码: {make_code}",
            )
            return make_code

        except Exception as e:
            logger.log_result(f"获取品牌代码失败: {str(e)}")
            return make_name.lower().replace(" ", "-") if make_name else ""

    def _convert_chinese_brand_to_english(self, chinese_name: str) -> str:
        """将中文品牌名称转换为英文品牌名称"""
        # 中文品牌名称到英文品牌名称的映射
        brand_mapping = {
            "本田": "Honda",
            "丰田": "Toyota",
            "日产": "Nissan",
            "马自达": "Mazda",
            "斯巴鲁": "Subaru",
            "三菱": "Mitsubishi",
            "铃木": "Suzuki",
            "雷克萨斯": "Lexus",
            "英菲尼迪": "Infiniti",
            "讴歌": "Acura",
            "宝马": "BMW",
            "奔驰": "Mercedes-Benz",
            "奥迪": "Audi",
            "大众": "Volkswagen",
            "保时捷": "Porsche",
            "捷豹": "Jaguar",
            "路虎": "Land Rover",
            "沃尔沃": "Volvo",
            "萨博": "Saab",
            "现代": "Hyundai",
            "起亚": "Kia",
            "福特": "Ford",
            "雪佛兰": "Chevrolet",
            "别克": "Buick",
            "凯迪拉克": "Cadillac",
            "林肯": "Lincoln",
            "道奇": "Dodge",
            "克莱斯勒": "Chrysler",
            "吉普": "Jeep",
            "菲亚特": "Fiat",
            "阿尔法罗密欧": "Alfa Romeo",
            "玛莎拉蒂": "Maserati",
            "法拉利": "Ferrari",
            "兰博基尼": "Lamborghini",
            "宾利": "Bentley",
            "劳斯莱斯": "Rolls-Royce",
            "阿斯顿马丁": "Aston Martin",
            "迈凯伦": "McLaren",
        }

        # 如果输入的是中文，尝试转换
        if chinese_name in brand_mapping:
            return brand_mapping[chinese_name]

        # 如果输入的不是中文或没有映射，直接返回原名称
        return chinese_name

    def _convert_chinese_model_to_english(self, chinese_name: str) -> str:
        """将中文车型名称转换为英文车型名称"""
        # 中文车型名称到英文车型名称的映射
        model_mapping = {
            "雅阁": "Accord",
            "思域": "Civic",
            "CR-V": "CR-V",
            "飞度": "Fit",
            "奥德赛": "Odyssey",
            "Pilot": "Pilot",
            "Passport": "Passport",
            "Ridgeline": "Ridgeline",
            "Insight": "Insight",
            "Clarity": "Clarity",
            "凯美瑞": "Camry",
            "卡罗拉": "Corolla",
            "RAV4": "RAV4",
            "汉兰达": "Highlander",
            "普锐斯": "Prius",
            "普拉多": "Land Cruiser",
            "坦途": "Tundra",
            "塔科马": "Tacoma",
            "塞纳": "Sienna",
            "4Runner": "4Runner",
            "天籁": "Altima",
            "轩逸": "Sentra",
            "奇骏": "Rogue",
            "逍客": "Qashqai",
            "楼兰": "Murano",
            "途乐": "Pathfinder",
            "GT-R": "GT-R",
            "370Z": "370Z",
            "Leaf": "Leaf",
            "Versa": "Versa",
            "马自达3": "Mazda3",
            "马自达6": "Mazda6",
            "CX-5": "CX-5",
            "CX-9": "CX-9",
            "MX-5": "MX-5",
            "CX-3": "CX-3",
            "CX-30": "CX-30",
            "森林人": "Forester",
            "傲虎": "Outback",
            "力狮": "Legacy",
            "翼豹": "Impreza",
            "WRX": "WRX",
            "BRZ": "BRZ",
            "阿特兹": "Atenza",
            "昂克赛拉": "Axela",
            "欧蓝德": "Outlander",
            "蓝瑟": "Lancer",
            "帕杰罗": "Pajero",
            "Eclipse": "Eclipse",
            "雨燕": "Swift",
            "维特拉": "Vitara",
            "吉姆尼": "Jimny",
            "SX4": "SX4",
            "ES": "ES",
            "IS": "IS",
            "GS": "GS",
            "LS": "LS",
            "RX": "RX",
            "GX": "GX",
            "LX": "LX",
            "CT": "CT",
            "RC": "RC",
            "LC": "LC",
            "UX": "UX",
            "NX": "NX",
            "Q50": "Q50",
            "Q60": "Q60",
            "Q70": "Q70",
            "QX50": "QX50",
            "QX60": "QX60",
            "QX70": "QX70",
            "QX80": "QX80",
            "MDX": "MDX",
            "RDX": "RDX",
            "TLX": "TLX",
            "ILX": "ILX",
            "NSX": "NSX",
        }

        # 如果输入的是中文，尝试转换
        if chinese_name in model_mapping:
            return model_mapping[chinese_name]

        # 如果输入的不是中文或没有映射，直接返回原名称
        return chinese_name

    async def _get_model_code_from_db(
        self, make_name: str, model_name: str
    ) -> str:
        """从数据库获取车型代码"""
        try:
            if not make_name or not model_name:
                return ""

            # 先转换品牌和车型名称
            english_make_name = self._convert_chinese_brand_to_english(
                make_name
            )
            english_model_name = self._convert_chinese_model_to_english(
                model_name
            )

            logger.log_result(
                "车型名称转换",
                f"品牌: {make_name} -> {english_make_name}, 车型: {model_name} -> {english_model_name}",
            )

            # 使用 ConfigDAO 获取车型代码
            model_code = await self.config_dao.get_model_code(
                english_make_name, english_model_name
            )
            logger.log_result(
                "获取车型代码",
                f"品牌: {english_make_name}, 车型: {english_model_name} -> 代码: {model_code}",
            )
            return model_code

        except Exception as e:
            logger.log_result(f"获取车型代码失败: {str(e)}")
            return (
                model_name.lower().replace(" ", "-").replace("/", "-")
                if model_name
                else ""
            )
