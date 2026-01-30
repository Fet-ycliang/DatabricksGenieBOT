# 🚀 Databricks Genie 機器人 - 效能優化建議

**日期:** 2026年1月30日  
**分析範圍:** 整個應用程式架構  
**優先級:** 企業級生產環境

---

## 📊 目前效能狀態

| 指標 | 狀態 | 備註 |
|------|------|------|
| HTTP 連接池 | ✅ 已實現 | 使用 aiohttp 連接重用 |
| 用戶快取 | ✅ 已實現 | LRU 快取（1000 大小）|
| 性能指標 | ✅ 已實現 | P50/P95 追蹤 |
| 日誌性能 | ⚠️ 需優化 | 大量日誌輸出可能影響性能 |
| 內存管理 | ⚠️ 需監控 | 用戶會話無自動過期 |
| 數據庫連接 | ✅ 良好 | 使用 Databricks SDK |

---

## 🎯 優化建議（按優先級排序）

### 優先級 1️⃣：日誌性能優化

#### 1.1 **異步日誌寫入** 🔴 HIGH

**問題:** 大量的日誌記錄（尤其是 `_log_api_response`）會阻塞主線程

**當前代碼:**
```python
def _log_api_response(self, request_id: str, response_data: Dict, total_elapsed: float) -> None:
    logger.info(
        f"\n{'='*80}\n"
        f"[{request_id}] 📤 API 響應 - 完整輸出\n"
        f"{self._format_json_for_logging(response_data)}\n"  # ⚠️ 大量字符串操作
        f"{'='*80}"
    )
```

**建議方案:**
```python
# ✅ 方案 1: 使用隊列異步寫入日誌
import queue
import threading

class AsyncLogger:
    def __init__(self):
        self.log_queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
    
    def _worker(self):
        """後台線程處理日誌"""
        while True:
            try:
                log_entry = self.log_queue.get(timeout=1)
                if log_entry is None:
                    break
                logger.info(log_entry)
            except queue.Empty:
                continue
    
    async def log_async(self, message: str):
        """異步日誌記錄"""
        self.log_queue.put(message)

# ✅ 方案 2: 條件化詳細日誌
def _log_api_response(self, request_id: str, response_data: Dict, total_elapsed: float) -> None:
    if os.environ.get('VERBOSE_LOGGING', '').lower() == 'true':
        logger.info(f"[{request_id}] 📤 API 響應已完成 ({total_elapsed:.2f}s)")
    
    # 僅在 DEBUG 模式記錄完整響應
    if os.environ.get('DEBUG_MODE', '').lower() == 'true':
        logger.debug(f"完整響應:\n{self._format_json_for_logging(response_data)}")
```

**預期改進:**
- ⬆️ 查詢響應時間 **減少 15-20%**
- ⬆️ 吞吐量 **提升 10-15%**

**實現難度:** ⭐⭐⭐ (中等)

---

#### 1.2 **日誌採樣** 🟡 MEDIUM

**問題:** 每個查詢都詳細記錄效能指標，對高流量有影響

**當前代碼:**
```python
if self.metrics.total_queries % 100 == 0:
    self.metrics.log_stats()  # 100 個查詢才記錄一次
```

**建議方案:**
```python
# ✅ 方案: 基於時間和查詢數的混合採樣
class SamplingLogger:
    def __init__(self, sample_rate: float = 0.01, time_interval: int = 60):
        self.sample_rate = sample_rate  # 1% 採樣率
        self.time_interval = time_interval  # 60 秒
        self.last_log_time = time.time()
    
    def should_log_stats(self, query_count: int) -> bool:
        """決定是否記錄統計信息"""
        import random
        
        # 時間條件：每 N 秒記錄一次
        if time.time() - self.last_log_time >= self.time_interval:
            self.last_log_time = time.time()
            return True
        
        # 查詢條件：按百分比採樣
        if random.random() < self.sample_rate and query_count % 10 == 0:
            return True
        
        return False

# 在 genie_service.py 使用
sampling_logger = SamplingLogger(sample_rate=0.01, time_interval=60)

if sampling_logger.should_log_stats(self.metrics.total_queries):
    self.metrics.log_stats()
```

**預期改進:**
- ⬇️ 日誌輸出 **減少 99%**（1% 採樣）
- ⬆️ I/O 負載 **減少 50-70%**

**實現難度:** ⭐⭐ (簡單)

---

### 優先級 2️⃣：內存管理優化

#### 2.1 **用戶會話自動過期清理** 🔴 HIGH

**問題:** 用戶會話無限期存儲，造成內存洩漏

**當前代碼:**
```python
class MyBot(ActivityHandler):
    def __init__(self, genie_service: GenieService):
        self.user_sessions: Dict[str, UserSession] = {}  # 無限增長
```

