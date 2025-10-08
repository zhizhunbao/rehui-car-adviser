"""
URL构建工具 - 统一构建各种汽车网站的URL

提供CarGurus、Kijiji等汽车网站的URL构建功能。
采用函数式设计，无默认值原则。
"""

from typing import Optional
from urllib.parse import urlencode
import re


def build_cargurus_search_url(
    make: str, model: str, zip_code: str, distance: int,
    year_min: Optional[int] = None, year_max: Optional[int] = None,
    price_min: Optional[int] = None, price_max: Optional[int] = None,
    mileage_max: Optional[int] = None
) -> str:
    """构建CarGurus搜索URL"""
    base_url = (
        "https://www.cargurus.ca/Cars/inventorylisting/"
        "viewDetailsFilterViewInventoryListing.action"
    )

    params = {
        "zip": zip_code,
        "distance": distance,
        "entitySelectingHelper.selectedEntity": "d1",
        "entitySelectingHelper.selectedEntity2": "d2",
        "sourceContext": "carGurusHomePageModel",
        "inventorySearchWidgetType": "AUTO",
        "newSearchFromOverviewPage": "true",
        "makeName": make.lower(),
        "modelName": model.lower()
    }

    # 添加可选参数
    if year_min is not None:
        params["yearMin"] = year_min
    if year_max is not None:
        params["yearMax"] = year_max
    if price_min is not None:
        params["priceMin"] = price_min
    if price_max is not None:
        params["priceMax"] = price_max
    if mileage_max is not None:
        params["mileageMax"] = mileage_max

    return f"{base_url}?{urlencode(params)}"


def build_cargurus_brand_url(
    make: str, zip_code: str, distance: int
) -> str:
    """构建CarGurus品牌页面URL - 使用简洁的参数格式"""
    from app.utils.cargurus_config_utils import get_make_code

    base_url = (
        "https://www.cargurus.ca/Cars/inventorylisting/"
        "viewDetailsFilterViewInventoryListing.action"
    )

    # 获取品牌对应的实体代码
    make_code = get_make_code(make)
    if not make_code:
        # 如果找不到品牌代码，使用默认值
        make_code = "m7"

    params = {
        "zip": zip_code,
        "distance": distance,
        "makeModelTrimPaths": make_code
    }

    return f"{base_url}?{urlencode(params)}"


def build_cargurus_listing_url(listing_id: str) -> str:
    """构建CarGurus车源详情URL"""
    return f"https://www.cargurus.ca/Cars/link/{listing_id}"


def extract_listing_id_from_url(url: str) -> Optional[str]:
    """从URL中提取车源ID"""
    # CarGurus URL模式
    cargurus_pattern = r"/Cars/link/(\d+)"
    match = re.search(cargurus_pattern, url)
    if match:
        return match.group(1)

    # Kijiji URL模式
    kijiji_pattern = r"/cars/.*?/(\d+)/?$"
    match = re.search(kijiji_pattern, url)
    if match:
        return match.group(1)

    return None


def is_valid_cargurus_url(url: str) -> bool:
    """验证是否为有效的CarGurus URL"""
    return "cargurus.ca" in url and ("/Cars/" in url or "/cars/" in url)
