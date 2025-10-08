#!/usr/bin/env python3
"""
车型数据收集脚本 - 重构版本
使用新的utils模块和CarGurusCrawler，抓取每个品牌的车型数据
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, List
import aiofiles

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入项目模块
from app.services.cargurus_crawler import CarGurusCrawler  # noqa: E402
from app.utils.logger import logger  # noqa: E402
from app.utils.path_util import (  # noqa: E402
    get_cargurus_data_dir, get_data_dir
)
from app.utils.cargurus_config_utils import (  # noqa: E402
    get_all_makes, get_city_zip_codes, get_make_code
)
from app.utils.profile_utils import generate_daily_profile_name  # noqa: E402
from app.utils.browser_utils import browser_utils  # noqa: E402


def get_brand_code(brand_name: str) -> str:
    """获取品牌代码，用于CSV文件中的make_code字段"""
    # 使用cargurus_config_utils中的get_make_code函数
    return get_make_code(brand_name)


# 从cargurus_config_utils获取品牌列表
BRANDS = get_all_makes()




async def collect_models_for_brands(make: str = None,
                                    city: str = "toronto",
                                    delay: int = 3,
                                    output_dir: Path = None):
    """
    使用新的CarGurusCrawler和utils模块，抓取每个品牌的车型数据

    Args:
        make: 指定品牌名称，如果为None则收集所有品牌
        city: 城市名称
        delay: 品牌间延迟时间（秒）
        output_dir: 输出目录
    """
    try:
        # 获取城市ZIP代码
        zip_codes = get_city_zip_codes(city)
        if not zip_codes:
            logger.log_result("错误", f"城市 '{city}' 不在支持的城市列表中")
            return {}
        zip_code = zip_codes[0]  # 使用第一个ZIP代码

        # 生成profile名称
        profile_name = generate_daily_profile_name("cargurus")

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

        # 使用新的CarGurusCrawler收集所有品牌的车型
        all_models = {}

        # 创建一个crawler实例，重用浏览器
        crawler = CarGurusCrawler(
            date_str="models",
            make_name="",  # 不指定具体品牌
            zip_code=zip_code,
            profile_name=profile_name
        )

        # 创建一个浏览器实例，为所有品牌重用
        async with browser_utils.get_driver(profile_name) as driver:
            for i, brand_name in enumerate(brands_to_collect):
                # 检查文件是否已经存在，存在则跳过
                output_file = output_dir / f"models_{brand_name.lower()}.csv"
                if output_file.exists():
                    logger.log_result("跳过收集",
                                      f"{brand_name} 的CSV文件已存在，跳过收集")
                    continue

                logger.log_result("车型收集",
                                  f"正在收集 {brand_name} 的车型... "
                                  f"({i+1}/{len(brands_to_collect)})")

                try:
                    # 使用已存在的driver收集车型数据
                    models = await crawler.model_collector.\
                        collect_models_for_brand_with_driver(
                            driver, brand_name, 100
                        )

                    if models:
                        # 转换数据格式以保持兼容性
                        formatted_models = []
                        for model in models:
                            formatted_models.append({
                                "name": model.get("model_name", ""),
                                "value": model.get("model_code", "")
                            })
                        all_models[brand_name] = formatted_models
                        logger.log_result(
                            "车型收集",
                            f"{brand_name}: {len(formatted_models)} 个车型"
                        )

                        # 立即保存这个品牌的数据到CSV文件
                        await save_single_brand_to_csv(
                            brand_name, formatted_models, output_dir
                        )
                        logger.log_result("文件保存",
                                          f"{brand_name} 数据已保存到CSV文件")
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


async def save_single_brand_to_csv(
    brand_name: str, models: List[Dict[str, str]], output_dir: Path
) -> bool:
    """保存单个品牌的数据到CSV文件"""
    try:
        # 确保输出目录存在
        output_dir.mkdir(parents=True, exist_ok=True)

        # 构建文件名
        output_file = output_dir / f"models_{brand_name.lower()}.csv"

        # 获取品牌代码
        brand_code = get_brand_code(brand_name)

        # 准备CSV数据
        csv_data = []
        for model in models:
            csv_data.append({
                "make": brand_name,
                "make_code": brand_code,
                "model": model.get("name", ""),
                "model_code": model.get("value", "")
            })

        # 异步写入CSV文件
        csv_content = []
        fieldnames = ["make", "make_code", "model", "model_code"]

        # 构建CSV内容
        csv_content.append(",".join(fieldnames))  # 表头
        for row in csv_data:
            csv_row = []
            for field in fieldnames:
                value = str(row.get(field, "")).replace('"', '""')  # 转义双引号
                csv_row.append(f'"{value}"')
            csv_content.append(",".join(csv_row))

        # 异步写入文件
        async with aiofiles.open(output_file, 'w', encoding='utf-8') as f:
            await f.write('\n'.join(csv_content))

        return True
    except Exception as e:
        print(f"保存 {brand_name} 数据失败: {str(e)}")
        return False


async def save_models_to_csv(
    models_data: Dict[str, List[Dict[str, str]]], output_dir: Path
) -> bool:
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
            brand_code = get_make_code(brand_name)
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

            # 异步写入CSV文件
            csv_content = []
            fieldnames = ["make", "make_code", "model", "model_code"]

            # 构建CSV内容
            csv_content.append(",".join(fieldnames))  # 表头
            for row in csv_data:
                csv_row = []
                for field in fieldnames:
                    value = str(row.get(field, "")).replace('"', '""')  # 转义双引号
                    csv_row.append(f'"{value}"')
                csv_content.append(",".join(csv_row))

            # 异步写入文件
            async with aiofiles.open(output_file, 'w', encoding='utf-8') as f:
                await f.write('\n'.join(csv_content))

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

    parser = argparse.ArgumentParser(
        description="使用新的CarGurusCrawler和utils模块收集车型数据"
    )
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

    # 确定输出目录
    if args.output:
        output_dir = Path(args.output)
    else:
        # 使用统一的路径管理，保存到CarGurus数据目录
        output_dir = get_cargurus_data_dir()

    # 获取车型数据
    models_data = await collect_models_for_brands(
        make=args.make,
        city=args.city,
        delay=args.delay,
        output_dir=output_dir
    )

    if models_data:
        print(f"所有数据已实时保存到目录: {output_dir}")
        print(f"总共收集到 {len(models_data)} 个品牌的数据")
    else:
        print("未能获取到任何车型数据")


if __name__ == "__main__":
    asyncio.run(main())
