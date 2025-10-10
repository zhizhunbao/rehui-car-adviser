#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
汽车数据查询服务
提供汽车品牌和型号的查询功能
"""

from typing import List, Dict, Optional
from app.utils.data.db_utils import get_db_util
from app.utils.core.logger import logger


class CarDataService:
    """汽车数据查询服务"""
    
    def __init__(self):
        self.db_util = None
    
    async def _ensure_db_util(self):
        """确保数据库工具已初始化"""
        if self.db_util is None:
            self.db_util = await get_db_util()
    
    async def get_all_makes(self) -> List[Dict[str, str]]:
        """获取所有汽车品牌"""
        try:
            await self._ensure_db_util()
            query = "SELECT id, make, make_code FROM car_makes ORDER BY make"
            result = await self.db_util.execute_sql(query)
            
            logger.log_result(f"获取汽车品牌列表", f"共{len(result)}个品牌")
            return result
            
        except Exception as e:
            logger.log_result("获取汽车品牌失败", str(e))
            return []
    
    async def get_models_by_make(self, make: str) -> List[Dict[str, str]]:
        """根据品牌获取型号列表"""
        try:
            await self._ensure_db_util()
            query = """
            SELECT id, make, make_code, model, model_code 
            FROM car_models 
            WHERE make = :make 
            ORDER BY model
            """
            result = await self.db_util.execute_sql(query, {"make": make})
            
            logger.log_result(f"获取{make}品牌型号列表", f"共{len(result)}个型号")
            return result
            
        except Exception as e:
            logger.log_result(f"获取{make}品牌型号失败", str(e))
            return []
    
    async def search_makes(self, keyword: str) -> List[Dict[str, str]]:
        """搜索汽车品牌"""
        try:
            await self._ensure_db_util()
            query = """
            SELECT id, make, make_code 
            FROM car_makes 
            WHERE make ILIKE :keyword 
            ORDER BY make
            """
            result = await self.db_util.execute_sql(query, {"keyword": f"%{keyword}%"})
            
            logger.log_result(f"搜索品牌: {keyword}", f"找到{len(result)}个匹配结果")
            return result
            
        except Exception as e:
            logger.log_result(f"搜索品牌失败: {keyword}", str(e))
            return []
    
    async def search_models(self, make: str, keyword: str) -> List[Dict[str, str]]:
        """搜索汽车型号"""
        try:
            await self._ensure_db_util()
            query = """
            SELECT id, make, make_code, model, model_code 
            FROM car_models 
            WHERE make = :make AND model ILIKE :keyword 
            ORDER BY model
            """
            result = await self.db_util.execute_sql(query, {
                "make": make,
                "keyword": f"%{keyword}%"
            })
            
            logger.log_result(f"搜索{make}品牌型号: {keyword}", f"找到{len(result)}个匹配结果")
            return result
            
        except Exception as e:
            logger.log_result(f"搜索型号失败: {make} {keyword}", str(e))
            return []
    
    async def get_make_by_code(self, make_code: str) -> Optional[Dict[str, str]]:
        """根据品牌代码获取品牌信息"""
        try:
            await self._ensure_db_util()
            query = "SELECT id, make, make_code FROM car_makes WHERE make_code = :make_code"
            result = await self.db_util.execute_sql(query, {"make_code": make_code})
            
            if result:
                logger.log_result(f"根据代码获取品牌: {make_code}", result[0]['make'])
                return result[0]
            else:
                logger.log_result(f"未找到品牌代码: {make_code}")
                return None
                
        except Exception as e:
            logger.log_result(f"根据代码获取品牌失败: {make_code}", str(e))
            return None
    
    async def get_model_by_codes(self, make_code: str, model_code: str) -> Optional[Dict[str, str]]:
        """根据品牌代码和型号代码获取型号信息"""
        try:
            await self._ensure_db_util()
            query = """
            SELECT id, make, make_code, model, model_code 
            FROM car_models 
            WHERE make_code = :make_code AND model_code = :model_code
            """
            result = await self.db_util.execute_sql(query, {
                "make_code": make_code,
                "model_code": model_code
            })
            
            if result:
                model_info = result[0]
                logger.log_result(f"根据代码获取型号: {make_code}/{model_code}", f"{model_info['make']} {model_info['model']}")
                return model_info
            else:
                logger.log_result(f"未找到型号代码: {make_code}/{model_code}")
                return None
                
        except Exception as e:
            logger.log_result(f"根据代码获取型号失败: {make_code}/{model_code}", str(e))
            return None
    
    async def validate_make_model(self, make: str, model: str) -> Dict[str, any]:
        """验证品牌和型号是否存在"""
        try:
            await self._ensure_db_util()
            # 检查品牌是否存在
            make_query = "SELECT id, make, make_code FROM car_makes WHERE make = :make"
            make_result = await self.db_util.execute_sql(make_query, {"make": make})
            
            if not make_result:
                return {
                    "valid": False,
                    "error": f"品牌 '{make}' 不存在",
                    "suggestions": await self._get_similar_makes(make)
                }
            
            make_info = make_result[0]
            
            # 检查型号是否存在
            model_query = """
            SELECT id, make, make_code, model, model_code 
            FROM car_models 
            WHERE make = :make AND model = :model
            """
            model_result = await self.db_util.execute_sql(model_query, {
                "make": make,
                "model": model
            })
            
            if not model_result:
                # 获取该品牌的所有型号作为建议
                all_models = await self.get_models_by_make(make)
                return {
                    "valid": False,
                    "error": f"型号 '{model}' 在品牌 '{make}' 中不存在",
                    "make_info": make_info,
                    "suggestions": [m['model'] for m in all_models[:10]]  # 只返回前10个建议
                }
            
            model_info = model_result[0]
            
            return {
                "valid": True,
                "make_info": make_info,
                "model_info": model_info
            }
            
        except Exception as e:
            logger.log_result(f"验证品牌型号失败: {make} {model}", str(e))
            return {
                "valid": False,
                "error": f"验证失败: {str(e)}"
            }
    
    async def _get_similar_makes(self, make: str) -> List[str]:
        """获取相似的品牌名称"""
        try:
            await self._ensure_db_util()
            query = """
            SELECT make 
            FROM car_makes 
            WHERE make ILIKE :pattern 
            ORDER BY make 
            LIMIT 5
            """
            result = await self.db_util.execute_sql(query, {"pattern": f"%{make}%"})
            return [row['make'] for row in result]
            
        except Exception as e:
            logger.log_result(f"获取相似品牌失败: {make}", str(e))
            return []
    
    async def get_statistics(self) -> Dict[str, any]:
        """获取汽车数据统计信息"""
        try:
            await self._ensure_db_util()
            # 品牌数量
            makes_count = await self.db_util.execute_sql("SELECT COUNT(*) as count FROM car_makes")
            makes_total = makes_count[0]['count'] if makes_count else 0
            
            # 型号数量
            models_count = await self.db_util.execute_sql("SELECT COUNT(*) as count FROM car_models")
            models_total = models_count[0]['count'] if models_count else 0
            
            # 各品牌型号数量
            models_by_make = await self.db_util.execute_sql("""
                SELECT make, COUNT(*) as model_count 
                FROM car_models 
                GROUP BY make 
                ORDER BY model_count DESC 
                LIMIT 10
            """)
            
            logger.log_result("获取汽车数据统计", f"品牌: {makes_total}, 型号: {models_total}")
            
            return {
                "makes_count": makes_total,
                "models_count": models_total,
                "top_makes": models_by_make
            }
            
        except Exception as e:
            logger.log_result("获取汽车数据统计失败", str(e))
            return {
                "makes_count": 0,
                "models_count": 0,
                "top_makes": [],
                "error": str(e)
            }


# 全局实例
car_data_service = CarDataService()
