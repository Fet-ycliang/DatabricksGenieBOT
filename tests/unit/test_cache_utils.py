"""
測試快取工具
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from app.utils.cache_utils import (
    SimpleCache,
    CacheStats,
    generate_cache_key,
    cached_query,
    cached_chart,
    get_query_cache,
    get_chart_cache,
    clear_all_caches,
    get_all_cache_stats,
)


def test_cache_stats():
    """測試快取統計"""
    stats = CacheStats()

    assert stats.hits == 0
    assert stats.misses == 0
    assert stats.total_requests == 0
    assert stats.hit_rate == 0.0

    stats.record_hit()
    stats.record_hit()
    stats.record_miss()

    assert stats.hits == 2
    assert stats.misses == 1
    assert stats.total_requests == 3
    assert stats.hit_rate == pytest.approx(0.666, 0.01)

    stats_dict = stats.to_dict()
    assert stats_dict["hits"] == 2
    assert stats_dict["misses"] == 1
    assert "66.67%" in stats_dict["hit_rate"]


def test_simple_cache_basic():
    """測試基本快取操作"""
    cache = SimpleCache(max_size=3, ttl_seconds=60)

    # 設定值
    cache.set("key1", "value1")
    cache.set("key2", "value2")

    # 取得值
    assert cache.get("key1") == "value1"
    assert cache.get("key2") == "value2"
    assert cache.get("key3") is None

    # 檢查統計
    assert cache.stats.hits == 2
    assert cache.stats.misses == 1


def test_simple_cache_lru_eviction():
    """測試 LRU 驅逐策略"""
    cache = SimpleCache(max_size=3, ttl_seconds=60)

    # 填滿快取
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")

    # 訪問 key1（移到最後）
    cache.get("key1")

    # 加入第 4 個項目，應該驅逐 key2（最少使用）
    cache.set("key4", "value4")

    assert cache.get("key1") == "value1"
    assert cache.get("key2") is None  # 被驅逐
    assert cache.get("key3") == "value3"
    assert cache.get("key4") == "value4"


def test_simple_cache_ttl_expiration():
    """測試 TTL 過期"""
    cache = SimpleCache(max_size=10, ttl_seconds=1)

    cache.set("key1", "value1")

    # 立即取得應該成功
    assert cache.get("key1") == "value1"

    # 等待過期
    import time
    time.sleep(1.1)

    # 過期後應該返回 None
    assert cache.get("key1") is None


def test_simple_cache_clear():
    """測試清空快取"""
    cache = SimpleCache(max_size=10, ttl_seconds=60)

    cache.set("key1", "value1")
    cache.set("key2", "value2")

    assert cache.get("key1") == "value1"

    cache.clear()

    assert cache.get("key1") is None
    assert cache.get("key2") is None


def test_generate_cache_key():
    """測試快取鍵生成"""
    # 相同參數應該生成相同的鍵
    key1 = generate_cache_key("user@example.com", "query1", limit=10)
    key2 = generate_cache_key("user@example.com", "query1", limit=10)
    assert key1 == key2

    # 不同參數應該生成不同的鍵
    key3 = generate_cache_key("user@example.com", "query2", limit=10)
    assert key1 != key3

    # 關鍵字參數順序不影響結果
    key4 = generate_cache_key("user@example.com", limit=10, offset=0)
    key5 = generate_cache_key("user@example.com", offset=0, limit=10)
    assert key4 == key5


def test_cached_query_decorator():
    """測試查詢快取裝飾器"""
    call_count = 0

    @cached_query
    async def mock_query(user: str, question: str):
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.01)  # 模擬延遲
        return f"Result for {user}: {question}"

    # 第一次調用，應該執行函數
    result1 = asyncio.run(mock_query("user1", "question1"))
    assert call_count == 1
    assert result1 == "Result for user1: question1"

    # 第二次調用相同參數，應該使用快取
    result2 = asyncio.run(mock_query("user1", "question1"))
    assert call_count == 1  # 沒有增加
    assert result2 == result1

    # 不同參數，應該執行函數
    result3 = asyncio.run(mock_query("user2", "question2"))
    assert call_count == 2
    assert result3 == "Result for user2: question2"


def test_cached_chart_decorator():
    """測試圖表快取裝飾器"""
    call_count = 0

    @cached_chart
    def mock_chart_gen(title: str, data: list):
        nonlocal call_count
        call_count += 1
        return f"Chart: {title} with {len(data)} points"

    # 第一次調用
    chart1 = mock_chart_gen("Sales", [1, 2, 3])
    assert call_count == 1
    assert chart1 == "Chart: Sales with 3 points"

    # 第二次調用相同參數，使用快取
    chart2 = mock_chart_gen("Sales", [1, 2, 3])
    assert call_count == 1  # 沒有增加
    assert chart2 == chart1

    # 不同參數
    chart3 = mock_chart_gen("Revenue", [4, 5])
    assert call_count == 2
    assert chart3 == "Chart: Revenue with 2 points"


def test_global_cache_instances():
    """測試全域快取實例"""
    query_cache = get_query_cache()
    chart_cache = get_chart_cache()

    assert query_cache is not None
    assert chart_cache is not None
    assert query_cache != chart_cache

    # 測試設定和取得
    query_cache.set("test_key", "test_value")
    assert query_cache.get("test_key") == "test_value"


def test_clear_all_caches():
    """測試清空所有快取"""
    query_cache = get_query_cache()
    chart_cache = get_chart_cache()

    query_cache.set("key1", "value1")
    chart_cache.set("key2", "value2")

    clear_all_caches()

    assert query_cache.get("key1") is None
    assert chart_cache.get("key2") is None


def test_get_all_cache_stats():
    """測試取得所有快取統計"""
    # 清空快取以獲得乾淨狀態
    clear_all_caches()

    query_cache = get_query_cache()
    query_cache.set("key1", "value1")
    query_cache.get("key1")

    stats = get_all_cache_stats()

    assert "query_cache" in stats
    assert "chart_cache" in stats

    assert stats["query_cache"]["current_size"] >= 1
    assert stats["query_cache"]["hits"] >= 1
