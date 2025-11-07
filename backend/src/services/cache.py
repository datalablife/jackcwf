"""
数据库架构缓存服务。

实现具有 TTL 的缓存机制来存储数据库架构信息。
使用内存中的 LRU 缓存，默认 TTL 为 5 分钟。
"""

import asyncio
from functools import lru_cache
from typing import Any, Dict, Optional
from datetime import datetime, timedelta


class CacheEntry:
    """缓存条目，包含数据和过期时间。"""

    def __init__(self, data: Any, ttl_seconds: int = 300):
        """
        初始化缓存条目。

        参数:
            data: 要缓存的数据
            ttl_seconds: 生存时间（秒），默认 300 秒（5 分钟）
        """
        self.data = data
        self.created_at = datetime.utcnow()
        self.ttl_seconds = ttl_seconds

    def is_expired(self) -> bool:
        """
        检查缓存条目是否已过期。

        返回:
            bool: 如果过期返回 True
        """
        expiry_time = self.created_at + timedelta(seconds=self.ttl_seconds)
        return datetime.utcnow() > expiry_time


class SchemaCache:
    """
    数据库架构缓存。

    使用字典存储缓存，键为 (datasource_id, schema_name)。
    """

    def __init__(self, default_ttl: int = 300):
        """
        初始化架构缓存。

        参数:
            default_ttl: 默认 TTL（秒），默认 300 秒（5 分钟）
        """
        self._cache: Dict[tuple, CacheEntry] = {}
        self.default_ttl = default_ttl

    def get(self, datasource_id: int, schema_name: str = "public") -> Optional[Any]:
        """
        从缓存获取架构信息。

        参数:
            datasource_id: 数据源 ID
            schema_name: 架构名称，默认 'public'

        返回:
            缓存的数据，或如果过期/不存在返回 None
        """
        key = (datasource_id, schema_name)
        entry = self._cache.get(key)

        if entry is None:
            return None

        if entry.is_expired():
            del self._cache[key]
            return None

        return entry.data

    def set(
        self,
        datasource_id: int,
        data: Any,
        schema_name: str = "public",
        ttl: Optional[int] = None,
    ) -> None:
        """
        在缓存中设置架构信息。

        参数:
            datasource_id: 数据源 ID
            data: 要缓存的数据
            schema_name: 架构名称，默认 'public'
            ttl: 生存时间（秒），若为 None 则使用默认值
        """
        key = (datasource_id, schema_name)
        ttl_seconds = ttl or self.default_ttl
        self._cache[key] = CacheEntry(data, ttl_seconds)

    def invalidate(self, datasource_id: int, schema_name: str = "public") -> None:
        """
        使缓存条目失效。

        参数:
            datasource_id: 数据源 ID
            schema_name: 架构名称，默认 'public'
        """
        key = (datasource_id, schema_name)
        if key in self._cache:
            del self._cache[key]

    def invalidate_all(self, datasource_id: int) -> None:
        """
        使数据源的所有缓存条目失效。

        参数:
            datasource_id: 数据源 ID
        """
        keys_to_delete = [key for key in self._cache if key[0] == datasource_id]
        for key in keys_to_delete:
            del self._cache[key]

    def clear(self) -> None:
        """清空所有缓存。"""
        self._cache.clear()

    def get_stats(self) -> Dict[str, int]:
        """
        获取缓存统计信息。

        返回:
            dict: 包含 'total'（总条目数）和 'valid'（有效条目数）的统计信息
        """
        total = len(self._cache)
        valid = sum(1 for entry in self._cache.values() if not entry.is_expired())
        return {"total": total, "valid": valid}


# 全局缓存实例
_schema_cache: Optional[SchemaCache] = None


def get_schema_cache(default_ttl: int = 300) -> SchemaCache:
    """
    获取或创建全局架构缓存实例（单例模式）。

    参数:
        default_ttl: 默认 TTL（秒），默认 300 秒（5 分钟）

    返回:
        SchemaCache: 全局缓存实例
    """
    global _schema_cache

    if _schema_cache is None:
        _schema_cache = SchemaCache(default_ttl)

    return _schema_cache
