# Azure Web App Health Check 配置指南

## 概述

此文件說明如何在 Azure App Service 上配置和使用 health check 機制來監控您的 DatabricksGenieBOT 應用程式。

## 1. 健康檢查端點

### 1.1 `/api/health` 端點 (診斷檢查)

**用途**: 檢查應用程式的整體健康狀態和依賴服務

**HTTP 方法**: GET  
**URL**: `https://<your-app-name>.azurewebsites.net/api/health`

**回應範例** (200 - 健康):
```json
{
  "status": "healthy",
  "timestamp": "2026-01-03T10:30:45.123456+00:00",
  "checks": {
    "app": {
      "status": "up",
      "details": {
        "message": "application running"
      }
    },
    "databricks": {
      "status": "up",
      "details": {
        "message": "Databricks client initialized",
        "space_id": "01f0c69c00351febace9707d33d3c5b3"
      }
    },
    "graph_api": {
      "status": "up",
      "details": {
        "message": "Graph API configured",
        "client_id": "e11ff460..."
      }
    },
    "bot_adapter": {
      "status": "up",
      "details": {
        "message": "BotFrameworkAdapter initialized"
      }
    }
  }
}
```

**回應範例** (503 - 異常):
```json
{
  "status": "unhealthy",
  "timestamp": "2026-01-03T10:30:45.123456+00:00",
  "error": "Databricks connection failed"
}
```

## 2. Azure 入口網站配置

### 2.1 在 Azure 入口網站設置 Health Check

1. 進入 Azure 入口網站
2. 導航到 **App Service** → 您的應用程式 → **Health check**
3. 設置以下值：

| 設定項 | 值 |
|--------|-----|
| Health check path | `/api/health` |
| Number of probes | 10 |
| Interval (seconds) | 60 |

### 2.2 在 Azure 入口網站設置監控告警

1. 導航到 **App Service** → 您的應用程式 → **Alerts** → **New alert rule**
2. 設置告警條件：

```
Resource type: App Service
Condition: Health check status is down
Threshold: 2 consecutive failures
Window size: 5 minutes
```

## 3. 在 web.config 中的配置

```xml
<configuration>
  <system.webServer>
    <!-- Health Check 配置 -->
    <healthCheck path="/api/health" />
    <!-- 其他配置... -->
  </system.webServer>
</configuration>
```

## 4. 使用 Azure CLI 配置

### 4.1 啟用 Health Check

```bash
# 啟用 health check
az webapp config set \
  --resource-group <resource-group-name> \
  --name <app-name> \
  --health-check-path "/api/health"

# 驗證設定
az webapp config show \
  --resource-group <resource-group-name> \
  --name <app-name>
```

### 4.2 查看 Health Check 歷史

```bash
az webapp config diagnostic list \
  --resource-group <resource-group-name> \
  --name <app-name> \
  --query "[?level=='Error']"
```

## 5. 本地測試

### 5.1 測試 Health Check 端點

```bash
# 使用 curl 測試健康檢查
curl -v http://localhost:3978/api/health

# 預期輸出 (200 OK):
# {
#   "status": "healthy",
#   "timestamp": "...",
#   "checks": {...}
# }
```

### 5.2 使用 Python 進行完整測試

```python
import requests
import json

# 健康檢查
print("=== Health Check ===")
response = requests.get("http://localhost:3978/api/health")
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))
```

## 6. 監控和告警

### 6.1 健康檢查指標

Azure 會自動記錄以下指標：

- **健康檢查成功率**: 通過的檢查佔比
- **健康檢查回應時間**: 端點回應延遲（毫秒）
- **實例重啟次數**: 因健康檢查失敗而重啟的次數

### 6.2 在 Application Insights 中監控

```kusto
# Application Insights 查詢
requests
| where url contains "/api/health"
| where timestamp > ago(24h)
| summarize 
    SuccessCount = sum(toint(success)),
    FailureCount = sum(toint(not success)),
    AvgDuration = avg(duration)
    by resultCode
| sort by FailureCount desc
```

### 6.3 設置告警

```bash
# 使用 Azure CLI 創建告警規則
az monitor metrics alert create \
  --resource-group <resource-group-name> \
  --name "HealthCheckFailure" \
  --scopes "/subscriptions/<subscription-id>/resourceGroups/<resource-group>/providers/Microsoft.Web/sites/<app-name>" \
  --condition "avg HealthCheckStatus < 1" \
  --window-size 5m \
  --evaluation-frequency 1m
```

## 7. 故障排除

### 7.1 常見問題

| 問題 | 原因 | 解決方案 |
|------|------|--------|
| Health Check 返回 503 | 依賴服務不可用 | 檢查 Databricks/Graph API 連接 |
| 頻繁的實例重啟 | Health Check 持續失敗 | 檢查應用程式日誌，查看具體的故障原因 |
| 高延遲 (> 10 秒) | 後端服務響應慢 | 檢查 Databricks API 性能，考慮添加超時 |

### 7.2 診斷命令

```bash
# 查看應用程式日誌
az webapp log tail \
  --resource-group <resource-group-name> \
  --name <app-name> \
  --provider "Application Insights"

# 查看實例健康狀態
az webapp show \
  --resource-group <resource-group-name> \
  --name <app-name> \
  --query "state"
```

### 7.3 調試 Health Check

在 app.py 中啟用詳細日誌：

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def health_check(req: Request) -> Response:
    logger.debug("Health check invoked")
    # ...
```

## 8. 最佳實踐

### 8.1 設計建議

- ✅ **輕量級檢查**: Health check 應該快速完成（< 1 秒）
- ✅ **不依賴外部呼叫**: 盡量減少到外部 API 的呼叫
- ✅ **快速失敗**: 如果依賴服務不可用，快速返回失敗
- ✅ **記錄詳細訊息**: 便於故障排除

### 8.2 超時配置

```python
# 在 health check 處理程式中設置超時
async def health_check(req: Request) -> Response:
    try:
        # 用 asyncio.wait_for 設置 5 秒超時
        result = await asyncio.wait_for(
            check_dependencies(),
            timeout=5.0
        )
        return json_response(result)
    except asyncio.TimeoutError:
        return json_response(
            {"status": "unhealthy", "error": "Check timeout"},
            status=503
        )
```

### 8.3 優雅降級

```python
# 即使某些依賴不可用，仍然返回 200
async def health_check(req: Request) -> Response:
    response = HealthCheckResponse("healthy")
    
    # 可選依賴
    if not check_optional_service():
        response.status = "degraded"  # 不是 unhealthy
    
    return json_response(response.to_dict(), status=200)  # 仍然返回 200
```

## 9. 參考資源

- [Azure App Service Health Check 官方文件](https://learn.microsoft.com/azure/app-service/monitor-instances-health-check)
- [Health Endpoint Monitoring Pattern](https://docs.microsoft.com/azure/architecture/patterns/health-endpoint-monitoring)
- [Azure Monitor Application Insights](https://learn.microsoft.com/azure/azure-monitor/app/app-insights-overview)

## 10. 相關檔案

- `health_check.py`: 健康檢查實現模組
- `app.py`: 主應用程式，包含 `/api/health` 路由
- `web.config`: IIS 配置，包含 health check 設定
