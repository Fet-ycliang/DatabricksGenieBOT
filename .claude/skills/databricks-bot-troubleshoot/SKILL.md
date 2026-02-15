---
name: databricks-bot-troubleshoot
description: |
  故障排除助手。診斷常見錯誤（Databricks API、Bot Framework、Azure、HTTP）。
  觸發：「錯誤」「debug」「troubleshoot」「問題」「失敗」「不work」
  快速找到問題原因和解決方案。
---

# DatabricksGenieBOT Troubleshoot Helper

診斷和解決常見問題，提供快速修復建議。

## 常見錯誤診斷

### 1. Databricks API 錯誤

#### 錯誤: 401 Unauthorized

```
httpx.HTTPStatusError: 401 Unauthorized
```

**原因**：
- `DATABRICKS_TOKEN` 無效或過期
- Token 沒有正確權限

**解決方案**：
```bash
# 1. 檢查環境變數
echo $DATABRICKS_TOKEN

# 2. 生成新 token
# Databricks → Settings → User Settings → Access Tokens

# 3. 更新 .env
DATABRICKS_TOKEN=dapi_new_token_here

# 4. 重啟應用程式
```

---

#### 錯誤: 404 Space Not Found

```
錯誤: Space '01234567890abcde' not found
```

**原因**：
- `DATABRICKS_SPACE_ID` 錯誤
- Space 已被刪除
- Token 沒有 Space 存取權限

**解決方案**：
```bash
# 1. 檢查 Space ID
curl -X GET \
  "${DATABRICKS_HOST}/api/2.0/genie/spaces" \
  -H "Authorization: Bearer ${DATABRICKS_TOKEN}"

# 2. 更新正確的 Space ID
DATABRICKS_SPACE_ID=正確的_space_id

# 3. 確認權限
# Databricks → Genie → Spaces → 檢查存取權限
```

---

#### 錯誤: Rate Limit Exceeded

```
HTTPStatusError: 429 Too Many Requests
```

**原因**：
- API 呼叫頻率過高
- 超過 Databricks rate limit

**解決方案**：
```python
# 實作重試機制
import time
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def call_genie_api():
    # API 呼叫邏輯
    pass

# 或手動處理
try:
    response = await client.post(url, ...)
except httpx.HTTPStatusError as e:
    if e.response.status_code == 429:
        retry_after = int(e.response.headers.get('Retry-After', 60))
        await asyncio.sleep(retry_after)
        # 重試
```

---

### 2. Bot Framework 錯誤

#### 錯誤: Bot 無法啟動

```
aiohttp.ClientConnectorError: Cannot connect to host
```

**原因**：
- Port 被佔用
- 防火牆阻擋
- `APP_ID` / `APP_PASSWORD` 錯誤

**解決方案**：
```bash
# 1. 檢查 port 是否被佔用
netstat -ano | findstr :3978   # Windows
lsof -i :3978                  # Linux/Mac

# 2. 更換 port
PORT=8000 uv run uvicorn app.main:app

# 3. 檢查 Bot 配置
# Azure → Bot Service → Configuration → 檢查 App ID/Password
```

---

#### 錯誤: SSO 認證失敗

```
BotFrameworkAdapterError: Invalid token
```

**原因**：
- OAuth Connection 未正確設定
- Token 過期
- Scope 不正確

**解決方案**：
```bash
# 1. 檢查 OAuth Connection
# Azure → Bot Service → OAuth Connection Settings

# 2. 確認 Scope
# 需要: email, profile, openid, User.Read

# 3. 測試 Token
# Bot Framework Emulator → Settings → Test OAuth

# 4. 清除快取重新登入
```

---

#### 錯誤: Activity Handler 沒有回應

```
TurnContext.send_activity() 沒有執行
```

**原因**：
- 非同步函式沒有 await
- 異常被靜默處理

**解決方案**：
```python
# 錯誤寫法 ❌
def on_message_activity(self, turn_context: TurnContext):
    turn_context.send_activity("Hello")  # 缺少 await

# 正確寫法 ✅
async def on_message_activity(self, turn_context: TurnContext):
    await turn_context.send_activity("Hello")

# 加上錯誤處理
async def on_message_activity(self, turn_context: TurnContext):
    try:
        await turn_context.send_activity("Hello")
    except Exception as e:
        logger.error(f"發送失敗: {e}", exc_info=True)
        raise
```

