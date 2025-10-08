"""
数据提取工具 - 提供通用的数据提取和文本处理功能

提供安全的数据提取、文本清理、数字提取等功能。
采用函数式设计，无默认值原则。
"""

import re
from typing import Dict, Optional
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException


def extract_listing_data(listing: WebElement) -> Dict[str, str]:
    """
    提取单个listing的数据

    Args:
        listing: Selenium WebElement对象

    Returns:
        包含提取数据的字典

    Raises:
        NoSuchElementException: 当必需元素不存在时
    """
    data = {}

    # 提取标题
    data['title'] = safe_text(listing, ".//h3[@class='title']")

    # 提取价格
    data['price'] = safe_text(listing, ".//span[@class='price']")

    # 提取里程
    data['mileage'] = safe_text(listing, ".//span[@class='mileage']")

    # 提取年份
    data['year'] = safe_text(listing, ".//span[@class='year']")

    # 提取位置
    data['location'] = safe_text(listing, ".//span[@class='location']")

    # 提取链接
    data['link'] = safe_attr(listing, "href")

    return data


def extract_year_from_title(title: str) -> Optional[int]:
    """
    从标题中提取年份

    Args:
        title: 车源标题

    Returns:
        提取的年份，如果未找到则返回None

    Example:
        >>> extract_year_from_title("2020 Honda Civic")
        2020
        >>> extract_year_from_title("Honda Civic")
        None
    """
    if not title:
        return None

    # 匹配4位数字年份
    year_match = re.search(r'\b(19|20)\d{2}\b', title)
    if year_match:
        return int(year_match.group())
    return None


def extract_mileage(mileage_text: str) -> Optional[int]:
    """
    从里程文本中提取数字

    Args:
        mileage_text: 里程文本，如 "50,000 km" 或 "50K km"

    Returns:
        提取的里程数字，如果未找到则返回None

    Example:
        >>> extract_mileage("50,000 km")
        50000
        >>> extract_mileage("50K km")
        50000
        >>> extract_mileage("N/A")
        None
    """
    if not mileage_text:
        return None

    # 清理文本
    cleaned = mileage_text.lower().replace(',', '').replace(' ', '')

    # 处理 "N/A" 或空值
    if cleaned in ['n/a', 'na', '']:
        return None

    # 提取数字
    if 'k' in cleaned:
        # 处理 "50K" 格式
        number_match = re.search(r'(\d+(?:\.\d+)?)k', cleaned)
        if number_match:
            return int(float(number_match.group(1)) * 1000)
    else:
        # 处理普通数字格式
        number_match = re.search(r'(\d+(?:,\d{3})*)', cleaned)
        if number_match:
            return int(number_match.group(1).replace(',', ''))

    return None


def extract_price(price_text: str) -> Optional[float]:
    """
    从价格文本中提取数字

    Args:
        price_text: 价格文本，如 "$25,000" 或 "25,000 CAD"

    Returns:
        提取的价格数字，如果未找到则返回None

    Example:
        >>> extract_price("$25,000")
        25000.0
        >>> extract_price("25,000 CAD")
        25000.0
        >>> extract_price("Contact for price")
        None
    """
    if not price_text:
        return None

    # 清理文本
    cleaned = price_text.lower().replace(',', '').replace(' ', '')

    # 处理 "Contact for price" 等非数字价格
    if any(phrase in cleaned for phrase in ['contact', 'call', 'n/a', 'na']):
        return None

    # 提取数字
    number_match = re.search(r'(\d+(?:\.\d+)?)', cleaned)
    if number_match:
        return float(number_match.group(1))

    return None


def safe_text(element: WebElement, xpath: str) -> str:
    """
    安全提取元素文本

    Args:
        element: Selenium WebElement对象
        xpath: XPath表达式

    Returns:
        提取的文本，如果元素不存在则返回空字符串
    """
    try:
        sub_element = element.find_element("xpath", xpath)
        return clean_text(sub_element.text)
    except NoSuchElementException:
        return ""


def safe_attr(element: WebElement, attr: str) -> str:
    """
    安全获取元素属性

    Args:
        element: Selenium WebElement对象
        attr: 属性名

    Returns:
        属性值，如果属性不存在则返回空字符串
    """
    try:
        return element.get_attribute(attr) or ""
    except Exception:
        return ""


def clean_text(text: str) -> str:
    """
    清理文本数据

    Args:
        text: 原始文本

    Returns:
        清理后的文本

    Example:
        >>> clean_text("  Honda Civic  \n")
        "Honda Civic"
        >>> clean_text("")
        ""
    """
    if not text:
        return ""

    # 去除首尾空白字符
    cleaned = text.strip()

    # 替换多个连续空白字符为单个空格
    cleaned = re.sub(r'\s+', ' ', cleaned)

    return cleaned


