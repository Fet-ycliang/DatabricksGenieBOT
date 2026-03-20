# Azure Application Insights 整合指南

**狀態**: ⏸️ 待實施（部署到 Azure 生產環境時）
**優先級**: 中（生產環境必要）
**預計時間**: 2-3 小時

---

## 📋 目錄

1. [什麼是 Application Insights](#什麼是-application-insights)
2. [為什麼需要它](#為什麼需要它)
3. [可以追蹤什麼](#可以追蹤什麼)
4. [整合方式](#整合方式)
5. [實施步驟](#實施步驟)
6. [監控儀表板](#監控儀表板)

---

## 什麼是 Application Insights

Azure Application Insights 是 Microsoft Azure 的**應用程式效能監控（APM）服務**，提供：

- 🔍 **即時監控**：追蹤每個請求的效能
- 📊 **遙測數據**：自動收集 CPU、記憶體、請求數等指標
- 🐛 **錯誤追蹤**：自動捕獲異常和堆疊追蹤
- 📈 **自訂指標**：追蹤業務相關的 KPI
- 🚨 **警報系統**：設定閾值並在超過時通知
- 📉 **依賴項追蹤**：監控外部 API 調用（Databricks、Graph API）

---

## 為什麼需要它

### 當前限制（沒有 Application Insights）

❌ **無法回答的問題**：
- Bot 的平均回應時間是多少？
- 有多少使用者在使用？
- Databricks API 的失敗率是多少？
- 哪些查詢最慢？
- 記憶體使用趨勢如何？
- 是否有記憶體洩漏？

❌ **當前監控方式的問題**：
- 只能看到本地日誌（`bot_debug.log`）
- 無法跨時間分析趨勢
- 手動分析日誌耗時
- 無法即時收到警報

### 有 Application Insights 後

✅ **可以回答**：
- ✅ 過去 24 小時的平均回應時間：**1.2 秒**
- ✅ 活躍使用者數：**25 人**
- ✅ Databricks API 成功率：**98.5%**
- ✅ 最慢的查詢類型：**複雜的 JOIN 查詢（3.5 秒）**
- ✅ 記憶體使用趨勢：**穩定在 500MB**
- ✅ 快取命中率：**62%**

✅ **自動警報**：
- 錯誤率超過 5% → 發送 Email/Teams 通知
- 回應時間超過 5 秒 → 發送警報
- 記憶體使用超過 80% → 發送警報

---

## 可以追蹤什麼

### 1. HTTP 請求（自動）

| 端點 | 追蹤內容 |
|------|---------|
| `/api/messages` | Bot 訊息處理時間、成功率 |
| `/api/health` | 健康檢查回應時間 |
| `/api/genie/*` | Genie 測試端點效能 |

**自動收集的指標**：
- 請求數量
- 回應時間（平均、P50、P95、P99）
- HTTP 狀態碼分布
- 失敗率

### 2. 依賴項（自動）

| 依賴項 | 追蹤內容 |
|--------|---------|
| Databricks Genie API | 調用次數、延遲、失敗率 |
| Microsoft Graph API | SSO 調用效能 |
| 外部 HTTP 請求 | 所有 httpx 調用 |

### 3. 異常（自動）

Application Insights 自動捕獲所有未處理的異常：

```python
try:
    result = await genie_service.ask(question)
except Exception as e:
    # ✅ 異常自動發送到 Application Insights
    # 包含：異常類型、訊息、堆疊追蹤、請求上下文
    logger.error(f"Query failed: {e}")
    raise
```

### 4. 自訂事件（需手動添加）

**業務指標**：

```python
from opencensus.ext.azure import metrics_exporter

# 追蹤查詢成功
track_event("genie_query", {
    "user_email": user_email,
    "query_type": "data_analysis",
    "has_chart": True,
    "duration_ms": 1250
})

# 追蹤 SSO 登入
track_event("sso_login", {
    "user_email": email,
    "source": "jwt_token",  # or "activity" or "graph_api"
    "duration_ms": 5
})

# 追蹤快取效能
track_metric("cache_hit_rate", cache_stats.hit_rate)
track_metric("active_sessions", len(session_manager.sessions))
```

### 5. 效能指標（自動 + 自訂）

**系統指標**（自動）：
- CPU 使用率
- 記憶體使用量
- 網路 I/O
- 磁碟 I/O

**自訂指標**：
- 活躍 session 數量
- 快取大小和命中率
- 查詢佇列長度

---

## 整合方式

### 選項 1：Azure 自動整合（推薦）✅

**優點**：
- ✅ 零代碼變更
- ✅ 5 分鐘完成設定
- ✅ 自動追蹤 HTTP 請求和異常
- ✅ 開箱即用

**缺點**：
- ⚠️ 無法追蹤自訂事件
- ⚠️ 無法追蹤業務指標

**適用場景**：
- 快速開始監控
- 不需要自訂指標
- 只關心基本效能和錯誤

**步驟**：

1. **在 Azure Portal 啟用**：
   ```
   Azure Portal → App Service → Settings → Application Insights → Enable
   ```

2. **選擇或建立 Application Insights 資源**：
   - 建議建立新的資源：`databricks-genie-bot-insights`
   - 區域選擇與 App Service 相同

3. **儲存並重啟**：
   - 點擊 Save
   - 重啟 App Service

4. **驗證**：
   ```bash
   # 發送測試請求
   curl https://your-app.azurewebsites.net/api/health

   # 2-3 分鐘後在 Application Insights 中查看數據
   ```

### 選項 2：手動 SDK 整合（完整功能）

**優點**：
- ✅ 完整控制遙測數據
- ✅ 可追蹤自訂事件和指標
- ✅ 更詳細的業務分析

**缺點**：
- ⚠️ 需要修改代碼
- ⚠️ 需要約 2-3 小時實施

**適用場景**：
- 需要追蹤業務 KPI
- 需要深入的效能分析
- 生產環境長期使用

**步驟詳見下節**。

---

## 實施步驟（選項 2：手動整合）

### 步驟 1：安裝依賴

```bash
# 添加到 pyproject.toml
[project]
dependencies = [
    "opencensus-ext-azure>=1.1.13",
    "opencensus-ext-flask>=0.8.0",  # 如果使用 Flask
    "opencensus-ext-logging>=0.1.1",
]

# 安裝
uv sync
```

### 步驟 2：配置環境變數

```bash
# .env
APPLICATIONINSIGHTS_CONNECTION_STRING="InstrumentationKey=your-key-here;IngestionEndpoint=https://..."
```

**如何取得 Connection String**：
1. Azure Portal → Application Insights 資源
2. Overview → Essentials → Connection String
3. 複製並貼到 `.env`

### 步驟 3：初始化 Application Insights

創建新文件 `app/core/telemetry.py`：

```python
"""
Application Insights 遙測配置
"""

import os
import logging
from typing import Optional
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure import metrics_exporter
from opencensus.stats import aggregation as aggregation_module
from opencensus.stats import measure as measure_module
from opencensus.stats import stats as stats_module
from opencensus.stats import view as view_module
from opencensus.tags import tag_map as tag_map_module

logger = logging.getLogger(__name__)

_metrics_exporter: Optional[metrics_exporter.MetricsExporter] = None
_is_initialized = False


def initialize_application_insights():
    """初始化 Application Insights"""
    global _metrics_exporter, _is_initialized

    if _is_initialized:
        return

    conn_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")

    if not conn_string:
        logger.warning("⚠️ APPLICATIONINSIGHTS_CONNECTION_STRING 未設定，跳過 Application Insights 初始化")
        return

    try:
        # 設定日誌處理器
        root_logger = logging.getLogger()
        root_logger.addHandler(
            AzureLogHandler(connection_string=conn_string)
        )

        # 設定指標導出器
        _metrics_exporter = metrics_exporter.new_metrics_exporter(
            connection_string=conn_string
        )

        stats = stats_module.stats
        view_manager = stats.view_manager
        view_manager.register_exporter(_metrics_exporter)

        _is_initialized = True
        logger.info("✅ Application Insights 已初始化")

    except Exception as e:
        logger.error(f"❌ Application Insights 初始化失敗: {e}")


def track_event(name: str, properties: dict = None):
    """追蹤自訂事件"""
    if not _is_initialized:
        return

    try:
        from opencensus.ext.azure.trace_exporter import AzureExporter
        from opencensus.trace import tracer as tracer_module

        tracer = tracer_module.Tracer(exporter=AzureExporter(
            connection_string=os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
        ))

        with tracer.span(name=name):
            if properties:
                for key, value in properties.items():
                    tracer.add_attribute_to_current_span(key, str(value))
    except Exception as e:
        logger.debug(f"Failed to track event {name}: {e}")


def track_metric(name: str, value: float, properties: dict = None):
    """追蹤自訂指標"""
    if not _is_initialized:
        return

    try:
        stats = stats_module.stats
        measure = measure_module.MeasureFloat(name, name, "")

        mmap = stats.stats_recorder.new_measurement_map()
        mmap.measure_float_put(measure, value)

        if properties:
            tmap = tag_map_module.TagMap()
            for key, val in properties.items():
                tmap.insert(key, str(val))
            mmap.record(tmap)
        else:
            mmap.record()
    except Exception as e:
        logger.debug(f"Failed to track metric {name}: {e}")
```

### 步驟 4：在應用程式啟動時初始化

修改 `app/main.py`：

```python
from app.core.telemetry import initialize_application_insights

@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理"""
    # 初始化 Application Insights
    initialize_application_insights()

    # ... 其他初始化 ...

    yield

    # ... 清理 ...
```

### 步驟 5：添加自訂追蹤

**在 Genie 查詢中追蹤**（`app/services/genie.py`）：

```python
from app.core.telemetry import track_event, track_metric

async def ask(self, question: str, user_email: str):
    start_time = time.time()

    try:
        result = await self._execute_query(question, user_email)
        duration_ms = (time.time() - start_time) * 1000

        # 追蹤成功查詢
        track_event("genie_query_success", {
            "user_email": user_email,
            "query_length": len(question),
            "duration_ms": duration_ms,
            "has_chart": result.get("has_chart", False)
        })

        # 追蹤查詢延遲
        track_metric("genie_query_duration_ms", duration_ms)

        return result

    except Exception as e:
        track_event("genie_query_failed", {
            "user_email": user_email,
            "error_type": type(e).__name__,
            "error_message": str(e)
        })
        raise
```

**在 Session Manager 中追蹤**（`app/utils/session_manager.py`）：

```python
from app.core.telemetry import track_metric

async def cleanup_expired_sessions(self) -> int:
    removed_count = await self._cleanup_logic()

    # 追蹤 session 統計
    track_metric("active_sessions", len(self._sessions))
    track_metric("expired_sessions_removed", removed_count)

    return removed_count
```

**在快取中追蹤**（`app/utils/cache_utils.py`）：

```python
from app.core.telemetry import track_metric

def get(self, key: str) -> Optional[Any]:
    if key not in self._cache:
        self.stats.record_miss()
        track_metric("cache_miss", 1)
        return None

    # ... 檢查過期 ...

    self.stats.record_hit()
    track_metric("cache_hit", 1)
    track_metric("cache_hit_rate", self.stats.hit_rate)

    return value
```

### 步驟 6：測試

```python
# 本地測試（需要有效的 Connection String）
import os
os.environ["APPLICATIONINSIGHTS_CONNECTION_STRING"] = "your-connection-string"

from app.core.telemetry import initialize_application_insights, track_event

initialize_application_insights()
track_event("test_event", {"message": "Hello from local"})

# 2-3 分鐘後在 Azure Portal 中查看
```

---

## 監控儀表板

### 在 Azure Portal 中查看

#### 1. **Overview（概覽）**
- 請求數量（過去 24 小時）
- 平均回應時間
- 失敗請求百分比
- 伺服器回應時間

#### 2. **Performance（效能）**
- 操作列表（最慢的端點）
- 依賴項延遲（Databricks API、Graph API）
- 時間線圖表

#### 3. **Failures（失敗）**
- 異常類型分布
- 失敗的操作
- 詳細堆疊追蹤

#### 4. **Metrics（指標）**
- 自訂指標視覺化
- 建立自訂圖表
- 比較不同時間段

#### 5. **Logs（日誌）**

使用 Kusto 查詢語言（KQL）：

```kql
// 查詢過去 24 小時的所有請求
requests
| where timestamp > ago(24h)
| summarize count() by name, resultCode
| order by count_ desc

// 查找最慢的查詢
requests
| where name == "POST /api/messages"
| where timestamp > ago(1h)
| top 10 by duration desc

// 錯誤分析
exceptions
| where timestamp > ago(24h)
| summarize count() by type, outerMessage
| order by count_ desc

// 自訂事件分析
customEvents
| where name == "genie_query_success"
| where timestamp > ago(24h)
| summarize avg_duration = avg(todouble(customDimensions.duration_ms))
    by user = tostring(customDimensions.user_email)
| order by avg_duration desc
```

### 設定警報

**範例：回應時間過長警報**

1. Application Insights → Alerts → New alert rule
2. 條件：
   - Signal: Response time
   - Threshold: > 5 seconds
   - Evaluation: Every 5 minutes
3. Actions:
   - Send email to: admin@company.com
   - Send Teams notification
4. 名稱：`High Response Time Alert`

**範例：錯誤率過高警報**

1. 條件：
   - Signal: Failed requests
   - Threshold: > 5% of total requests
   - Time window: 15 minutes
2. Actions:
   - Send email
   - Create incident in Azure DevOps

---

## 成本考量

### Azure Application Insights 定價

**免費層**：
- 前 5GB/月 資料：免費
- 適合小型應用或測試環境

**標準層**：
- $2.88 USD / GB（超過 5GB）
- 資料保留：90 天（預設）

### 預估成本（Databricks Genie Bot）

假設：
- 50 個活躍使用者
- 每天 500 個查詢
- 每個請求約 10KB 遙測數據

**每月數據量**：
- 500 查詢/天 × 30 天 = 15,000 請求
- 15,000 × 10KB = 150MB ≈ **0.15GB/月**

**每月成本**：**免費**（遠低於 5GB 免費額度）

---

## 總結

### 何時整合？

✅ **建議整合**：
- 部署到 Azure 生產環境
- 有多個使用者
- 需要監控和診斷

⏸️ **暫時不需要**：
- 本地開發
- POC 階段
- 個人測試

### 推薦方式

**階段 1：快速開始**（5 分鐘）
- 使用 Azure 自動整合
- 無需修改代碼
- 立即獲得基本監控

**階段 2：深入追蹤**（部署後 1-2 週）
- 根據實際需求
- 添加自訂事件和指標
- 建立業務儀表板

### 參考資源

- [Application Insights 官方文檔](https://learn.microsoft.com/azure/azure-monitor/app/app-insights-overview)
- [Python SDK 文檔](https://learn.microsoft.com/azure/azure-monitor/app/opencensus-python)
- [KQL 查詢語法](https://learn.microsoft.com/azure/data-explorer/kusto/query/)
