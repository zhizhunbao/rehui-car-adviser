"""
数据验证工具 - 提供通用的数据验证功能

提供各种数据验证函数，包括车型数据验证、URL验证等。
采用函数式设计，无默认值原则。
"""

from typing import Dict, Any


def is_valid_model(model_name: str, model_value: str) -> bool:
    """
    验证车型数据是否有效
    
    Args:
        model_name: 车型名称
        model_value: 车型代码/值
        
    Returns:
        bool: 如果车型数据有效返回True，否则返回False
    """
    if not model_name or not model_value:
        return False
    
    invalid_names = ["Any Model", "Select Model", "All Models", "Reset"]
    return model_name not in invalid_names


def is_valid_brand(brand_name: str) -> bool:
    """
    验证品牌名称是否有效
    
    Args:
        brand_name: 品牌名称
        
    Returns:
        bool: 如果品牌名称有效返回True，否则返回False
    """
    if not brand_name:
        return False
    
    invalid_names = ["Any Make", "Select Make", "All Makes", "Reset"]
    return brand_name not in invalid_names


def is_valid_year(year: str) -> bool:
    """
    验证年份是否有效
    
    Args:
        year: 年份字符串
        
    Returns:
        bool: 如果年份有效返回True，否则返回False
    """
    if not year:
        return False
    
    try:
        year_int = int(year)
        return 1900 <= year_int <= 2030
    except ValueError:
        return False


def is_valid_price(price: str) -> bool:
    """
    验证价格是否有效
    
    Args:
        price: 价格字符串
        
    Returns:
        bool: 如果价格有效返回True，否则返回False
    """
    if not price:
        return False
    
    # 移除货币符号和逗号
    clean_price = price.replace('$', '').replace(',', '').strip()
    
    try:
        price_float = float(clean_price)
        return price_float > 0
    except ValueError:
        return False


def is_valid_mileage(mileage: str) -> bool:
    """
    验证里程数是否有效
    
    Args:
        mileage: 里程数字符串
        
    Returns:
        bool: 如果里程数有效返回True，否则返回False
    """
    if not mileage:
        return False
    
    # 移除逗号和单位
    clean_mileage = mileage.replace(',', '').replace(' miles', '').replace(' mi', '').strip()
    
    try:
        mileage_int = int(clean_mileage)
        return mileage_int >= 0
    except ValueError:
        return False


def validate_listing_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    验证并清理listing数据
    
    Args:
        data: 原始数据字典
        
    Returns:
        Dict[str, Any]: 验证后的数据字典
    """
    validated_data = {}
    
    # 验证标题
    if data.get('title') and isinstance(data['title'], str):
        validated_data['title'] = data['title'].strip()
    
    # 验证价格
    if data.get('price') and is_valid_price(data['price']):
        validated_data['price'] = data['price']
    
    # 验证里程数
    if data.get('mileage') and is_valid_mileage(data['mileage']):
        validated_data['mileage'] = data['mileage']
    
    # 验证年份
    if data.get('year') and is_valid_year(data['year']):
        validated_data['year'] = data['year']
    
    # 验证品牌
    if data.get('brand') and is_valid_brand(data['brand']):
        validated_data['brand'] = data['brand']
    
    # 验证车型
    if data.get('model') and is_valid_model(data['model'], data.get('model_code', '')):
        validated_data['model'] = data['model']
        if data.get('model_code'):
            validated_data['model_code'] = data['model_code']
    
    return validated_data
