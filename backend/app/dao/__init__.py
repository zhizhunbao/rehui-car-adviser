"""
DAO (Data Access Object) 层
提供统一的数据访问接口，分离业务逻辑和数据访问逻辑
"""

from .base_dao import BaseDAO
from .car_dao import CarDAO, CarSearchHistoryDAO, CarRecommendationLogDAO
from .config_dao import ConfigDAO

__all__ = [
    'BaseDAO', 
    'CarDAO', 
    'CarSearchHistoryDAO', 
    'CarRecommendationLogDAO',
    'ConfigDAO'
]
