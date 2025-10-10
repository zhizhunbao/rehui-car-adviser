"""
Supabase 配置数据工具 - 管理爬虫相关的配置数据

直接从 Supabase 数据库读取配置数据，替代原来的 CSV 文件方式。
提供城市映射、品牌映射等配置数据的统一管理。
"""

from functools import lru_cache
from typing import Dict, List

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.utils.core.config import Config


class SupabaseConfigUtils:
    """Supabase 配置工具类"""

    def __init__(self, database_url: str = None):
        if database_url is None:
            database_url = Config.DATABASE_URL

        self.database_url = database_url
        self.engine = create_engine(
            database_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def close(self):
        """关闭数据库连接"""
        self.engine.dispose()

    @lru_cache(maxsize=128)
    def get_city_zip_codes(self, city_name: str) -> List[str]:
        """根据城市名称获取ZIP代码列表"""
        if not city_name or not isinstance(city_name, str):
            return []

        with self.engine.connect() as conn:
            try:
                result = conn.execute(
                    text(
                        """
                    SELECT czc.zip_code 
                    FROM cities c
                    JOIN city_zip_codes czc ON c.id = czc.city_id
                    WHERE LOWER(c.name) = LOWER(:city_name)
                    ORDER BY czc.is_primary DESC, czc.zip_code
                """
                    ),
                    {"city_name": city_name},
                )

                return [row[0] for row in result.fetchall()]
            except Exception as e:
                print(f"Error getting city zip codes: {e}")
                return []

    @lru_cache(maxsize=128)
    def get_make_code(self, make_name: str) -> str:
        """根据品牌名称获取品牌代码"""
        if not make_name or not isinstance(make_name, str):
            return ""

        with self.engine.connect() as conn:
            try:
                # 首先尝试直接查找
                result = conn.execute(
                    text(
                        """
                    SELECT make_code FROM car_makes 
                    WHERE LOWER(make) = LOWER(:make_name)
                """
                    ),
                    {"make_name": make_name},
                )

                row = result.fetchone()
                if row:
                    return row[0]

                # 如果没找到，尝试中文到英文的映射
                result = conn.execute(
                    text(
                        """
                    SELECT cm.make_code 
                    FROM name_mappings nm
                    JOIN car_makes cm ON LOWER(cm.make) = LOWER(nm.english_name)
                    WHERE nm.type = 'make' AND LOWER(nm.chinese_name) = LOWER(:make_name)
                """
                    ),
                    {"make_name": make_name},
                )

                row = result.fetchone()
                if row:
                    return row[0]

                return ""
            except Exception as e:
                print(f"Error getting make code: {e}")
                return ""

    @lru_cache(maxsize=128)
    def get_model_code(self, make_name: str, model_name: str) -> str:
        """根据品牌名称和型号名称获取型号代码"""
        if (
            not make_name
            or not model_name
            or not isinstance(make_name, str)
            or not isinstance(model_name, str)
        ):
            return ""

        with self.engine.connect() as conn:
            try:
                # 首先尝试直接查找
                result = conn.execute(
                    text(
                        """
                    SELECT model_code FROM car_models 
                    WHERE LOWER(make) = LOWER(:make_name) 
                    AND LOWER(model) = LOWER(:model_name)
                """
                    ),
                    {"make_name": make_name, "model_name": model_name},
                )

                row = result.fetchone()
                if row:
                    return row[0]

                # 如果没找到，尝试中文到英文的映射
                result = conn.execute(
                    text(
                        """
                    SELECT cm.model_code 
                    FROM name_mappings nm_make
                    JOIN name_mappings nm_model ON nm_make.type = 'make' AND nm_model.type = 'model'
                    JOIN car_models cm ON LOWER(cm.make) = LOWER(nm_make.english_name)
                    WHERE LOWER(nm_make.chinese_name) = LOWER(:make_name)
                    AND LOWER(nm_model.chinese_name) = LOWER(:model_name)
                    AND LOWER(cm.model) = LOWER(nm_model.english_name)
                """
                    ),
                    {"make_name": make_name, "model_name": model_name},
                )

                row = result.fetchone()
                if row:
                    return row[0]

                return ""
            except Exception as e:
                print(f"Error getting model code: {e}")
                return ""

    def get_all_cities(self) -> List[str]:
        """获取所有支持的城市列表"""
        with self.engine.connect() as conn:
            try:
                result = conn.execute(
                    text(
                        """
                    SELECT name FROM cities 
                    WHERE is_major = true 
                    ORDER BY name
                """
                    )
                )
                return [row[0] for row in result.fetchall()]
            except Exception as e:
                print(f"Error getting all cities: {e}")
                return []

    def get_all_makes(self) -> List[str]:
        """获取所有支持的品牌列表"""
        with self.engine.connect() as conn:
            try:
                result = conn.execute(
                    text(
                        """
                    SELECT make FROM car_makes 
                    ORDER BY make
                """
                    )
                )
                return [row[0] for row in result.fetchall()]
            except Exception as e:
                print(f"Error getting all makes: {e}")
                return []

    def get_all_models_for_make(self, make_name: str) -> List[str]:
        """获取指定品牌的所有型号列表"""
        if not make_name or not isinstance(make_name, str):
            return []

        with self.engine.connect() as conn:
            try:
                result = conn.execute(
                    text(
                        """
                    SELECT model FROM car_models 
                    WHERE LOWER(make) = LOWER(:make_name)
                    ORDER BY model
                """
                    ),
                    {"make_name": make_name},
                )
                return [row[0] for row in result.fetchall()]
            except Exception as e:
                print(f"Error getting models for make: {e}")
                return []

    def validate_city_name(self, city_name: str) -> bool:
        """验证城市名称是否有效"""
        if not city_name or not isinstance(city_name, str):
            return False

        with self.engine.connect() as conn:
            try:
                result = conn.execute(
                    text(
                        """
                    SELECT COUNT(*) FROM cities 
                    WHERE LOWER(name) = LOWER(:city_name)
                """
                    ),
                    {"city_name": city_name},
                )
                return result.fetchone()[0] > 0
            except Exception as e:
                print(f"Error validating city name: {e}")
                return False

    def validate_make_name(self, make_name: str) -> bool:
        """验证品牌名称是否有效"""
        if not make_name or not isinstance(make_name, str):
            return False

        with self.engine.connect() as conn:
            try:
                # 检查英文名称
                result = conn.execute(
                    text(
                        """
                    SELECT COUNT(*) FROM car_makes 
                    WHERE LOWER(make) = LOWER(:make_name)
                """
                    ),
                    {"make_name": make_name},
                )
                if result.fetchone()[0] > 0:
                    return True

                # 检查中文名称映射
                result = conn.execute(
                    text(
                        """
                    SELECT COUNT(*) FROM name_mappings 
                    WHERE type = 'make' AND LOWER(chinese_name) = LOWER(:make_name)
                """
                    ),
                    {"make_name": make_name},
                )
                return result.fetchone()[0] > 0
            except Exception as e:
                print(f"Error validating make name: {e}")
                return False

    def validate_model_name(self, make_name: str, model_name: str) -> bool:
        """验证型号名称是否有效"""
        if (
            not make_name
            or not model_name
            or not isinstance(make_name, str)
            or not isinstance(model_name, str)
        ):
            return False

        with self.engine.connect() as conn:
            try:
                # 检查英文名称
                result = conn.execute(
                    text(
                        """
                    SELECT COUNT(*) FROM car_models 
                    WHERE LOWER(make) = LOWER(:make_name) 
                    AND LOWER(model) = LOWER(:model_name)
                """
                    ),
                    {"make_name": make_name, "model_name": model_name},
                )
                if result.fetchone()[0] > 0:
                    return True

                # 检查中文名称映射
                result = conn.execute(
                    text(
                        """
                    SELECT COUNT(*) FROM name_mappings nm_make
                    JOIN name_mappings nm_model ON nm_make.type = 'make' AND nm_model.type = 'model'
                    JOIN car_models cm ON LOWER(cm.make) = LOWER(nm_make.english_name)
                    WHERE LOWER(nm_make.chinese_name) = LOWER(:make_name)
                    AND LOWER(nm_model.chinese_name) = LOWER(:model_name)
                    AND LOWER(cm.model) = LOWER(nm_model.english_name)
                """
                    ),
                    {"make_name": make_name, "model_name": model_name},
                )
                return result.fetchone()[0] > 0
            except Exception as e:
                print(f"Error validating model name: {e}")
                return False

    def get_all_makes_with_models(self) -> List[str]:
        """获取所有有型号数据的品牌列表"""
        with self.engine.connect() as conn:
            try:
                result = conn.execute(
                    text(
                        """
                    SELECT DISTINCT make FROM car_models 
                    ORDER BY make
                """
                    )
                )
                return [row[0] for row in result.fetchall()]
            except Exception as e:
                print(f"Error getting makes with models: {e}")
                return []


# 距离选项和年份范围（保持与原来一致）
DISTANCE_OPTIONS = [10, 25, 50, 100, 200, 500]
YEAR_RANGE = {"min": 1990, "max": 2025}


def get_distance_options() -> List[int]:
    """获取可用的距离选项"""
    return DISTANCE_OPTIONS.copy()


def get_year_range() -> Dict[str, int]:
    """获取年份范围"""
    return YEAR_RANGE.copy()
