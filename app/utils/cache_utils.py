"""
快取工具

提供 LRU 快取機制，用於優化查詢和圖表生成效能。
"""

import hashlib
import logging
from typing import Any, Optional, Callable
from functools import lru_cache, wraps
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CacheStats:
    """快取統計資訊"""

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    @property
    def total_requests(self) -> int:
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        """計算命中率（0-1）"""
        if self.total_requests == 0:
            return 0.0
        return self.hits / self.total_requests

    def record_hit(self):
        self.hits += 1

    def record_miss(self):
        self.misses += 1

    def record_eviction(self):
        self.evictions += 1

    def to_dict(self) -> dict:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "total_requests": self.total_requests,
            "hit_rate": f"{self.hit_rate:.2%}"
        }


class SimpleCache:
    """
    簡單的記憶體快取實現

    特點：
    - TTL（Time To Live）支援
    - 容量限制（LRU 驅逐策略）
    - 統計資訊追蹤
    """

    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        """
        初始化快取

        Args:
            max_size: 最大快取項目數
            ttl_seconds: 快取項目的生存時間（秒）
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache = {}  # key -> (value, timestamp)
        self._access_order = []  # LRU tracking
        self.stats = CacheStats()

    def _is_expired(self, timestamp: datetime) -> bool:
        """檢查快取項目是否過期"""
        return datetime.now() - timestamp > timedelta(seconds=self.ttl_seconds)

    def _evict_lru(self):
        """驅逐最少使用的項目"""
        if self._access_order:
            lru_key = self._access_order.pop(0)
            if lru_key in self._cache:
                del self._cache[lru_key]
                self.stats.record_eviction()
                logger.debug(f"驅逐 LRU 快取項目: {lru_key[:32]}...")

    def get(self, key: str) -> Optional[Any]:
        """
        從快取中取得值

        Args:
            key: 快取鍵

        Returns:
            快取的值，如果不存在或已過期則返回 None
        """
        if key not in self._cache:
            self.stats.record_miss()
            return None

        value, timestamp = self._cache[key]

        # 檢查是否過期
        if self._is_expired(timestamp):
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            self.stats.record_miss()
            logger.debug(f"快取項目已過期: {key[:32]}...")
            return None

        # 更新訪問順序（移到最後）
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

        self.stats.record_hit()
        logger.debug(f"快取命中: {key[:32]}...")
        return value

    def set(self, key: str, value: Any):
        """
        設定快取值

        Args:
            key: 快取鍵
            value: 要快取的值
        """
        # 如果快取已滿，驅逐 LRU
        if len(self._cache) >= self.max_size and key not in self._cache:
            self._evict_lru()

        # 設定新值
        self._cache[key] = (value, datetime.now())

        # 更新訪問順序
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

        logger.debug(f"快取設定: {key[:32]}... (size: {len(self._cache)}/{self.max_size})")

    def clear(self):
        """清空快取"""
        self._cache.clear()
        self._access_order.clear()
        logger.info("快取已清空")

    def get_stats(self) -> dict:
        """取得快取統計資訊"""
        stats = self.stats.to_dict()
        stats["current_size"] = len(self._cache)
        stats["max_size"] = self.max_size
        stats["ttl_seconds"] = self.ttl_seconds
        return stats


def generate_cache_key(*args, **kwargs) -> str:
    """
    生成快取鍵

    基於參數生成唯一的快取鍵（使用 SHA256）

    Args:
        *args: 位置參數
        **kwargs: 關鍵字參數

    Returns:
        快取鍵（SHA256 hash）
    """
    # 建立可序列化的表示
    key_parts = []

    for arg in args:
        if isinstance(arg, (str, int, float, bool)):
            key_parts.append(str(arg))
        else:
            key_parts.append(repr(arg))

    for k, v in sorted(kwargs.items()):
        if isinstance(v, (str, int, float, bool)):
            key_parts.append(f"{k}={v}")
        else:
            key_parts.append(f"{k}={repr(v)}")

    key_string = "|".join(key_parts)
    return hashlib.sha256(key_string.encode()).hexdigest()


# 全域快取實例
_query_cache = SimpleCache(max_size=50, ttl_seconds=3600)  # 查詢快取：1 小時
_chart_cache = SimpleCache(max_size=30, ttl_seconds=1800)  # 圖表快取：30 分鐘


def get_query_cache() -> SimpleCache:
    """取得查詢快取實例"""
    return _query_cache


def get_chart_cache() -> SimpleCache:
    """取得圖表快取實例"""
    return _chart_cache


def cached_query(func: Callable) -> Callable:
    """
    查詢結果快取裝飾器

    自動快取函數結果，基於函數參數生成快取鍵。

    Example:
        ```python
        @cached_query
        async def query_databricks(user_email: str, question: str):
            # 執行實際查詢
            return result
        ```
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # 生成快取鍵
        cache_key = generate_cache_key(func.__name__, *args, **kwargs)

        # 嘗試從快取取得
        cached_result = _query_cache.get(cache_key)
        if cached_result is not None:
            logger.info(f"使用快取的查詢結果: {func.__name__}")
            return cached_result

        # 執行實際查詢
        result = await func(*args, **kwargs)

        # 儲存到快取
        if result is not None:
            _query_cache.set(cache_key, result)

        return result

    return wrapper


def cached_chart(func: Callable) -> Callable:
    """
    圖表生成快取裝飾器

    自動快取生成的圖表，避免重複渲染。

    Example:
        ```python
        @cached_chart
        def generate_bar_chart(data: dict, title: str):
            # 生成圖表
            return chart_base64
        ```
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 生成快取鍵
        cache_key = generate_cache_key(func.__name__, *args, **kwargs)

        # 嘗試從快取取得
        cached_result = _chart_cache.get(cache_key)
        if cached_result is not None:
            logger.info(f"使用快取的圖表: {func.__name__}")
            return cached_result

        # 執行實際生成
        result = func(*args, **kwargs)

        # 儲存到快取
        if result is not None:
            _chart_cache.set(cache_key, result)

        return result

    return wrapper


def clear_all_caches():
    """清空所有快取"""
    _query_cache.clear()
    _chart_cache.clear()
    logger.info("所有快取已清空")


def get_all_cache_stats() -> dict:
    """取得所有快取的統計資訊"""
    return {
        "query_cache": _query_cache.get_stats(),
        "chart_cache": _chart_cache.get_stats(),
    }