**建議方案:**
```python
# ✅ 方案: LRU 快取 + TTL 組合
from functools import lru_cache
import time

class SessionManager:
    """帶 TTL 和 LRU 清理的會話管理器"""
    
    def __init__(self, max_sessions: int = 1000, ttl_seconds: int = 86400):
        self.user_sessions: Dict[str, UserSession] = {}
        self.max_sessions = max_sessions
        self.ttl_seconds = ttl_seconds  # 24 小時 TTL
        self.access_times: Dict[str, float] = {}
    
    def get_session(self, user_id: str) -> Optional[UserSession]:
        """獲取會話並更新訪問時間"""
        if user_id not in self.user_sessions:
            return None
        
        # 檢查 TTL
        last_access = self.access_times.get(user_id, 0)
        if time.time() - last_access > self.ttl_seconds:
            self.delete_session(user_id)
            return None
        
        # 更新訪問時間
        self.access_times[user_id] = time.time()
        return self.user_sessions[user_id]
    
    def add_session(self, user_id: str, session: UserSession) -> None:
        """添加會話，如果超過限制則清理最舊的"""
        if len(self.user_sessions) >= self.max_sessions:
            # 移除最舊的訪問的會話
            oldest_user = min(self.access_times, key=self.access_times.get)
            self.delete_session(oldest_user)
        
        self.user_sessions[user_id] = session
        self.access_times[user_id] = time.time()
    
    def delete_session(self, user_id: str) -> None:
        """刪除會話"""
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
            del self.access_times[user_id]
            logger.info(f"🗑️ 已清理過期會話: {user_id}")
    
    def cleanup_expired(self) -> int:
        """清理所有過期會話，返回清理數量"""
        current_time = time.time()
        expired_users = [
            user_id for user_id, access_time in self.access_times.items()
            if current_time - access_time > self.ttl_seconds
        ]
        
        for user_id in expired_users:
            self.delete_session(user_id)
        
        return len(expired_users)

# ✅ 在 app.py 中使用
class MyBot(ActivityHandler):
    def __init__(self, genie_service: GenieService):
        self.genie_service = genie_service
        self.session_manager = SessionManager(max_sessions=1000, ttl_seconds=86400)
        # ...

# ✅ 定期清理任務
async def cleanup_task():
    """每小時運行一次會話清理"""
    while True:
        await asyncio.sleep(3600)  # 每小時
        count = BOT.session_manager.cleanup_expired()
        logger.info(f"✅ 已清理 {count} 個過期會話")

# 在應用啟動時註冊
async def on_startup(app: web.Application):
    asyncio.create_task(cleanup_task())
```

**預期改進:**
- ⬇️ 內存使用 **減少 60-80%**（長期運行）
- ✅ 防止 OOM（Out of Memory）崩潰
- ✅ 完全自動化，無需人工干預

**實現難度:** ⭐⭐⭐ (中等)

---

#### 2.2 **用戶上下文快取大小優化** 🟡 MEDIUM

**問題:** LRU 快取大小固定為 1000，在高流量下可能不足

**建議方案:**
```python
# ✅ 動態調整快取大小
class AdaptiveLRUCache:
    """根據內存使用情況動態調整 LRU 快取大小"""
    
    def __init__(self, initial_size: int = 1000):
        self.cache = {}
        self.max_size = initial_size
        self.access_order = deque()  # 追蹤訪問順序
    
    def get(self, key: str):
        if key in self.cache:
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        return None
    
    def put(self, key: str, value: Any) -> None:
        if key in self.cache:
            self.access_order.remove(key)
        elif len(self.cache) >= self.max_size:
            # 移除最舊的條目
            oldest = self.access_order.popleft()
            del self.cache[oldest]
        
        self.cache[key] = value
        self.access_order.append(key)
    
    def adjust_size_based_on_memory(self) -> None:
        """根據內存使用情況調整快取大小"""
        import psutil
        
        mem_percent = psutil.virtual_memory().percent
        
        if mem_percent > 80:  # 內存超過 80%
            self.max_size = max(100, int(self.max_size * 0.8))
            logger.warning(f"⚠️ 內存壓力高，減少快取大小到 {self.max_size}")
        elif mem_percent < 50:  # 內存低於 50%
            self.max_size = min(5000, int(self.max_size * 1.2))
            logger.info(f"✅ 內存充足，增加快取大小到 {self.max_size}")
```

**預期改進:**
- 🎯 自適應內存使用
- ⬆️ 高流量下快取命中率提升

**實現難度:** ⭐⭐⭐ (中等)

---

### 優先級 3️⃣：API 調用優化

#### 3.1 **請求批量化** 🟡 MEDIUM

**問題:** 無法對 Databricks 進行批量查詢

