#!/usr/bin/env python3
"""
基础 DAO 类 - 提供通用的数据库访问功能
"""

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from app.utils.core.logger import get_logger
from app.utils.data.db_utils import get_sync_db_util

logger = get_logger(__name__)

T = TypeVar("T")


class BaseDAO(ABC, Generic[T]):
    """
    基础 DAO 类
    提供通用的数据库访问功能，包括会话管理、错误处理等
    """

    def __init__(self, model_class: Type[T]):
        """
        初始化 DAO

        Args:
            model_class: 数据库模型类
        """
        self.model_class = model_class
        self.db_util = get_sync_db_util()

    @contextmanager
    def get_session(self):
        """
        获取数据库会话的上下文管理器
        自动处理会话的创建、提交和回滚
        """
        session = self.db_util.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库操作失败: {str(e)}")
            raise
        finally:
            session.close()

    def create(self, **kwargs) -> T:
        """
        创建新记录

        Args:
            **kwargs: 记录字段

        Returns:
            创建的记录
        """
        with self.get_session() as session:
            instance = self.model_class(**kwargs)
            session.add(instance)
            session.flush()  # 获取生成的ID
            return instance

    def get_by_id(self, record_id: int) -> Optional[T]:
        """
        根据ID获取记录

        Args:
            record_id: 记录ID

        Returns:
            记录对象或None
        """
        with self.get_session() as session:
            return (
                session.query(self.model_class)
                .filter(self.model_class.id == record_id)
                .first()
            )

    def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[T]:
        """
        获取所有记录

        Args:
            limit: 限制数量
            offset: 偏移量

        Returns:
            记录列表
        """
        with self.get_session() as session:
            query = session.query(self.model_class)
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            return query.all()

    def update(self, record_id: int, **kwargs) -> Optional[T]:
        """
        更新记录

        Args:
            record_id: 记录ID
            **kwargs: 要更新的字段

        Returns:
            更新后的记录或None
        """
        with self.get_session() as session:
            instance = (
                session.query(self.model_class)
                .filter(self.model_class.id == record_id)
                .first()
            )

            if instance:
                for key, value in kwargs.items():
                    if hasattr(instance, key):
                        setattr(instance, key, value)
                session.flush()
                return instance
            return None

    def delete(self, record_id: int) -> bool:
        """
        删除记录

        Args:
            record_id: 记录ID

        Returns:
            是否删除成功
        """
        with self.get_session() as session:
            instance = (
                session.query(self.model_class)
                .filter(self.model_class.id == record_id)
                .first()
            )

            if instance:
                session.delete(instance)
                return True
            return False

    def count(self) -> int:
        """
        获取记录总数

        Returns:
            记录总数
        """
        with self.get_session() as session:
            return session.query(self.model_class).count()

    def exists(self, record_id: int) -> bool:
        """
        检查记录是否存在

        Args:
            record_id: 记录ID

        Returns:
            是否存在
        """
        with self.get_session() as session:
            return (
                session.query(self.model_class)
                .filter(self.model_class.id == record_id)
                .first()
                is not None
            )

    def bulk_create(self, records: List[Dict[str, Any]]) -> List[T]:
        """
        批量创建记录

        Args:
            records: 记录数据列表

        Returns:
            创建的记录列表
        """
        with self.get_session() as session:
            instances = []
            for record_data in records:
                instance = self.model_class(**record_data)
                session.add(instance)
                instances.append(instance)
            session.flush()
            return instances

    def bulk_update(self, updates: List[Dict[str, Any]]) -> int:
        """
        批量更新记录

        Args:
            updates: 更新数据列表，每个字典必须包含 'id' 字段

        Returns:
            更新的记录数量
        """
        updated_count = 0
        with self.get_session() as session:
            for update_data in updates:
                record_id = update_data.pop("id")
                instance = (
                    session.query(self.model_class)
                    .filter(self.model_class.id == record_id)
                    .first()
                )

                if instance:
                    for key, value in update_data.items():
                        if hasattr(instance, key):
                            setattr(instance, key, value)
                    updated_count += 1
            return updated_count

    def execute_raw_sql(
        self, sql: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        执行原始SQL查询

        Args:
            sql: SQL语句
            params: 参数

        Returns:
            查询结果
        """
        with self.get_session() as session:
            result = session.execute(sql, params or {})
            return [dict(row) for row in result.fetchall()]

    @abstractmethod
    def get_table_name(self) -> str:
        """
        获取表名

        Returns:
            表名
        """
        pass
