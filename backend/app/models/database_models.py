#!/usr/bin/env python3
"""
数据库模型定义 - 车源存储和管理
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import Optional, List
import json

Base = declarative_base()


class CarListingDB(Base):
    """
    车源数据库表 - 存储从各平台爬取的车源信息
    """
    __tablename__ = "car_listings"
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 车源基本信息
    platform = Column(String(50), nullable=False, comment="平台名称 (cargurus, kijiji, etc.)")
    platform_id = Column(String(100), nullable=False, comment="平台内部ID")
    title = Column(String(500), nullable=False, comment="车源标题")
    make = Column(String(100), comment="品牌")
    model = Column(String(100), comment="型号")
    year = Column(Integer, comment="年份")
    
    # 价格和里程
    price = Column(Float, comment="价格 (数字)")
    price_text = Column(String(100), comment="价格文本")
    mileage = Column(Integer, comment="里程数")
    mileage_text = Column(String(100), comment="里程文本")
    
    # 位置信息
    city = Column(String(100), comment="城市")
    province = Column(String(50), comment="省份")
    postal_code = Column(String(20), comment="邮编")
    
    # 链接和图片
    link = Column(Text, nullable=False, comment="详情链接")
    image_url = Column(Text, comment="图片链接")
    
    # 车源状态
    is_active = Column(Boolean, default=True, comment="是否有效")
    is_sold = Column(Boolean, default=False, comment="是否已售出")
    
    # 质量评分
    quality_score = Column(Float, comment="质量评分 (0-100)")
    price_score = Column(Float, comment="价格评分 (0-100)")
    year_score = Column(Float, comment="年份评分 (0-100)")
    mileage_score = Column(Float, comment="里程评分 (0-100)")
    overall_score = Column(Float, comment="综合评分 (0-100)")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    last_seen_at = Column(DateTime, default=datetime.utcnow, comment="最后发现时间")
    
    # 额外信息 (JSON格式存储)
    extra_info = Column(Text, comment="额外信息 (JSON格式)")
    
    # 索引
    __table_args__ = (
        Index('idx_platform_id', 'platform', 'platform_id'),
        Index('idx_make_model_year', 'make', 'model', 'year'),
        Index('idx_price_range', 'price'),
        Index('idx_location', 'city', 'province'),
        Index('idx_quality_score', 'overall_score'),
        Index('idx_active_listings', 'is_active', 'is_sold'),
        Index('idx_created_at', 'created_at'),
    )
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'id': self.id,
            'platform': self.platform,
            'platform_id': self.platform_id,
            'title': self.title,
            'make': self.make,
            'model': self.model,
            'year': self.year,
            'price': self.price,
            'price_text': self.price_text,
            'mileage': self.mileage,
            'mileage_text': self.mileage_text,
            'city': self.city,
            'province': self.province,
            'postal_code': self.postal_code,
            'link': self.link,
            'image_url': self.image_url,
            'is_active': self.is_active,
            'is_sold': self.is_sold,
            'quality_score': self.quality_score,
            'price_score': self.price_score,
            'year_score': self.year_score,
            'mileage_score': self.mileage_score,
            'overall_score': self.overall_score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_seen_at': self.last_seen_at.isoformat() if self.last_seen_at else None,
            'extra_info': json.loads(self.extra_info) if self.extra_info else None
        }
    
    def get_extra_info(self) -> dict:
        """获取额外信息"""
        if self.extra_info:
            try:
                return json.loads(self.extra_info)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_extra_info(self, info: dict):
        """设置额外信息"""
        self.extra_info = json.dumps(info, ensure_ascii=False)


class CarSearchHistory(Base):
    """
    搜索历史表 - 记录用户搜索行为
    """
    __tablename__ = "car_search_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), comment="会话ID")
    user_query = Column(Text, nullable=False, comment="用户查询")
    parsed_query = Column(Text, comment="解析后的查询 (JSON)")
    search_results_count = Column(Integer, comment="搜索结果数量")
    search_duration = Column(Float, comment="搜索耗时 (秒)")
    created_at = Column(DateTime, default=datetime.utcnow, comment="搜索时间")
    
    # 索引
    __table_args__ = (
        Index('idx_session_id', 'session_id'),
        Index('idx_created_at', 'created_at'),
    )


class CarRecommendationLog(Base):
    """
    推荐日志表 - 记录推荐算法执行情况
    """
    __tablename__ = "car_recommendation_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), comment="会话ID")
    search_query = Column(Text, comment="搜索查询")
    total_candidates = Column(Integer, comment="候选车源总数")
    selected_count = Column(Integer, comment="选择的车源数量")
    selection_criteria = Column(Text, comment="选择标准 (JSON)")
    execution_time = Column(Float, comment="执行时间 (秒)")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    
    # 索引
    __table_args__ = (
        Index('idx_session_id', 'session_id'),
        Index('idx_created_at', 'created_at'),
    )


class DatabaseManager:
    """
    数据库管理器 - 负责数据库连接和会话管理
    """
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # 创建所有表
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """获取数据库会话"""
        return self.SessionLocal()
    
    def close(self):
        """关闭数据库连接"""
        self.engine.dispose()