**建議方案:**
```python
# ✅ 實現請求批隊列
from collections import deque
import asyncio

class RequestBatcher:
    """批量化 API 請求以提高吞吐量"""
    
    def __init__(self, batch_size: int = 5, batch_timeout: float = 0.5):
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.queue: deque = deque()
        self.pending_futures: List = []
    
    async def add_request(self, request_data: Dict) -> Any:
        """添加請求到隊列並等待結果"""
        future = asyncio.Future()
        self.queue.append((request_data, future))
        
        # 如果達到批次大小，立即處理
        if len(self.queue) >= self.batch_size:
            await self._process_batch()
        
        return await future
    
    async def _process_batch(self) -> None:
        """處理一個批次的請求"""
        batch = []
        futures = []
        
        while self.queue and len(batch) < self.batch_size:
            request_data, future = self.queue.popleft()
            batch.append(request_data)
            futures.append(future)
        
        if not batch:
            return
        
        # 批量發送請求
        logger.info(f"📦 處理批次: {len(batch)} 個請求")
        
        try:
            results = await self._send_batch(batch)
            for future, result in zip(futures, results):
                future.set_result(result)
        except Exception as e:
            for future in futures:
                future.set_exception(e)
    
    async def _send_batch(self, batch: List[Dict]) -> List[Any]:
        """發送批次請求"""
        # 這裡實現實際的 API 調用邏輯
        pass
```

**預期改進:**
- ⬆️ 吞吐量 **提升 30-50%**（適用於高並發場景）
- ⬇️ 延遲 **減少 10-20%**

**實現難度:** ⭐⭐⭐⭐ (複雜)

---

#### 3.2 **連接超時優化** 🔴 HIGH

**問題:** 無超時配置，慢速連接會堵塞

**建議方案:**
```python
# ✅ 設置合理的超時配置
@asynccontextmanager
async def get_http_session(self):
    """帶優化超時的 HTTP Session"""
    if not self._http_session or self._http_session.closed:
        timeout = aiohttp.ClientTimeout(
            total=30,      # 總超時：30 秒
            connect=5,     # 連接超時：5 秒
            sock_read=10,  # 讀取超時：10 秒
            sock_connect=5 # Socket 連接：5 秒
        )
        self._http_session = aiohttp.ClientSession(
            timeout=timeout,
            connector=aiohttp.TCPConnector(
                limit=100,           # 連接池大小
                limit_per_host=30,   # 每個 host 最多 30 個連接
                ttl_dns_cache=300    # DNS 快取 5 分鐘
            )
        )
    
    try:
        yield self._http_session
    except asyncio.TimeoutError:
        logger.error("❌ HTTP 請求超時，正在關閉連接")
        await self._http_session.close()
        self._http_session = None
        raise
```

**預期改進:**
- ✅ 防止無限期等待
- ⬇️ 錯誤恢復時間 **減少 50%**

**實現難度:** ⭐⭐ (簡單)

---

### 優先級 4️⃣：數據處理優化

#### 4.1 **JSON 序列化優化** 🟡 MEDIUM

**問題:** 大型 JSON 響應的重複序列化和格式化

**當前代碼:**
```python
def _format_json_for_logging(self, data: Any, indent: int = 2) -> str:
    """每次都重新格式化大型 JSON"""
    return json.dumps(data, indent=indent, ensure_ascii=False)
```

**建議方案:**
```python
# ✅ 使用 simplejson 和流式處理
import simplejson

class OptimizedJsonHandler:
    """優化的 JSON 處理"""
    
    @staticmethod
    def dump_minimal(data: Dict) -> str:
        """最小化輸出（生產環境）"""
        return simplejson.dumps(data, separators=(',', ':'), ensure_ascii=False)
    
    @staticmethod
    def dump_pretty(data: Dict, truncate_length: int = 1000) -> str:
        """美化輸出，截斷大字段（調試）"""
        def truncate_dict(obj):
            if isinstance(obj, dict):
                return {k: truncate_dict(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [truncate_dict(item) for item in obj[:10]]  # 限制列表大小
            elif isinstance(obj, str) and len(obj) > truncate_length:
                return obj[:truncate_length] + "..."
            return obj
        
        truncated = truncate_dict(data)
        return simplejson.dumps(truncated, indent=2, ensure_ascii=False)
    
    @staticmethod
    async def stream_write(data: Dict, file_path: str) -> None:
        """非同步流式寫入大型 JSON"""
        import aiofiles
        
        async with aiofiles.open(file_path, 'w') as f:
            await f.write(simplejson.dumps(data))
```

**預期改進:**
- ⬇️ JSON 序列化時間 **減少 30-40%**
- ⬇️ 內存使用 **減少 20%**

**實現難度:** ⭐⭐ (簡單)

---

#### 4.2 **回應壓縮** 🟡 MEDIUM

**問題:** 大型回應未壓縮，浪費網路頻寬

