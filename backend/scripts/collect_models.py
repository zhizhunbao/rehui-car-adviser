#!/usr/bin/env python3
"""
车型数据收集脚本
使用MAKE_CODES映射中的品牌列表，抓取每个品牌的车型数据
"""

import asyncio
import csv
import sys
from pathlib import Path
from typing import Dict, List

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入项目模块
from app.services.cargurus_crawler import (  # noqa: E402
    CarGurusModelCollector, CarGurusConfig
)
from app.utils.logger import logger  # noqa: E402
from app.utils.path_util import (  # noqa: E402
    get_cargurus_data_dir, get_data_dir
)
from app.utils.browser_utils import browser_utils  # noqa: E402

# 直接从MAKE_CODES映射获取品牌列表
BRANDS = list(CarGurusConfig.MAKE_CODES.keys())


async def collect_models_for_brands(make: str = None,
                                    city: str = "toronto",
                                    delay: int = 3):
    """
    使用MAKE_CODES映射中的品牌列表，抓取每个品牌的车型数据

    Args:
        make: 指定品牌名称，如果为None则收集所有品牌
        city: 城市名称
        delay: 品牌间延迟时间（秒）
    """
    try:
        # 直接创建ModelCollector，避免创建不必要的目录
        zip_code = "M5V"  # 默认使用多伦多ZIP

        # 获取城市ZIP代码
        zip_codes = CarGurusConfig.get_city_zip_codes(city)
        if zip_codes:
            zip_code = zip_codes[0]

        # 创建ModelCollector实例
        profile_name = browser_utils.generate_daily_profile_name("cargurus")
        model_collector = CarGurusModelCollector(profile_name, zip_code, 100)

        # 确定要收集的品牌列表
        if make:
            if make.lower() in [brand.lower() for brand in BRANDS]:
                brands_to_collect = [
                    brand for brand in BRANDS
                    if brand.lower() == make.lower()
                ]
            else:
                logger.log_result("错误",
                                  f"品牌 '{make}' 不在支持的品牌列表中")
                return {}
        else:
            brands_to_collect = BRANDS

        logger.log_result("开始收集",
                          f"城市: {city}, ZIP: {zip_code}, 延迟: {delay}秒")
        logger.log_result("品牌列表",
                          f"将收集 {len(brands_to_collect)} 个品牌的车型数据")

        # 使用单个浏览器实例收集所有品牌的车型
        all_models = {}

        async with browser_utils.get_driver(profile_name) as driver:
            for i, brand_name in enumerate(brands_to_collect):
                logger.log_result("车型收集",
                                  f"正在收集 {brand_name} 的车型... "
                                  f"({i+1}/{len(brands_to_collect)})")

                try:
                    # 直接调用model_collector的方法，传入driver
                    models = await (
                        model_collector
                        .collect_models_for_brand_with_driver(
                            driver, brand_name)
                    )

                    if models:
                        all_models[brand_name] = models
                        logger.log_result("车型收集",
                                          f"{brand_name}: {len(models)} 个车型")
                    else:
                        logger.log_result("车型收集",
                                          f"{brand_name}: 无车型数据")

                    # 添加延迟避免被封
                    if i < len(brands_to_collect) - 1:  # 最后一个品牌不需要延迟
                        logger.log_result("等待", f"等待 {delay} 秒...")
                        await asyncio.sleep(delay)

                except Exception as e:
                    logger.log_result("车型收集失败", f"{brand_name}: {str(e)}")
                    continue

        logger.log_result("收集完成",
                          f"总共收集到 {len(all_models)} 个品牌的车型数据")
        return all_models

    except Exception as e:
        logger.log_result("收集失败", f"获取车型数据失败: {str(e)}")
        return {}


def save_models_to_csv(models_data: Dict[str, List[Dict[str, str]]],
                       output_dir: Path) -> bool:
    """为每个品牌保存单独的CSV文件"""
    try:
        # 确保输出目录存在
        output_dir.mkdir(parents=True, exist_ok=True)

        total_saved = 0
        saved_files = []

        for brand_name, models in models_data.items():
            if not models:
                continue

            # 为每个品牌生成单独的文件名，使用品牌名称而不是代码
            brand_code = CarGurusConfig.get_make_code(brand_name)
            # 使用品牌名称的小写形式作为文件名
            brand_name_lower = brand_name.lower()
            output_file = output_dir / f"models_{brand_name_lower}.csv"

            # 准备该品牌的CSV数据
            csv_data = []
            for model in models:
                csv_data.append({
                    "make": brand_name.title(),
                    "make_code": brand_code,
                    "model": model.get("name", ""),
                    "model_code": model.get("value", "")
                })

            # 写入CSV文件
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ["make", "make_code", "model", "model_code"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)

            total_saved += len(csv_data)
            saved_files.append(f"{brand_name.title()}: {len(csv_data)} 条记录 -> "
                               f"{output_file.name}")

        logger.log_result("CSV文件保存",
                          f"成功保存 {total_saved} 条车型数据到 "
                          f"{len(saved_files)} 个文件")
        for file_info in saved_files:
            logger.log_result("", f"  {file_info}")
        return True

    except Exception as e:
        logger.log_result("CSV文件保存失败",
                          f"保存车型数据失败: {str(e)}")
        return False


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="使用MAKE_CODES映射收集车型数据")
    parser.add_argument("--make", help="指定品牌名称，如果不指定则收集所有品牌")
    parser.add_argument("--city", default="toronto", help="城市名称")
    parser.add_argument("--delay", type=int, default=3, help="品牌间延迟时间（秒）")
    parser.add_argument("--output", help="输出文件路径")

    args = parser.parse_args()

    # 显示数据目录信息
    data_dir = get_data_dir()
    cargurus_dir = get_cargurus_data_dir()
    print(f"数据目录: {data_dir}")
    print(f"CarGurus数据目录: {cargurus_dir}")
    print(f"默认输出目录: {cargurus_dir}")
    print("-" * 50)

    # 获取车型数据
    models_data = await collect_models_for_brands(
        make=args.make,
        city=args.city,
        delay=args.delay
    )

    if models_data:
        # 输出结果
        if args.output:
            output_dir = Path(args.output)
        else:
            # 使用统一的路径管理，保存到CarGurus数据目录
            output_dir = get_cargurus_data_dir()

        # 保存为CSV格式（每个品牌一个文件）
        success = save_models_to_csv(models_data, output_dir)
        if success:
            print(f"数据已保存到目录: {output_dir}")
        else:
            print("保存数据失败")
    else:
        print("未能获取到任何车型数据")


if __name__ == "__main__":
    asyncio.run(main())
