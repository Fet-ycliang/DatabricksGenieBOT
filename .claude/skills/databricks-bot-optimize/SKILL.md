---
name: databricks-bot-optimize
description: |
  效能優化助手。提供快取、連接池、非同步、記憶體優化策略。
  觸發：「優化」「效能」「速度慢」「memory」「performance」「快取」
  幫助提升應用程式效能和資源使用效率。
---

# DatabricksGenieBOT Performance Optimizer

提供效能優化策略和實作指南，提升回應速度和資源效率。

## 優化領域

1. **HTTP 連接池** - 減少連接建立時間
2. **快取系統** - 避免重複計算
3. **非同步處理** - 提升並發能力
4. **記憶體管理** - 防止 OOM
5. **日誌優化** - 減少 I/O 開銷

---

## 1. HTTP 連接池優化

### 問題
每次 API 呼叫都建立新連接，浪費時間。

```python
# ❌ 不好：每次建立新連接
async def query_api(url):
    async with httpx.AsyncClient() as client:  # 新連接
        response = await client.get(url)
        return response.json()
```

**效能影響**：
- 連接建立時間：200-300ms
- TLS 握手：100-200ms
- 總延遲：300-500ms

### 解決方案

```python
# ✅ 好：重用連接池
class APIService:
    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """取得或建立 HTTP 客戶端（連接池）"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    connect=5.0,
                    read=10.0,
                    write=10.0,
                    pool=30.0
                ),
                limits=httpx.Limits(
                    max_keepalive_connections=5,  # 保持連接數
                    max_connections=10             # 最大連接數
                )
            )
        return self._client

    async def query_api(self, url: str):
        client = await self._get_client()
        response = await client.get(url)
        return response.json()

    async def close(self):
        """關閉客戶端"""
        if self._client:
            await self._client.aclose()
            self._client = None
```

**效能提升**：
- 首次請求：300ms（建立連接）
- 後續請求：20-30ms（重用連接）
- **提升 90%**

---

## 2. 快取系統實作

### 專案已實作的快取

```python
from app.utils.cache_utils import SimpleCache, cached_query, cached_chart

# 全域快取實例
query_cache = SimpleCache(max_size=100, ttl_seconds=3600)    # 1小時
chart_cache = SimpleCache(max_size=50, ttl_seconds=7200)     # 2小時
```

### 使用裝飾器快取

```python
from app.utils.cache_utils import cached_query

@cached_query(cache=query_cache)
async def expensive_query(space_id: str, query: str) -> dict:
    """昂貴的查詢（會被快取）"""
    result = await genie_service.query(space_id, query)
    return result

# 首次呼叫：1200ms（真實 API）
result1 = await expensive_query("space-1", "SELECT * FROM table")

# 後續呼叫：< 1ms（快取命中）
result2 = await expensive_query("space-1", "SELECT * FROM table")
```

### 手動快取控制

```python
from app.utils.cache_utils import SimpleCache

cache = SimpleCache(max_size=100, ttl_seconds=3600)

# 設定快取
cache_key = f"user:{user_id}:query:{query_hash}"
cache.set(cache_key, result)

# 取得快取
result = cache.get(cache_key)
if result is None:
    # 快取未命中，執行查詢
    result = await expensive_operation()
    cache.set(cache_key, result)

# 清除快取
cache.clear()

# 查看統計
stats = cache.get_stats()
print(f"命中率: {stats.hit_rate:.2%}")
```

---

## 3. 非同步最佳化

### 並發處理多個請求

```python
import asyncio

# ❌ 不好：序列處理
async def process_multiple_queries_serial(queries):
    results = []
    for query in queries:
        result = await genie_service.query(query)  # 等待完成
        results.append(result)
    return results
# 總時間：n × 1200ms

# ✅ 好：並發處理
async def process_multiple_queries_parallel(queries):
    tasks = [
        genie_service.query(query)
        for query in queries
    ]
    results = await asyncio.gather(*tasks)  # 並發執行
    return results
# 總時間：max(1200ms)
```

**效能提升**：
- 10 個查詢序列：12 秒
- 10 個查詢並發：1.5 秒
- **提升 88%**

