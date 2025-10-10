"""
URL构建服务 - 负责构建各种汽车网站的URL

这个服务层负责协调DAO层获取配置数据，然后调用工具层构建URL。
遵循正确的架构层次：Service -> DAO -> Utils
"""

from typing import Optional
from app.dao.config_dao import ConfigDAO
from app.utils.web.url_builder_utils import (
    build_cargurus_search_url as _build_cargurus_search_url,
    build_cargurus_brand_url as _build_cargurus_brand_url,
    build_cargurus_model_url as _build_cargurus_model_url,
    build_cargurus_listing_url,
    extract_listing_id_from_url,
    is_valid_cargurus_url
)


class URLBuilderService:
    """URL构建服务类"""
    
    def __init__(self):
        self.config_dao = ConfigDAO()
    
    async def build_cargurus_search_url(
        self,
        make: str, model: str, zip_code: str, distance: int,
        year_min: Optional[int] = None, year_max: Optional[int] = None,
        price_min: Optional[int] = None, price_max: Optional[int] = None,
        mileage_max: Optional[int] = None
    ) -> str:
        """
        构建CarGurus搜索URL
        
        服务层负责：
        1. 从DAO层获取配置数据
        2. 调用工具层构建URL
        3. 处理业务逻辑
        """
        # 从DAO层获取品牌和车型代码
        make_code = await self.config_dao.get_make_code(make)
        model_code = await self.config_dao.get_model_code(make, model)
        
        # 调用工具层构建URL，传入已获取的代码
        return _build_cargurus_search_url(
            make=make, model=model, zip_code=zip_code, distance=distance,
            year_min=year_min, year_max=year_max,
            price_min=price_min, price_max=price_max,
            mileage_max=mileage_max,
            make_code=make_code, model_code=model_code
        )
    
    async def build_cargurus_brand_url(
        self, make: str, zip_code: str, distance: int
    ) -> str:
        """构建CarGurus品牌页面URL"""
        make_code = await self.config_dao.get_make_code(make)
        return _build_cargurus_brand_url(
            make=make, zip_code=zip_code, distance=distance,
            make_code=make_code
        )
    
    async def build_cargurus_model_url(
        self, make: str, model: str, zip_code: str, distance: int
    ) -> str:
        """构建CarGurus车型页面URL"""
        make_code = await self.config_dao.get_make_code(make)
        model_code = await self.config_dao.get_model_code(make, model)
        return _build_cargurus_model_url(
            make=make, model=model, zip_code=zip_code, distance=distance,
            make_code=make_code, model_code=model_code
        )
    
    def build_cargurus_listing_url(self, listing_id: str) -> str:
        """构建CarGurus车源详情URL"""
        return build_cargurus_listing_url(listing_id)
    
    def extract_listing_id_from_url(self, url: str) -> Optional[str]:
        """从URL中提取车源ID"""
        return extract_listing_id_from_url(url)
    
    def is_valid_cargurus_url(self, url: str) -> bool:
        """验证是否为有效的CarGurus URL"""
        return is_valid_cargurus_url(url)
