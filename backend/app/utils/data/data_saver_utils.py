"""
数据保存工具 - 提供车型数据保存功能

提供JSON格式的车型数据保存功能。
采用函数式设计，无默认值原则。
"""

from pathlib import Path
from typing import List, Dict
from .file_utils import ensure_directory, write_json_file


def save_models_data(
    models: List[Dict],
    brand_name: str,
    output_dir: Path,
    date_str: str,
    city: str,
    zip_code: str,
    distance: int
) -> Path:
    """
    保存车型数据到JSON文件

    Args:
        models: 车型数据列表
        brand_name: 品牌名称
        output_dir: 输出目录
        date_str: 日期字符串
        city: 城市名称
        zip_code: ZIP代码
        distance: 搜索距离

    Returns:
        保存的文件路径

    Raises:
        OSError: 当文件写入失败时
    """
    # 确保输出目录存在
    ensure_directory(output_dir)

    # 构建文件名
    filename = f"{brand_name}_{city}_{zip_code}_{distance}km_{date_str}.json"
    output_file = output_dir / filename

    # 构建保存数据
    save_data = {
        "metadata": {
            "brand": brand_name,
            "city": city,
            "zip_code": zip_code,
            "distance": distance,
            "date": date_str,
            "count": len(models)
        },
        "models": models
    }

    # 保存到JSON文件
    write_json_file(output_file, save_data)

    return output_file