### 使用 asyncio.gather 處理錯誤

```python
# 某些任務失敗時繼續
async def process_with_error_handling(queries):
    tasks = [genie_service.query(q) for q in queries]

    # return_exceptions=True：錯誤不會中斷其他任務
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 處理結果
    successes = []
    failures = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            failures.append((queries[i], result))
        else:
            successes.append(result)

    return successes, failures
```

---

## 4. 記憶體優化

### 會話自動清理

```python
from app.utils.session_manager import cleanup_expired_sessions

# 背景任務定期清理會話
async def session_cleanup_task():
    """背景清理任務"""
    while True:
        await asyncio.sleep(3600)  # 每小時執行
        count = await cleanup_expired_sessions(timeout_hours=4)
        logger.info(f"清理 {count} 個過期會話")

# 在應用程式啟動時啟動
asyncio.create_task(session_cleanup_task())
```

### 限制快取大小

```python
from app.utils.cache_utils import SimpleCache

# LRU + TTL 快取（自動清理）
cache = SimpleCache(
    max_size=100,      # 最多 100 項（LRU 驅逐）
    ttl_seconds=3600   # 1 小時過期
)

# 當超過 max_size 時，自動驅逐最少使用的項目
```

### 大資料分頁處理

```python
def process_large_dataset(data: list, chunk_size: int = 100):
    """分批處理大資料集"""
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i+chunk_size]
        yield chunk

# 使用
for chunk in process_large_dataset(large_data, chunk_size=100):
    process_chunk(chunk)
    # 每次只處理 100 項，避免記憶體爆炸
```

---

## 5. 日誌優化

### 問題
頻繁日誌 I/O 影響效能。

### 解決方案：日誌採樣

```python
import random
import time

class SampledLogger:
    """採樣日誌記錄器（減少 I/O）"""

    def __init__(self, logger, sample_rate: float = 0.01):
        """
        Args:
            logger: 標準 logger
            sample_rate: 採樣率（0.01 = 1%）
        """
        self.logger = logger
        self.sample_rate = sample_rate
        self.last_stats_time = time.time()
        self.stats = {"total": 0, "sampled": 0}

    def info(self, message: str, force: bool = False):
        """記錄 info（採樣）"""
        self.stats["total"] += 1

        if force or random.random() < self.sample_rate:
            self.logger.info(message)
            self.stats["sampled"] += 1

        # 定期輸出統計
        if time.time() - self.last_stats_time > 60:
            self.logger.info(
                f"日誌統計: {self.stats['sampled']}/{self.stats['total']} "
                f"({self.stats['sampled']/self.stats['total']*100:.1f}%)"
            )
            self.last_stats_time = time.time()
            self.stats = {"total": 0, "sampled": 0}

# 使用
sampled_logger = SampledLogger(logger, sample_rate=0.01)

for i in range(1000):
    sampled_logger.info(f"處理請求 {i}")  # 只記錄 1%
```

**效能提升**：
- 日誌 I/O 減少 99%
- 應用程式吞吐量提升 15-20%

---

## 6. 資料庫查詢優化（Databricks）

### 批次查詢

```python
# ❌ 不好：多次小查詢
async def get_user_data_serial(user_ids):
    results = []
    for user_id in user_ids:
        result = await db.query(f"SELECT * FROM users WHERE id = {user_id}")
        results.append(result)
    return results
# 10 個用戶 = 10 次查詢

# ✅ 好：單次批次查詢
async def get_user_data_batch(user_ids):
    ids_str = ','.join([f"'{uid}'" for uid in user_ids])
    query = f"SELECT * FROM users WHERE id IN ({ids_str})"
    result = await db.query(query)
    return result
# 10 個用戶 = 1 次查詢
```

### 使用 LIMIT

```python
# 只取需要的資料
query = "SELECT * FROM large_table LIMIT 100"  # 限制結果數
```

---

## 7. 圖表生成優化

### 快取圖表

```python
from app.utils.cache_utils import cached_chart

@cached_chart(cache=chart_cache)
def generate_chart(data: list, chart_type: str) -> str:
    """生成圖表（會被快取）"""
    # 圖表生成邏輯...
    return base64_image

# 首次：300ms（生成圖表）
chart1 = generate_chart(data, "bar")

# 後續：< 1ms（快取命中）
chart2 = generate_chart(data, "bar")
```

