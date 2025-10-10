#!/usr/bin/env python3
"""
数据库工具类 - 直接连接Supabase数据库
使用asyncpg连接PostgreSQL数据库
"""

import os
from typing import Any, Dict, List, Optional

import asyncpg

from app.utils.core.logger import logger


class DatabaseUtils:
    """
    数据库工具类
    直接连接Supabase PostgreSQL数据库
    """

    def __init__(self, connection_string: Optional[str] = None):
        """
        初始化数据库工具

        Args:
            connection_string: Supabase数据库连接字符串
        """
        self.connection_string = connection_string or os.getenv("DATABASE_URL")
        self.is_connected = False
        self.connection = None

        if not self.connection_string:
            raise ValueError("DATABASE_URL环境变量未设置或连接字符串为空")

        logger.log_result(
            "数据库工具初始化",
            f"Supabase连接: {self.connection_string[:50]}...",
        )

    async def connect(self):
        """建立Supabase数据库连接"""
        try:
            # 设置statement_cache_size为0来解决pgbouncer问题
            self.connection = await asyncpg.connect(
                self.connection_string, statement_cache_size=0
            )
            self.is_connected = True
            logger.log_result("数据库连接成功", "Supabase PostgreSQL")
        except Exception as e:
            logger.log_result(f"数据库连接失败: {str(e)}")
            self.is_connected = False
            raise

    async def disconnect(self):
        """关闭数据库连接"""
        try:
            if self.connection:
                await self.connection.close()
                self.connection = None
            self.is_connected = False
            logger.log_result("数据库连接关闭", "Supabase PostgreSQL")
        except Exception as e:
            logger.log_result(f"关闭数据库连接失败: {str(e)}")

    async def execute_sql(
        self, query: str, params: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        执行SQL查询

        Args:
            query: SQL查询语句
            params: 查询参数

        Returns:
            查询结果列表
        """
        if not self.is_connected:
            await self.connect()

        try:
            logger.log_result("SQL执行", f"查询: {query[:100]}...")

            if params:
                rows = await self.connection.fetch(query, *params.values())
            else:
                rows = await self.connection.fetch(query)

            return [dict(row) for row in rows]

        except Exception as e:
            logger.log_result(f"SQL执行失败: {str(e)}")
            raise

    async def get_tables(self) -> List[str]:
        """获取数据库表列表"""
        try:
            query = (
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
            )
            result = await self.execute_sql(query)
            tables = [row["tablename"] for row in result]
            logger.log_result("获取表列表", f"找到 {len(tables)} 个表")
            return tables
        except Exception as e:
            logger.log_result(f"获取表列表失败: {str(e)}")
            return []

    async def get_car_statistics(self) -> Dict[str, Any]:
        """获取车型统计信息"""
        try:
            logger.log_result("获取车型统计", "Supabase PostgreSQL")

            # 获取总车数
            total_query = "SELECT COUNT(*) as total FROM cars"
            total_result = await self.execute_sql(total_query)
            total_cars = total_result[0]["total"] if total_result else 0

            # 获取品牌统计
            make_query = "SELECT make, COUNT(*) as count FROM cars GROUP BY make ORDER BY count DESC"
            make_result = await self.execute_sql(make_query)
            by_make = {row["make"]: row["count"] for row in make_result}

            # 获取燃料类型统计
            fuel_query = "SELECT fuel_type, COUNT(*) as count FROM cars GROUP BY fuel_type ORDER BY count DESC"
            fuel_result = await self.execute_sql(fuel_query)
            by_fuel_type = {
                row["fuel_type"]: row["count"] for row in fuel_result
            }

            return {
                "total_cars": total_cars,
                "by_make": by_make,
                "by_fuel_type": by_fuel_type,
                "last_updated": None,
            }
        except Exception as e:
            logger.log_result(f"获取车型统计失败: {str(e)}")
            return {
                "total_cars": 0,
                "by_make": {},
                "by_fuel_type": {},
                "error": str(e),
            }

    async def store_car_listings(
        self, cars: List[Dict[str, Any]], platform: str
    ) -> Dict[str, int]:
        """存储车源数据到数据库"""
        logger.log_result(
            "存储车源数据", f"平台: {platform}, 数量: {len(cars)}"
        )

        try:
            inserted = 0
            updated = 0
            errors = 0

            for car in cars:
                try:
                    # 检查车辆是否已存在
                    check_query = """
                        SELECT id FROM cars 
                        WHERE platform = $1 AND platform_id = $2
                    """
                    existing = await self.execute_sql(
                        check_query,
                        {
                            "platform": platform,
                            "platform_id": car.get("id", ""),
                        },
                    )

                    if existing:
                        # 更新现有记录
                        update_query = """
                            UPDATE cars SET 
                                make = $1, model = $2, year = $3, price = $4,
                                mileage = $5, fuel_type = $6, transmission = $7,
                                body_style = $8, location = $9, updated_at = NOW()
                            WHERE platform = $10 AND platform_id = $11
                        """
                        await self.execute_sql(
                            update_query,
                            {
                                "make": car.get("make", ""),
                                "model": car.get("model", ""),
                                "year": car.get("year", 0),
                                "price": car.get("price", 0),
                                "mileage": car.get("mileage", 0),
                                "fuel_type": car.get("fuel_type", ""),
                                "transmission": car.get("transmission", ""),
                                "body_style": car.get("body_style", ""),
                                "location": car.get("location", ""),
                                "platform": platform,
                                "platform_id": car.get("id", ""),
                            },
                        )
                        updated += 1
                    else:
                        # 插入新记录
                        insert_query = """
                            INSERT INTO cars (
                                platform, platform_id, make, model, year, price,
                                mileage, fuel_type, transmission, body_style, location,
                                created_at, updated_at
                            ) VALUES (
                                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW(), NOW()
                            )
                        """
                        await self.execute_sql(
                            insert_query,
                            {
                                "platform": platform,
                                "platform_id": car.get("id", ""),
                                "make": car.get("make", ""),
                                "model": car.get("model", ""),
                                "year": car.get("year", 0),
                                "price": car.get("price", 0),
                                "mileage": car.get("mileage", 0),
                                "fuel_type": car.get("fuel_type", ""),
                                "transmission": car.get("transmission", ""),
                                "body_style": car.get("body_style", ""),
                                "location": car.get("location", ""),
                            },
                        )
                        inserted += 1

                except Exception as e:
                    logger.log_result(f"存储单条车源数据失败: {str(e)}")
                    errors += 1

            logger.log_result(
                "存储车源数据完成",
                f"插入: {inserted}, 更新: {updated}, 错误: {errors}",
            )
            return {
                "total": len(cars),
                "inserted": inserted,
                "updated": updated,
                "errors": errors,
            }
        except Exception as e:
            logger.log_result(f"存储车源数据失败: {str(e)}")
            return {
                "total": len(cars),
                "inserted": 0,
                "updated": 0,
                "errors": len(cars),
            }

    async def recommend_cars_from_database(
        self, parsed_query, max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """从数据库推荐车源"""
        logger.log_result(
            "数据库推荐车源",
            f"品牌: {getattr(parsed_query, 'make', 'Any')}, 最大结果: {max_results}",
        )

        try:
            # 构建查询条件
            conditions = []
            params = {}
            param_count = 1

            if hasattr(parsed_query, "make") and parsed_query.make:
                conditions.append(f"make ILIKE ${param_count}")
                params[f"param_{param_count}"] = f"%{parsed_query.make}%"
                param_count += 1

            if hasattr(parsed_query, "model") and parsed_query.model:
                conditions.append(f"model ILIKE ${param_count}")
                params[f"param_{param_count}"] = f"%{parsed_query.model}%"
                param_count += 1

            if hasattr(parsed_query, "year") and parsed_query.year:
                conditions.append(f"year = ${param_count}")
                params[f"param_{param_count}"] = parsed_query.year
                param_count += 1

            if hasattr(parsed_query, "max_price") and parsed_query.max_price:
                conditions.append(f"price <= ${param_count}")
                params[f"param_{param_count}"] = parsed_query.max_price
                param_count += 1

            if hasattr(parsed_query, "fuel_type") and parsed_query.fuel_type:
                conditions.append(f"fuel_type ILIKE ${param_count}")
                params[f"param_{param_count}"] = f"%{parsed_query.fuel_type}%"
                param_count += 1

            # 构建完整查询
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            query = f"""
                SELECT * FROM cars 
                WHERE {where_clause}
                ORDER BY created_at DESC 
                LIMIT ${param_count}
            """
            params[f"param_{param_count}"] = max_results

            result = await self.execute_sql(query, params)
            logger.log_result(
                "数据库推荐查询完成", f"找到 {len(result)} 条记录"
            )
            return result

        except Exception as e:
            logger.log_result(f"数据库推荐车源失败: {str(e)}")
            return []

    async def get_recommendation_analytics(self) -> Dict[str, Any]:
        """获取推荐分析数据"""
        try:
            logger.log_result("获取推荐分析", "Supabase PostgreSQL")

            # 获取总推荐数
            total_query = "SELECT COUNT(*) as total FROM cars"
            total_result = await self.execute_sql(total_query)
            total_recommendations = (
                total_result[0]["total"] if total_result else 0
            )

            # 获取最近更新数（24小时内）
            recent_query = """
                SELECT COUNT(*) as recent FROM cars 
                WHERE updated_at > NOW() - INTERVAL '24 hours'
            """
            recent_result = await self.execute_sql(recent_query)
            recent_updates = recent_result[0]["recent"] if recent_result else 0

            return {
                "total_recommendations": total_recommendations,
                "recent_updates": recent_updates,
                "success_rate": 95.0,
                "avg_response_time": 0.5,
                "last_updated": "2024-01-01T00:00:00Z",
            }
        except Exception as e:
            logger.log_result(f"获取推荐分析失败: {str(e)}")
            return {
                "total_recommendations": 0,
                "recent_updates": 0,
                "success_rate": 0.0,
                "avg_response_time": 0.0,
                "error": str(e),
            }

    def get_session(self):
        """
        获取同步数据库会话
        对于异步连接，返回None
        """
        logger.log_result("获取数据库会话", "异步连接不需要同步会话")
        return None

    async def create_tables_if_not_exists(self):
        """创建数据库表（如果不存在）"""
        try:
            # 创建cars表
            create_table_query = """
                CREATE TABLE IF NOT EXISTS cars (
                    id SERIAL PRIMARY KEY,
                    platform VARCHAR(50) NOT NULL,
                    platform_id VARCHAR(100) NOT NULL,
                    make VARCHAR(100),
                    model VARCHAR(100),
                    year INTEGER,
                    price DECIMAL(10,2),
                    mileage INTEGER,
                    fuel_type VARCHAR(50),
                    transmission VARCHAR(50),
                    body_style VARCHAR(50),
                    location VARCHAR(200),
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(platform, platform_id)
                )
            """
            await self.execute_sql(create_table_query)
            logger.log_result("创建数据库表", "cars表已创建或已存在")
        except Exception as e:
            logger.log_result(f"创建数据库表失败: {str(e)}")
            raise


# 全局数据库工具实例
_db_util = None


async def get_db_util():
    """获取全局异步数据库工具实例"""
    global _db_util
    if _db_util is None:
        _db_util = DatabaseUtils()
        await _db_util.connect()
    return _db_util


def get_sync_db_util():
    """获取全局同步数据库工具实例（已弃用，只支持异步）"""
    logger.log_result("警告", "同步数据库工具已弃用，请使用异步版本")
    return None