def extract_make_model_from_title(title: str) -> Dict[str, str]:
    """
    从标题中提取品牌和车型

    Args:
        title: 车源标题

    Returns:
        包含make和model的字典

    Example:
        >>> extract_make_model_from_title("2020 Honda Civic")
        {"make": "Honda", "model": "Civic"}
    """
    if not title:
        return {"make": "", "model": ""}

    # 常见的汽车品牌
    brands = [
        "Honda", "Toyota", "Ford", "Chevrolet", "Nissan", "Hyundai", "Kia",
        "Mazda", "Subaru", "Volkswagen", "BMW", "Mercedes-Benz", "Audi",
        "Lexus", "Acura", "Infiniti", "Volvo", "Jaguar", "Land Rover",
        "Porsche", "Tesla", "Genesis"
    ]

    title_upper = title.upper()

    # 查找品牌
    make = ""
    for brand in brands:
        if brand.upper() in title_upper:
            make = brand
            break

    # 提取车型（品牌后面的部分）
    model = ""
    if make:
        # 找到品牌在标题中的位置
        make_index = title_upper.find(make.upper())
        if make_index != -1:
            # 获取品牌后面的文本
            after_make = title[make_index + len(make):].strip()
            # 去除年份
            after_make = re.sub(r'^\d{4}\s*', '', after_make)
            model = after_make.strip()

    return {"make": make, "model": model}


def extract_vin_from_text(text: str) -> Optional[str]:
    """
    从文本中提取VIN码

    Args:
        text: 包含VIN码的文本

    Returns:
        提取的VIN码，如果未找到则返回None

    Example:
        >>> extract_vin_from_text("VIN: 1HGBH41JXMN109186")
        "1HGBH41JXMN109186"
    """
    if not text:
        return None

    # VIN码通常是17位字母数字组合
    vin_pattern = r'\b[A-HJ-NPR-Z0-9]{17}\b'
    vin_match = re.search(vin_pattern, text.upper())

    if vin_match:
        return vin_match.group()

    return None


def extract_phone_number(text: str) -> Optional[str]:
    """
    从文本中提取电话号码

    Args:
        text: 包含电话号码的文本

    Returns:
        提取的电话号码，如果未找到则返回None

    Example:
        >>> extract_phone_number("Call: (416) 555-1234")
        "(416) 555-1234"
    """
    if not text:
        return None

    # 匹配常见的电话号码格式
    phone_patterns = [
        r'\(\d{3}\)\s*\d{3}-\d{4}',  # (416) 555-1234
        r'\d{3}-\d{3}-\d{4}',        # 416-555-1234
        r'\d{3}\.\d{3}\.\d{4}',      # 416.555.1234
        r'\d{10}',                    # 4165551234
    ]

    for pattern in phone_patterns:
        phone_match = re.search(pattern, text)
        if phone_match:
            return phone_match.group()

    return None


def extract_dealer_name(text: str) -> str:
    """
    从文本中提取经销商名称

    Args:
        text: 包含经销商信息的文本

    Returns:
        提取的经销商名称

    Example:
        >>> extract_dealer_name("Honda Downtown Toronto")
        "Honda Downtown Toronto"
    """
    if not text:
        return ""

    # 清理文本
    cleaned = clean_text(text)

    # 去除常见的后缀
    suffixes = ["Dealer", "Dealership", "Auto", "Motors", "Cars"]
    for suffix in suffixes:
        if cleaned.endswith(suffix):
            cleaned = cleaned[:-len(suffix)].strip()

    return cleaned


def extract_fuel_type(text: str) -> Optional[str]:
    """
    从文本中提取燃料类型

    Args:
        text: 包含燃料信息的文本

    Returns:
        提取的燃料类型，如果未找到则返回None

    Example:
        >>> extract_fuel_type("Gasoline Engine")
        "Gasoline"
        >>> extract_fuel_type("Electric Vehicle")
        "Electric"
    """
    if not text:
        return None

    text_lower = text.lower()

    fuel_types = {
        "gasoline": ["gas", "gasoline", "petrol"],
        "diesel": ["diesel"],
        "electric": ["electric", "ev", "battery"],
        "hybrid": ["hybrid"],
        "plug-in hybrid": ["plug-in hybrid", "phev"]
    }

    for fuel_type, keywords in fuel_types.items():
        if any(keyword in text_lower for keyword in keywords):
            return fuel_type

    return None


def extract_transmission(text: str) -> Optional[str]:
    """
    从文本中提取变速箱类型

    Args:
        text: 包含变速箱信息的文本

    Returns:
        提取的变速箱类型，如果未找到则返回None

    Example:
        >>> extract_transmission("Automatic Transmission")
        "Automatic"
        >>> extract_transmission("Manual 6-Speed")
        "Manual"
    """
    if not text:
        return None

    text_lower = text.lower()

    if "automatic" in text_lower or "auto" in text_lower:
        return "Automatic"
    elif "manual" in text_lower:
        return "Manual"
    elif "cvt" in text_lower:
        return "CVT"

    return None
