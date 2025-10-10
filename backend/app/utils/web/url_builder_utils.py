"""
URL构建工具 - 统一构建各种汽车网站的URL

提供CarGurus、Kijiji等汽车网站的URL构建功能。
采用纯函数设计，不依赖任何外部服务。

架构原则：
- 工具层应该是纯函数，无副作用
- 不直接调用DAO层或其他服务层
- 配置数据由调用方（服务层）提供
- 遵循单一职责原则
"""

import re
import uuid
from typing import Optional
from urllib.parse import quote, urlencode


def build_cargurus_search_url(
    make: str,
    model: str,
    zip_code: str,
    distance: int,
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    price_min: Optional[int] = None,
    price_max: Optional[int] = None,
    mileage_max: Optional[int] = None,
    make_code: Optional[str] = None,
    model_code: Optional[str] = None,
) -> str:
    """
    构建CarGurus搜索URL - 纯函数版本

    工具层应该是纯函数，不依赖任何外部服务。
    配置数据由调用方（服务层）提供。
    """
    base_url = (
        "https://www.cargurus.ca/Cars/inventorylisting/"
        "viewDetailsFilterViewInventoryListing.action"
    )

    # 使用传入的代码，如果没有则回退到使用名称（进行URL编码）
    if not make_code:
        make_code = quote(make)
    if not model_code:
        model_code = quote(model)

    # 构建参数列表
    param_list = [
        ("zip", zip_code),
        ("distance", distance),
        ("sourceContext", "untrackedWithinSite_false_0"),
        ("sortDir", "ASC"),
        ("sortType", "DEAL_SCORE"),
        ("srpVariation", "DEFAULT_SEARCH"),
        ("isDeliveryEnabled", "true"),
        ("nonShippableBaseline", "0"),
    ]

    # 构建makeModelTrimPaths参数 - 添加两个参数：品牌和品牌/车型
    # 先添加品牌参数
    param_list.append(("makeModelTrimPaths", make_code))

    # 如果有车型代码且与品牌代码不同，添加品牌/车型组合参数
    if model_code and model_code != make_code:
        # 检查model_code是否已经包含make_code（即已经是完整路径）
        if model_code.startswith(f"{make_code}/"):
            # model_code已经是完整路径，直接使用
            make_model_path = model_code
        else:
            # 如果车型代码不包含品牌代码，则组合
            make_model_path = f"{make_code}/{model_code}"
        param_list.append(("makeModelTrimPaths", make_model_path))

    # 添加entitySelectingHelper.selectedEntity参数
    param_list.append(("entitySelectingHelper.selectedEntity", make_code))

    # 添加可选参数（使用实际参数名，确保整数格式）
    if year_min is not None:
        param_list.append(("startYear", int(year_min)))
    if year_max is not None:
        param_list.append(("endYear", int(year_max)))
    if price_min is not None:
        param_list.append(("minPrice", int(price_min)))
    if price_max is not None:
        param_list.append(("maxPrice", int(price_max)))
    if mileage_max is not None:
        param_list.append(("maxMileage", int(mileage_max)))

    # 动态生成searchId，避免反爬虫检测
    search_id = str(uuid.uuid4())
    param_list.append(("searchId", search_id))

    return f"{base_url}?{urlencode(param_list)}"


def build_cargurus_brand_url(
    make: str, zip_code: str, distance: int, make_code: Optional[str] = None
) -> str:
    """
    构建CarGurus品牌页面URL - 纯函数版本

    工具层应该是纯函数，不依赖任何外部服务。
    配置数据由调用方（服务层）提供。
    """
    base_url = (
        "https://www.cargurus.ca/Cars/inventorylisting/"
        "viewDetailsFilterViewInventoryListing.action"
    )

    # 使用传入的代码，如果没有则回退到使用名称（进行URL编码）
    if not make_code:
        make_code = quote(make)

    params = {
        "zip": zip_code,
        "distance": distance,
        "makeModelTrimPaths": make_code,
        "searchId": str(uuid.uuid4()),  # 动态生成searchId
    }

    return f"{base_url}?{urlencode(params)}"


def build_cargurus_model_url(
    make: str,
    model: str,
    zip_code: str,
    distance: int,
    make_code: Optional[str] = None,
    model_code: Optional[str] = None,
) -> str:
    """
    构建CarGurus车型页面URL - 纯函数版本

    工具层应该是纯函数，不依赖任何外部服务。
    配置数据由调用方（服务层）提供。
    """
    base_url = (
        "https://www.cargurus.ca/Cars/inventorylisting/"
        "viewDetailsFilterViewInventoryListing.action"
    )

    # 使用传入的代码，如果没有则回退到使用名称（进行URL编码）
    if not make_code:
        make_code = quote(make)
    if not model_code:
        model_code = quote(model)

    # 构建makeModelTrimPaths参数
    make_model_path = f"{make_code}/{model_code}"

    params = {
        "zip": zip_code,
        "distance": distance,
        "makeModelTrimPaths": make_model_path,
        "searchId": str(uuid.uuid4()),  # 动态生成searchId
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
