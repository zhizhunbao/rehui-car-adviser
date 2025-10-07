from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class SearchRequest(BaseModel):
    query: str = Field(..., description="用户搜索查询", min_length=1, max_length=500)

class CarListing(BaseModel):
    id: str = Field(..., description="车源唯一标识")
    title: str = Field(..., description="车源标题")
    price: str = Field(..., description="价格")
    year: int = Field(..., description="年份")
    mileage: str = Field(..., description="里程")
    city: str = Field(..., description="城市")
    link: str = Field(..., description="详情链接")
    image: Optional[str] = Field(None, description="图片链接")

class SearchResponse(BaseModel):
    success: bool = Field(..., description="请求是否成功")
    data: Optional[List[CarListing]] = Field(None, description="搜索结果数据")
    error: Optional[str] = Field(None, description="错误信息")
    message: Optional[str] = Field(None, description="响应消息")
    total_count: Optional[int] = Field(None, description="结果总数")

class ParsedQuery(BaseModel):
    make: Optional[str] = Field(None, description="品牌")
    model: Optional[str] = Field(None, description="型号")
    year_min: Optional[int] = Field(None, description="最小年份")
    year_max: Optional[int] = Field(None, description="最大年份")
    price_max: Optional[float] = Field(None, description="最大价格")
    mileage_max: Optional[int] = Field(None, description="最大里程")
    location: Optional[str] = Field(None, description="位置")
    keywords: List[str] = Field(default_factory=list, description="关键词")