---

### 3. Azure 部署錯誤

#### 錯誤: Application Insights 連接失敗

```
azure.monitor.opentelemetry: Connection refused
```

**原因**：
- Connection String 錯誤
- 防火牆阻擋

**解決方案**：
```bash
# 1. 檢查 Connection String
# Azure → Application Insights → Overview → Connection String

# 2. 更新環境變數
APPLICATIONINSIGHTS_CONNECTION_STRING="InstrumentationKey=..."

# 3. 如果是防火牆問題
# 暫時停用 Application Insights
# 或設定 firewall rules
```

---

#### 錯誤: Web App 部署失敗

```
ERROR: Site failed to start
```

**原因**：
- requirements.txt 依賴問題
- Port 配置錯誤
- 啟動命令錯誤

**解決方案**：
```bash
# 1. 檢查日誌
az webapp log tail --name <app-name> --resource-group <rg-name>

# 2. 檢查啟動命令
# Azure → Web App → Configuration → Startup Command
# 應該是：uvicorn app.main:app --host 0.0.0.0 --port $PORT

# 3. 確認 requirements.txt
pip freeze > requirements.txt

# 4. 本地測試
docker build -t test-bot .
docker run -p 8000:8000 test-bot
```

---

### 4. HTTP / 網路錯誤

#### 錯誤: Connection Timeout

```
httpx.ConnectTimeout: Connection timeout
```

**原因**：
- 網路問題
- Timeout 設定太短
- DNS 解析失敗

**解決方案**：
```python
# 增加 timeout
client = httpx.AsyncClient(
    timeout=httpx.Timeout(
        connect=10.0,  # 連接超時（增加）
        read=30.0,     # 讀取超時
        write=10.0,
        pool=60.0
    )
)

# 檢查網路連接
import socket
try:
    socket.create_connection(("databricks.com", 443), timeout=5)
    print("網路正常")
except Exception as e:
    print(f"網路問題: {e}")
```

---

#### 錯誤: SSL Certificate Error

```
ssl.SSLCertVerificationError: certificate verify failed
```

**原因**：
- 公司代理或防火牆
- 自簽證書

**解決方案**：
```python
# ⚠️ 僅用於開發環境
import httpx

client = httpx.AsyncClient(verify=False)  # 跳過 SSL 驗證

# 生產環境解決方案
# 1. 安裝公司根證書
# 2. 設定環境變數
# export REQUESTS_CA_BUNDLE=/path/to/ca-bundle.crt
```

---

### 5. 記憶體和效能問題

#### 錯誤: Memory Error / OOM

```
MemoryError: Out of memory
```

**原因**：
- 會話物件沒有清理
- 快取無上限
- 大量資料沒有分頁

**解決方案**：
```python
# 1. 實作會話清理
from app.utils.session_manager import cleanup_expired_sessions

# 定期清理（在背景任務）
asyncio.create_task(cleanup_expired_sessions(timeout_hours=4))

# 2. 限制快取大小
from app.utils.cache_utils import SimpleCache

cache = SimpleCache(max_size=100, ttl_seconds=3600)

# 3. 分頁處理大量資料
def process_large_dataset(data):
    chunk_size = 100
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i+chunk_size]
        yield chunk
```

---

#### 錯誤: 回應速度慢

```
查詢超過 5 秒才回應
```

**診斷步驟**：
```python
import time
import logging

logger = logging.getLogger(__name__)

async def diagnose_performance():
    # 1. 測量 API 呼叫時間
    start = time.time()
    response = await genie_service.query(...)
    elapsed = time.time() - start
    logger.info(f"Genie API 耗時: {elapsed:.2f}s")

    # 2. 檢查是否使用快取
    if cache.get(query_key):
        logger.info("快取命中")
    else:
        logger.info("快取未命中")

    # 3. 檢查連接池
    # 確認使用 httpx.AsyncClient 重用連接
```

**優化方案**：
- 啟用快取（見 databricks-bot-optimize skill）
- 使用 HTTP 連接池
- 實作請求批次處理

---

### 6. 測試錯誤

