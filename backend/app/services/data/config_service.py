#!/usr/bin/env python3
"""
重构后的配置服务 - 使用 DAO 层
"""

from typing import List, Dict, Optional
from app.dao.config_dao import ConfigDAO
from app.utils.core.logger import get_logger

logger = get_logger(__name__)


class ConfigServiceRefactored:
    """
    重构后的配置服务 - 使用 DAO 层
    提供配置数据的统一访问接口
    """
    
    def __init__(self):
        self.config_dao = ConfigDAO()
    
    def get_city_zip_codes(self, city_name: str) -> List[str]:
        """
        根据城市名称获取ZIP代码列表
        
        Args:
            city_name: 城市名称
            
        Returns:
            ZIP代码列表
        """
        return self.config_dao.get_city_zip_codes(city_name)
    
    def get_make_code(self, make_name: str) -> str:
        """
        根据品牌名称获取品牌代码
        
        Args:
            make_name: 品牌名称
            
        Returns:
            品牌代码
        """
        return self.config_dao.get_make_code(make_name)
    
    def get_model_code(self, make_name: str, model_name: str) -> str:
        """
        根据品牌和型号名称获取型号代码
        
        Args:
            make_name: 品牌名称
            model_name: 型号名称
            
        Returns:
            型号代码
        """
        return self.config_dao.get_model_code(make_name, model_name)
    
    def get_all_makes(self) -> List[Dict[str, str]]:
        """
        获取所有汽车品牌
        
        Returns:
            品牌列表
        """
        return self.config_dao.get_all_makes()
    
    def get_models_by_make(self, make_name: str) -> List[Dict[str, str]]:
        """
        根据品牌获取型号列表
        
        Args:
            make_name: 品牌名称
            
        Returns:
            型号列表
        """
        return self.config_dao.get_models_by_make(make_name)
    
    def search_makes(self, keyword: str) -> List[Dict[str, str]]:
        """
        搜索品牌
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            匹配的品牌列表
        """
        return self.config_dao.search_makes(keyword)
    
    def search_models(self, make_name: str, keyword: str) -> List[Dict[str, str]]:
        """
        搜索型号
        
        Args:
            make_name: 品牌名称
            keyword: 搜索关键词
            
        Returns:
            匹配的型号列表
        """
        return self.config_dao.search_models(make_name, keyword)
    
    def get_zip_codes_by_province(self, province: str) -> List[str]:
        """
        根据省份获取所有ZIP代码
        
        Args:
            province: 省份名称
            
        Returns:
            ZIP代码列表
        """
        return self.config_dao.get_zip_codes_by_province(province)
    
    def get_cities_by_province(self, province: str) -> List[Dict[str, str]]:
        """
        根据省份获取城市列表
        
        Args:
            province: 省份名称
            
        Returns:
            城市列表
        """
        return self.config_dao.get_cities_by_province(province)
    
    def get_provinces(self) -> List[str]:
        """
        获取所有省份列表
        
        Returns:
            省份列表
        """
        return self.config_dao.get_provinces()
    
    def clear_cache(self):
        """清除配置数据缓存"""
        self.config_dao.clear_cache()
        logger.info("配置服务缓存已清除")
    
    def get_statistics(self) -> Dict[str, int]:
        """获取配置数据统计信息"""
        return self.config_dao.get_config_statistics()
    
    def validate_data(self) -> Dict[str, List[str]]:
        """
        验证配置数据的完整性
        
        Returns:
            验证结果，包含错误信息
        """
        return self.config_dao.validate_config_data()
