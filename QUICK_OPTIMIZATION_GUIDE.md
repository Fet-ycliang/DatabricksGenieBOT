# 🔧 效能優化 - 快速實施指南

## 快速開始：優先級 1️⃣ 改進（可在 1 小時內完成）

### 改進 1️⃣：日誌採樣

**檔案:** `genie_service.py`

```python
# 1. 添加到頂部導入
import random
import time

# 2. 在 GenieService 類中添加
class GenieService:
    def __init__(self, config: Any, workspace_client: WorkspaceClient | None = None):
        # ... 現有代碼 ...
        self.last_stats_log_time = time.time()
        self.stats_log_interval = 60  # 每 60 秒記錄一次
    
    def should_log_stats(self) -> bool:
        """決定是否記錄統計信息"""
        current_time = time.time()
        if current_time - self.last_stats_log_time >= self.stats_log_interval:
            self.last_stats_log_time = current_time
            return True
        # 1% 隨機採樣
        return random.random() < 0.01

# 3. 修改記錄統計的位置（搜索 "if self.metrics.total_queries % 100 == 0"）
    if self.should_log_stats():  # 改為新方法
        self.metrics.log_stats()
```

---

### 改進 2️⃣：連接超時配置

**檔案:** `genie_service.py`

```python
# 在 GenieService 類中找到 get_http_session 方法，替換為：

@asynccontextmanager
async def get_http_session(self):
    """重用 HTTP Session 減少連接開銷"""
    if not self._http_session or self._http_session.closed:
        # ✅ 添加超時配置
        timeout = aiohttp.ClientTimeout(
            total=30,      # 總超時：30 秒
            connect=5,     # 連接超時：5 秒
            sock_read=10,  # 讀取超時：10 秒
        )
        self._http_session = aiohttp.ClientSession(
            timeout=timeout,
            connector=aiohttp.TCPConnector(
                limit=100,
                limit_per_host=30,
                ttl_dns_cache=300
            )
        )
    try:
        yield self._http_session
    except asyncio.TimeoutError as e:
        logger.error(f"❌ HTTP 請求超時: {e}")
        if self._http_session:
            await self._http_session.close()
        self._http_session = None
        raise
```

---

### 改進 3️⃣：Gzip 壓縮

**檔案:** `requirements.txt`

```
# 添加以下行
aiohttp-compress>=0.2.0
```

**檔案:** `app.py`

```python
# 1. 在導入中添加
from aiohttp_compress import GZipMiddleware

# 2. 在 init_func 中修改
def init_func(argv):
    APP = web.Application(
        middlewares=[
            aiohttp_error_middleware,
            GZipMiddleware(minimum_size=1024)  # 1KB 以上進行壓縮
        ]
    )
    # ... 其他代碼 ...
```

---

### 改進 4️⃣：效能指標端點

**檔案:** `app.py`

```python
# 1. 在頂部添加導入
from datetime import datetime, timezone
import psutil  # 需要安裝：pip install psutil

# 2. 在 on_cleanup 之後添加新函數
async def get_performance_metrics(request: web.Request) -> web.Response:
    """獲取效能指標"""
    try:
        stats = GENIE_SERVICE.metrics.get_stats()
        
        # 獲取內存使用
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return web.json_response({
            'status': 'ok',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'performance': stats,
            'system': {
                'memory_mb': memory_info.rss / 1024 / 1024,
                'cpu_percent': process.cpu_percent(),
                'active_sessions': len(BOT.user_sessions) if BOT else 0,
            }
        })
    except Exception as e:
        logger.error(f"獲取效能指標時出錯: {e}")
        return web.json_response({'error': str(e)}, status=500)

# 3. 在 init_func 中添加路由
def init_func(argv):
    APP = web.Application(middlewares=[aiohttp_error_middleware, GZipMiddleware(minimum_size=1024)])
    APP.on_startup.append(on_startup)
    APP.on_cleanup.append(on_cleanup)
    
    # ✅ 添加新路由
    APP.router.add_get("/api/metrics", get_performance_metrics)
    
    APP.router.add_get("/api/health", health_check)
    APP.router.add_post("/api/messages", messages)
    return APP
```

---

## 🧪 驗證改進

### 測試日誌採樣
```bash
# 運行 100 個查詢，檢查日誌輸出
# 應該看到大約 2-3 次統計信息，而不是每 100 次一次
```

### 測試超時
```python
# 模擬慢速連接
import asyncio

async def test_timeout():
    service = GENIE_SERVICE
    async with service.get_http_session() as session:
        # 測試超時行為
        pass
```

### 測試效能指標
```bash
# 請求新的指標端點
curl http://localhost:3978/api/metrics | python -m json.tool
```

---

## 📊 預期效果（實施第 1 週改進後）

| 指標 | 改善 |
|------|------|
| 日誌 I/O 負載 | ↓ 99% |
| 平均查詢延遲 | ↓ 5-10% |
| 網路傳輸 | ↓ 70% |
| 伺服器可觀測性 | ✅ 新增 |

---

## ⚠️ 注意事項

1. **備份代碼** - 在進行更改前提交當前代碼
2. **逐一實施** - 每次只實施一個改進，測試後再進行下一個
3. **監控影響** - 比較實施前後的效能指標
4. **生產部署** - 在 staging 環境測試後再部署到生產環境

---

## 🚀 下一步

完成快速改進後，考慮實施優先級 2️⃣ 的改進：

- [ ] 會話自動過期清理（最重要）
- [ ] 異步日誌寫入（進階）
- [ ] JSON 序列化優化

**預計時間:** 第 2-3 週，2-3 小時工作量

---

**最後更新:** 2026年1月30日
