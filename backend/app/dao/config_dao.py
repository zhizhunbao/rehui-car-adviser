#!/usr/bin/env python3
"""
配置数据 DAO - 使用直接数据库连接
处理配置相关的数据库操作，包括城市映射、品牌映射等
"""

from functools import lru_cache
from typing import Any, Dict, List

from app.utils.core.logger import get_logger
from app.utils.data.db_utils import get_db_util

logger = get_logger(__name__)


class ConfigDAO:
    """
    配置数据 DAO
    使用直接数据库连接处理配置相关的数据库操作
    主要使用car_models表来获取品牌和车型代码映射
    """

    def __init__(self):
        """初始化配置DAO"""
        logger.log_result("ConfigDAO初始化", "使用直接数据库连接")

    async def get_city_zip_codes(self, city_name: str) -> List[str]:
        """
        根据城市名称获取ZIP代码列表

        Args:
            city_name: 城市名称

        Returns:
            ZIP代码列表
        """
        if not city_name or not isinstance(city_name, str):
            return []

        try:
            logger.log_result("获取城市ZIP代码", f"城市: {city_name}")

            # 使用数据库查询城市ZIP代码
            db_util = await get_db_util()

            # 查询城市ZIP代码
            query = """
                SELECT zip_codes FROM city_zip_mapping 
                WHERE city_name ILIKE $1
            """
            result = await db_util.execute_sql(
                query, {"city_name": f"%{city_name}%"}
            )

            if result:
                # 假设zip_codes存储为逗号分隔的字符串
                zip_codes_str = result[0].get("zip_codes", "")
                return [
                    zip_code.strip()
                    for zip_code in zip_codes_str.split(",")
                    if zip_code.strip()
                ]

            # 如果没有找到，返回空列表
            return []

        except Exception as e:
            logger.log_result(f"获取城市ZIP代码失败: {str(e)}")
            return []

    async def get_make_code(self, make_name: str) -> str:
        """
        根据品牌名称获取品牌代码

        Args:
            make_name: 品牌名称

        Returns:
            品牌代码
        """
        if not make_name or not isinstance(make_name, str):
            return ""

        try:
            logger.log_result("获取品牌代码", f"品牌: {make_name}")

            # 使用car_models表查询品牌代码
            db_util = await get_db_util()

            # 查询品牌代码
            query = """
                SELECT DISTINCT make_code FROM car_models 
                WHERE make ILIKE $1
                LIMIT 1
            """
            result = await db_util.execute_sql(
                query, {"make_name": f"%{make_name}%"}
            )

            if result:
                make_code = result[0].get("make_code", "")
                logger.log_result(
                    "获取品牌代码成功",
                    f"品牌: {make_name} -> 代码: {make_code}",
                )
                return make_code
            else:
                logger.log_result("品牌代码未找到", f"品牌: {make_name}")
                return make_name.lower().replace(" ", "-")

        except Exception as e:
            logger.log_result(f"获取品牌代码失败: {str(e)}")
            return make_name.lower().replace(" ", "-") if make_name else ""

    async def get_model_code(self, make_name: str, model_name: str) -> str:
        """
        根据品牌和车型名称获取车型代码

        Args:
            make_name: 品牌名称
            model_name: 车型名称

        Returns:
            车型代码
        """
        if (
            not make_name
            or not model_name
            or not isinstance(make_name, str)
            or not isinstance(model_name, str)
        ):
            return ""

        try:
            logger.log_result(
                "获取车型代码", f"品牌: {make_name}, 车型: {model_name}"
            )

            # 使用car_models表查询车型代码
            db_util = await get_db_util()

            # 查询车型代码
            query = """
                SELECT model_code FROM car_models 
                WHERE make ILIKE $1 AND model ILIKE $2
                LIMIT 1
            """
            result = await db_util.execute_sql(
                query,
                {
                    "make_name": f"%{make_name}%",
                    "model_name": f"%{model_name}%",
                },
            )

            if result:
                model_code = result[0].get("model_code", "")
                logger.log_result(
                    "获取车型代码成功",
                    f"品牌: {make_name}, 车型: {model_name} -> 代码: {model_code}",
                )
                return model_code
            else:
                logger.log_result(
                    "车型代码未找到", f"品牌: {make_name}, 车型: {model_name}"
                )
                return model_name.lower().replace(" ", "-").replace("/", "-")

        except Exception as e:
            logger.log_result(f"获取车型代码失败: {str(e)}")
            return (
                model_name.lower().replace(" ", "-").replace("/", "-")
                if model_name
                else ""
            )

    async def get_all_makes(self) -> List[Dict[str, str]]:
        """
        获取所有品牌及其代码

        Returns:
            品牌列表，包含make和make_code
        """
        try:
            logger.log_result("获取所有品牌", "从car_models表查询")

            db_util = await get_db_util()
            query = """
                SELECT DISTINCT make, make_code 
                FROM car_models 
                ORDER BY make
            """
            result = await db_util.execute_sql(query)

            makes = [
                {"make": row["make"], "make_code": row["make_code"]}
                for row in result
            ]
            logger.log_result("获取品牌成功", f"共{len(makes)}个品牌")
            return makes

        except Exception as e:
            logger.log_result(f"获取所有品牌失败: {str(e)}")
            return []

    async def get_models_by_make(self, make_name: str) -> List[Dict[str, str]]:
        """
        根据品牌获取所有车型

        Args:
            make_name: 品牌名称

        Returns:
            车型列表，包含model和model_code
        """
        if not make_name or not isinstance(make_name, str):
            return []

        try:
            logger.log_result("获取品牌车型", f"品牌: {make_name}")

            db_util = await get_db_util()
            query = """
                SELECT DISTINCT model, model_code 
                FROM car_models 
                WHERE make ILIKE $1
                ORDER BY model
            """
            result = await db_util.execute_sql(
                query, {"make_name": f"%{make_name}%"}
            )

            models = [
                {"model": row["model"], "model_code": row["model_code"]}
                for row in result
            ]
            logger.log_result(
                "获取车型成功", f"品牌{make_name}共{len(models)}个车型"
            )
            return models

        except Exception as e:
            logger.log_result(f"获取品牌车型失败: {str(e)}")
            return []

    async def search_car_models(
        self, make_name: str = None, model_name: str = None
    ) -> List[Dict[str, str]]:
        """
        搜索汽车型号

        Args:
            make_name: 品牌名称（可选）
            model_name: 车型名称（可选）

        Returns:
            匹配的汽车型号列表
        """
        try:
            logger.log_result(
                "搜索汽车型号", f"品牌: {make_name}, 车型: {model_name}"
            )

            db_util = await get_db_util()

            # 构建动态查询
            conditions = []
            params = {}
            param_count = 1

            if make_name:
                conditions.append(f"make ILIKE ${param_count}")
                params[f"param_{param_count}"] = f"%{make_name}%"
                param_count += 1

            if model_name:
                conditions.append(f"model ILIKE ${param_count}")
                params[f"param_{param_count}"] = f"%{model_name}%"
                param_count += 1

            where_clause = " AND ".join(conditions) if conditions else "1=1"

            query = f"""
                SELECT make, make_code, model, model_code 
                FROM car_models 
                WHERE {where_clause}
                ORDER BY make, model
                LIMIT 100
            """

            result = await db_util.execute_sql(query, params)

            models = [
                {
                    "make": row["make"],
                    "make_code": row["make_code"],
                    "model": row["model"],
                    "model_code": row["model_code"],
                }
                for row in result
            ]

            logger.log_result("搜索完成", f"找到{len(models)}个匹配结果")
            return models

        except Exception as e:
            logger.log_result(f"搜索汽车型号失败: {str(e)}")
            return []

    @lru_cache(maxsize=128)
    def get_fuel_type_mapping(self) -> Dict[str, str]:
        """
        获取燃料类型映射

        Returns:
            燃料类型映射字典
        """
        try:
            logger.log_result("获取燃料类型映射", "使用静态映射数据")

            # 静态燃料类型映射数据
            fuel_type_mapping = {
                "Gasoline": "gasoline",
                "Diesel": "diesel",
                "Hybrid": "hybrid",
                "Electric": "electric",
                "Plug-in Hybrid": "plug-in-hybrid",
                "Natural Gas": "natural-gas",
                "Propane": "propane",
                "Ethanol": "ethanol",
                "Biodiesel": "biodiesel",
                "Hydrogen": "hydrogen",
            }

            return fuel_type_mapping

        except Exception as e:
            logger.log_result(f"获取燃料类型映射失败: {str(e)}")
            return {}

    @lru_cache(maxsize=128)
    def get_transmission_mapping(self) -> Dict[str, str]:
        """
        获取变速箱类型映射

        Returns:
            变速箱类型映射字典
        """
        try:
            logger.log_result("获取变速箱类型映射", "使用静态映射数据")

            # 静态变速箱类型映射数据
            transmission_mapping = {
                "Automatic": "automatic",
                "Manual": "manual",
                "CVT": "cvt",
                "Semi-Automatic": "semi-automatic",
                "Dual Clutch": "dual-clutch",
                "Sequential": "sequential",
                "Automated Manual": "automated-manual",
                "Torque Converter": "torque-converter",
                "Planetary": "planetary",
                "Continuously Variable": "continuously-variable",
            }

            return transmission_mapping

        except Exception as e:
            logger.log_result(f"获取变速箱类型映射失败: {str(e)}")
            return {}

    @lru_cache(maxsize=128)
    def get_body_style_mapping(self) -> Dict[str, str]:
        """
        获取车身类型映射

        Returns:
            车身类型映射字典
        """
        try:
            logger.log_result("获取车身类型映射", "使用静态映射数据")

            # 静态车身类型映射数据
            body_style_mapping = {
                "Sedan": "sedan",
                "SUV": "suv",
                "Hatchback": "hatchback",
                "Coupe": "coupe",
                "Convertible": "convertible",
                "Wagon": "wagon",
                "Truck": "truck",
                "Van": "van",
                "Crossover": "crossover",
                "Pickup": "pickup",
                "Minivan": "minivan",
                "Roadster": "roadster",
                "Limo": "limo",
                "Bus": "bus",
                "Motorcycle": "motorcycle",
                "Scooter": "scooter",
                "ATV": "atv",
                "UTV": "utv",
                "Snowmobile": "snowmobile",
                "Boat": "boat",
                "Jet Ski": "jet-ski",
                "RV": "rv",
                "Trailer": "trailer",
                "Camper": "camper",
                "Motorhome": "motorhome",
                "Truck Camper": "truck-camper",
                "Fifth Wheel": "fifth-wheel",
                "Travel Trailer": "travel-trailer",
                "Toy Hauler": "toy-hauler",
                "Pop-up": "pop-up",
                "Teardrop": "teardrop",
                "Airstream": "airstream",
                "Class A": "class-a",
                "Class B": "class-b",
                "Class C": "class-c",
            }

            return body_style_mapping

        except Exception as e:
            logger.log_result(f"获取车身类型映射失败: {str(e)}")
            return {}

    def clear_cache(self):
        """清除所有缓存"""
        try:
            # 注意：get_city_zip_codes, get_make_code, get_model_code 现在是异步方法，没有缓存
            self.get_fuel_type_mapping.cache_clear()
            self.get_transmission_mapping.cache_clear()
            self.get_body_style_mapping.cache_clear()
            logger.log_result("缓存清除", "静态映射缓存已清除")
        except Exception as e:
            logger.log_result(f"清除缓存失败: {str(e)}")

    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        try:
            return {
                "city_zip_codes": "异步方法，无缓存",
                "make_code": "异步方法，无缓存",
                "model_code": "异步方法，无缓存",
                "get_all_makes": "异步方法，无缓存",
                "get_models_by_make": "异步方法，无缓存",
                "search_car_models": "异步方法，无缓存",
                "fuel_type_mapping": self.get_fuel_type_mapping.cache_info(),
                "transmission_mapping": self.get_transmission_mapping.cache_info(),
                "body_style_mapping": self.get_body_style_mapping.cache_info(),
            }
        except Exception as e:
            logger.log_result(f"获取缓存信息失败: {str(e)}")
            return {}