**建議方案:**
```python
# ✅ 在 app.py 添加 gzip 中介軟體
from aiohttp_compress import GZipMiddleware

def init_func(argv):
    APP = web.Application(
        middlewares=[
            aiohttp_error_middleware,
            GZipMiddleware(minimum_size=1024)  # 1KB 以上進行壓縮
        ]
    )
    # ...
```

**預期改進:**
- ⬇️ 網路傳輸 **減少 70-80%**（取決於內容）
- ⬆️ 用戶體驗改善（更快的加載）

**實現難度:** ⭐ (非常簡單)

---

### 優先級 5️⃣：監控和診斷

#### 5.1 **效能追蹤儀表板** 🟡 MEDIUM

**建議方案:**
```python
# ✅ 建立效能指標端點
from datetime import datetime

async def get_performance_metrics(request: web.Request) -> web.Response:
    """獲取效能指標 JSON"""
    stats = GENIE_SERVICE.metrics.get_stats()
    
    return web.json_response({
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'metrics': stats,
        'sessions': {
            'active': len(BOT.session_manager.user_sessions),
            'cached': len(BOT._user_context_cache),
        },
        'memory': {
            'usage_mb': get_memory_usage(),
            'connections': GENIE_SERVICE._http_session.connector.limit if GENIE_SERVICE._http_session else 0,
        }
    })

# 在 init_func 中添加路由
def init_func(argv):
    APP = web.Application(middlewares=[aiohttp_error_middleware])
    APP.router.add_get("/api/metrics", get_performance_metrics)
    # ...
```

**預期改進:**
- ✅ 實時性能可視化
- ✅ 快速識別瓶頸

**實現難度:** ⭐⭐ (簡單)

---

## 📈 優化效果預估

| 優化項 | 影響 | 難度 | 預期改善 |
|------|------|------|--------|
| 異步日誌寫入 | 高 | 中 | P95 延遲 ↓ 15-20% |
| 日誌採樣 | 中 | 低 | 日誌輸出 ↓ 99% |
| 會話自動過期 | 高 | 中 | 內存使用 ↓ 60-80% |
| 快取動態調整 | 中 | 中 | 命中率 ↑ 10-15% |
| 請求批量化 | 高 | 高 | 吞吐量 ↑ 30-50% |
| 連接超時配置 | 高 | 低 | 錯誤恢復 ↓ 50% |
| JSON 序列化優化 | 中 | 低 | 序列化時間 ↓ 30-40% |
| 回應壓縮 | 中 | 低 | 網路傳輸 ↓ 70-80% |

---

## 🎯 建議實施計劃

### **第 1 週**（快速勝利）
- [ ] 實現日誌採樣（15 分鐘）
- [ ] 添加連接超時配置（30 分鐘）
- [ ] 部署 gzip 壓縮（10 分鐘）
- [ ] 創建效能指標端點（1 小時）

### **第 2-3 週**（核心改進）
- [ ] 實現會話自動過期清理（2-3 小時）
- [ ] 異步日誌寫入（2-3 小時）
- [ ] JSON 序列化優化（1-2 小時）

### **第 4-6 週**（高級優化）
- [ ] 請求批量化（4-6 小時）
- [ ] 動態快取調整（2-3 小時）
- [ ] 性能測試和調優（3-4 小時）

---

## 🧪 效能測試方案

```python
# ✅ 性能基準測試
import time
import statistics

async def benchmark():
    """運行效能基準測試"""
    durations = []
    
    for i in range(1000):
        start = time.time()
        # 模擬查詢
        await GENIE_SERVICE.ask(
            "test query",
            space_id=CONFIG.SPACE_ID,
            user_session=mock_session
        )
        durations.append(time.time() - start)
    
    print(f"""
    === 效能基準測試結果 ===
    平均: {statistics.mean(durations):.2f}s
    中位數: {statistics.median(durations):.2f}s
    P95: {sorted(durations)[int(len(durations)*0.95)]:.2f}s
    P99: {sorted(durations)[int(len(durations)*0.99)]:.2f}s
    """)
```

---

## 📝 實施檢查清單

- [ ] 評估當前效能基準
- [ ] 實施第 1 週的快速勝利
- [ ] 監控改進效果
- [ ] 逐步實施進階優化
- [ ] 定期性能基準測試
- [ ] 文檔化優化變更
- [ ] 團隊培訓（最佳實踐）

---

## 📚 參考資源

- [aiohttp 性能調優](https://docs.aiohttp.org/en/stable/client_advanced.html)
- [Python 性能最佳實踐](https://realpython.com/python-performance/)
- [非同步 Python 模式](https://docs.python.org/3/library/asyncio.html)
- [Databricks SDK 性能](https://docs.databricks.com/en/sdk-guide/index.html)

---

**完成時間:** 2026年1月30日  
**下一步:** 選擇優先級 1️⃣ 的項目開始實施