#### 錯誤: Async Test 失敗

```
RuntimeWarning: coroutine was never awaited
```

**原因**：
- 忘記 await
- 沒有使用 asyncio.run()

**解決方案**：
```python
# 錯誤 ❌
def test_async_function():
    result = my_async_function()  # 沒有 await
    assert result == "expected"

# 正確 ✅
def test_async_function():
    async def run_test():
        result = await my_async_function()
        return result

    result = asyncio.run(run_test())
    assert result == "expected"
```

---

#### 錯誤: Mock 不生效

```
Mock 被呼叫但測試失敗
```

**原因**：
- Mock 路徑錯誤
- Mock 在 import 之後才設定

**解決方案**：
```python
# 錯誤：Mock 錯誤的路徑 ❌
with patch('httpx.AsyncClient') as mock:
    from app.services.feature import FeatureService
    service = FeatureService()  # 還是使用真實的 httpx

# 正確：Mock 正確的路徑 ✅
with patch('app.services.feature.httpx.AsyncClient') as mock:
    from app.services.feature import FeatureService
    service = FeatureService()  # 使用 Mock
```

---

## 診斷工具

### 1. 日誌分析

```bash
# 查看最近的錯誤
grep "ERROR" app.log | tail -20

# 查看特定時間範圍
grep "2024-02-16" app.log | grep "ERROR"

# 統計錯誤類型
grep "ERROR" app.log | awk '{print $5}' | sort | uniq -c
```

### 2. 效能分析

```python
# 簡單的效能分析
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# 執行程式碼
await my_function()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumtime')
stats.print_stats(10)
```

### 3. 記憶體分析

```python
import psutil
import os

process = psutil.Process(os.getpid())
memory_info = process.memory_info()

print(f"記憶體使用: {memory_info.rss / 1024 / 1024:.2f} MB")
```

### 4. 健康檢查

```bash
# 呼叫健康檢查端點
curl http://localhost:8000/api/health

# 預期回應
{
  "status": "healthy",
  "databricks": "connected",
  "timestamp": "2024-02-16T10:30:00Z"
}
```

---

## 除錯最佳實踐

### 1. 詳細日誌

```python
import logging

logger = logging.getLogger(__name__)

# 記錄關鍵資訊
logger.info(f"處理請求: user_id={user_id}, query={query}")

# 記錄錯誤（包含 stack trace）
try:
    result = await service.process()
except Exception as e:
    logger.error(f"處理失敗: {e}", exc_info=True)  # ← exc_info=True
    raise
```

### 2. 錯誤重現

```python
# 建立最小可重現案例
async def reproduce_error():
    """重現錯誤的最小案例"""
    service = GenieService()
    try:
        result = await service.query("specific query that fails")
        print(f"結果: {result}")
    except Exception as e:
        print(f"錯誤: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(reproduce_error())
```

### 3. 使用 Debugger

```python
# 在程式碼中加入中斷點
import pdb; pdb.set_trace()  # Python debugger

# 或使用 IDE debugger（VS Code, PyCharm）
```

---

## 快速故障排除檢查清單

Bot 無法啟動：
- [ ] 檢查環境變數（.env 檔案）
- [ ] 檢查 port 是否被佔用
- [ ] 檢查依賴是否安裝（`uv sync`）
- [ ] 查看日誌檔案

API 呼叫失敗：
- [ ] 檢查 Token 是否有效
- [ ] 檢查網路連接
- [ ] 檢查 API endpoint URL
- [ ] 查看 HTTP status code

Bot 沒有回應：
- [ ] 檢查 async/await 是否正確
- [ ] 檢查錯誤處理
- [ ] 查看 Bot Framework Emulator 日誌
- [ ] 確認 Activity Handler 註冊

效能問題：
- [ ] 檢查是否使用快取
- [ ] 檢查 HTTP 連接池配置
- [ ] 查看記憶體使用
- [ ] 分析慢查詢

---

## 參考資源

- [docs/troubleshooting.md](../../../docs/troubleshooting.md) - 完整故障排除指南
- [Databricks API 文檔](https://docs.databricks.com/api/)
- [Bot Framework 故障排除](https://docs.microsoft.com/en-us/azure/bot-service/bot-service-troubleshoot)