### 降低圖表解析度

```python
import matplotlib.pyplot as plt

# 調整 DPI 平衡品質和大小
plt.savefig(
    buffer,
    format='png',
    dpi=100,  # 降低 DPI（預設 150）
    bbox_inches='tight'
)
```

---

## 8. 效能監控

### 測量關鍵操作時間

```python
import time
from functools import wraps

def measure_time(operation_name: str):
    """測量函式執行時間的裝飾器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            result = await func(*args, **kwargs)
            elapsed = time.time() - start

            logger.info(
                f"⏱️ {operation_name} 耗時: {elapsed*1000:.0f}ms"
            )

            # 如果超過閾值，發出警告
            if elapsed > 2.0:
                logger.warning(
                    f"⚠️ {operation_name} 執行緩慢: {elapsed:.2f}s"
                )

            return result
        return wrapper
    return decorator

# 使用
@measure_time("Genie 查詢")
async def query_genie(query: str):
    result = await genie_service.query(query)
    return result
```

### 記憶體使用監控

```python
import psutil
import os

def log_memory_usage():
    """記錄記憶體使用"""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()

    memory_mb = memory_info.rss / 1024 / 1024

    logger.info(f"📊 記憶體使用: {memory_mb:.0f} MB")

    # 警告高記憶體使用
    if memory_mb > 500:  # > 500 MB
        logger.warning(f"⚠️ 記憶體使用過高: {memory_mb:.0f} MB")

# 定期監控
async def memory_monitor_task():
    while True:
        log_memory_usage()
        await asyncio.sleep(300)  # 每 5 分鐘
```

---

## 9. 效能基準測試

### 簡單基準測試

```python
import time
import asyncio

async def benchmark_function(func, iterations: int = 100):
    """基準測試函式效能"""

    # 暖身
    await func()

    # 測量
    times = []
    for _ in range(iterations):
        start = time.time()
        await func()
        elapsed = time.time() - start
        times.append(elapsed)

    # 統計
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    print(f"平均: {avg_time*1000:.0f}ms")
    print(f"最小: {min_time*1000:.0f}ms")
    print(f"最大: {max_time*1000:.0f}ms")

    return times

# 使用
async def test_query():
    return await genie_service.query("SELECT 1")

await benchmark_function(test_query, iterations=100)
```

---

## 10. 優化檢查清單

效能優化前檢查：

- [ ] 使用 HTTP 連接池（httpx.AsyncClient 重用）
- [ ] 實作快取系統（查詢、圖表）
- [ ] 並發處理多個請求（asyncio.gather）
- [ ] 會話自動清理（防止記憶體洩漏）
- [ ] 日誌採樣（減少 I/O）
- [ ] 限制快取大小（LRU + TTL）
- [ ] 大資料分頁處理
- [ ] 測量關鍵操作時間
- [ ] 監控記憶體使用
- [ ] 基準測試驗證優化效果

---

## 快速參考

### 優化策略優先級

| 優先級 | 策略 | 預期提升 | 實作複雜度 |
|-------|------|---------|----------|
| 🔴 高 | HTTP 連接池 | 90% | 低 |
| 🔴 高 | 查詢快取 | 99% | 低 |
| 🟡 中 | 並發處理 | 80% | 中 |
| 🟡 中 | 會話清理 | 避免 OOM | 低 |
| 🟢 低 | 日誌採樣 | 15% | 中 |
| 🟢 低 | 圖表快取 | 99% | 低 |

### 效能目標

```
API 回應時間（首次）：< 1500ms
API 回應時間（快取）：< 50ms
記憶體使用：< 300MB
並發請求：10-50 QPS
```

---

## 參考資源

- [docs/architecture/optimization.md](../../../docs/architecture/optimization.md) - 完整優化指南
- [app/utils/cache_utils.py](../../../app/utils/cache_utils.py) - 快取實作
- [app/utils/session_manager.py](../../../app/utils/session_manager.py) - 會話管理
