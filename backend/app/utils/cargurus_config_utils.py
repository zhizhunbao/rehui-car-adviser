"""
配置数据工具 - 管理爬虫相关的配置数据

提供城市映射、品牌映射等配置数据的统一管理。
采用函数式设计，无默认值原则。
动态加载CSV数据，避免硬编码。
"""

import csv
from typing import List, Dict
from functools import lru_cache
from .path_util import get_cargurus_data_dir


# 主要城市及其ZIP代码映射
MAJOR_CITIES = {
    "toronto": ["M5V", "M6G", "M4Y", "M5A", "M5H", "M5B", "M5C", "M5E"],
    "vancouver": ["V6B", "V6Z", "V6E", "V6H", "V6J", "V6K", "V6L", "V6M"],
    "montreal": ["H3A", "H3B", "H3G", "H3H", "H3J", "H3K", "H3L", "H3M"],
    "calgary": ["T2P", "T2R", "T2S", "T2T", "T2V", "T2W", "T2X", "T2Y"],
    "ottawa": ["K1P", "K1R", "K1S", "K1T", "K1V", "K1W", "K1X", "K1Y"],
    "edmonton": ["T5J", "T5K", "T5L", "T5M", "T5N", "T5P", "T5R", "T5S"],
    "winnipeg": ["R3B", "R3C", "R3E", "R3G", "R3H", "R3J", "R3K", "R3L"],
    "halifax": ["B3H", "B3J", "B3K", "B3L", "B3M", "B3N", "B3P", "B3R"]
}

# 数据文件路径
DATA_DIR = get_cargurus_data_dir()
MAKES_CSV_PATH = DATA_DIR / "makes.csv"
MODELS_CSV_DIR = DATA_DIR


def _load_makes_from_csv() -> Dict[str, str]:
    """从CSV文件加载汽车品牌代码映射"""
    make_codes = {}
    try:
        if MAKES_CSV_PATH.exists():
            with open(MAKES_CSV_PATH, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    make_name = row['make'].lower()
                    make_code = row['make_code']
                    make_codes[make_name] = make_code
    except Exception as e:
        print(f"Error loading makes from CSV: {e}")
    return make_codes


def _load_models_from_csv(make_name: str) -> Dict[str, str]:
    """从CSV文件加载指定品牌的型号代码映射"""
    models = {}
    try:
        csv_file = MODELS_CSV_DIR / f"models_{make_name.lower()}.csv"
        if csv_file.exists():
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    model_name = row['model'].lower()
                    model_code = row['model_code']
                    models[model_name] = model_code
    except Exception as e:
        print(f"Error loading models for {make_name} from CSV: {e}")
    return models


def _load_all_models_from_csv() -> Dict[str, Dict[str, str]]:
    """从CSV文件加载所有品牌的型号代码映射"""
    all_models = {}
    try:
        # 获取所有models_*.csv文件
        for csv_file in MODELS_CSV_DIR.glob('models_*.csv'):
            make_name = csv_file.stem[7:]  # 移除'models_'前缀
            models = _load_models_from_csv(make_name)
            if models:
                all_models[make_name] = models
    except Exception as e:
        print(f"Error loading all models from CSV: {e}")
    return all_models


# 动态加载数据
MAKE_CODES = _load_makes_from_csv()
MODEL_CODES = _load_all_models_from_csv()


# 距离选项
DISTANCE_OPTIONS = [10, 25, 50, 100, 200, 500]

# 年份范围
YEAR_RANGE = {
    "min": 1990,
    "max": 2025
}


@lru_cache(maxsize=128)
def get_city_zip_codes(city_name: str) -> List[str]:
    """根据城市名称获取ZIP代码列表"""
    if not city_name or not isinstance(city_name, str):
        return []
    return MAJOR_CITIES.get(city_name.lower(), [])


@lru_cache(maxsize=128)
def get_make_code(make_name: str) -> str:
    """根据品牌名称获取品牌代码"""
    if not make_name or not isinstance(make_name, str):
        return ""
    return MAKE_CODES.get(make_name.lower(), "")


def get_all_cities() -> List[str]:
    """获取所有支持的城市列表"""
    return list(MAJOR_CITIES.keys())


def get_all_makes() -> List[str]:
    """获取所有支持的品牌列表"""
    return list(MAKE_CODES.keys())


def get_distance_options() -> List[int]:
    """获取可用的距离选项"""
    return DISTANCE_OPTIONS.copy()


def get_year_range() -> Dict[str, int]:
    """获取年份范围"""
    return YEAR_RANGE.copy()


def validate_city_name(city_name: str) -> bool:
    """验证城市名称是否有效"""
    if not city_name or not isinstance(city_name, str):
        return False
    return city_name.lower() in MAJOR_CITIES


def validate_make_name(make_name: str) -> bool:
    """验证品牌名称是否有效"""
    if not make_name or not isinstance(make_name, str):
        return False
    return make_name.lower() in MAKE_CODES


@lru_cache(maxsize=128)
def get_model_code(make_name: str, model_name: str) -> str:
    """根据品牌名称和型号名称获取型号代码"""
    if (not make_name or not model_name or
            not isinstance(make_name, str) or not isinstance(model_name, str)):
        return ""

    make_key = make_name.lower()
    model_key = model_name.lower()

    if make_key not in MODEL_CODES:
        return ""

    return MODEL_CODES[make_key].get(model_key, "")


def get_all_models_for_make(make_name: str) -> List[str]:
    """获取指定品牌的所有型号列表"""
    if not make_name or not isinstance(make_name, str):
        return []

    make_key = make_name.lower()
    if make_key not in MODEL_CODES:
        return []

    return list(MODEL_CODES[make_key].keys())


def validate_model_name(make_name: str, model_name: str) -> bool:
    """验证型号名称是否有效"""
    if (not make_name or not model_name or
            not isinstance(make_name, str) or not isinstance(model_name, str)):
        return False

    make_key = make_name.lower()
    model_key = model_name.lower()

    if make_key not in MODEL_CODES:
        return False

    return model_key in MODEL_CODES[make_key]


def get_all_makes_with_models() -> List[str]:
    """获取所有有型号数据的品牌列表"""
    return list(MODEL_CODES.keys())
