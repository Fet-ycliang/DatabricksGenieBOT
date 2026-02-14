---
name: azure-monitor-opentelemetry-py
description: |
  Azure Monitor OpenTelemetry Distro for Python。用於一鍵設定 Application Insights 的自動檢測 (auto-instrumentation)。
  Triggers: "azure-monitor-opentelemetry", "configure_azure_monitor", "Application Insights", "OpenTelemetry distro", "auto-instrumentation".
package: azure-monitor-opentelemetry
---

# Azure Monitor OpenTelemetry Distro for Python

使用 OpenTelemetry 自動檢測進行 Application Insights 的一鍵設定。

## 安裝

```bash
pip install azure-monitor-opentelemetry
```

## 環境變數

```bash
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=xxx;IngestionEndpoint=https://xxx.in.applicationinsights.azure.com/
```

## 快速開始

```python
from azure.monitor.opentelemetry import configure_azure_monitor

# 一行設定 - 從環境變數讀取連接字串
configure_azure_monitor()

# 你的應用程式程式碼...
```

## 明確設定

```python
from azure.monitor.opentelemetry import configure_azure_monitor

configure_azure_monitor(
    connection_string="InstrumentationKey=xxx;IngestionEndpoint=https://xxx.in.applicationinsights.azure.com/"
)
```

## 搭配 Flask

```python
from flask import Flask
from azure.monitor.opentelemetry import configure_azure_monitor

configure_azure_monitor()

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello, World!"

if __name__ == "__main__":
    app.run()
```

## 搭配 Django

```python
# settings.py
from azure.monitor.opentelemetry import configure_azure_monitor

configure_azure_monitor()

# Django settings...
```

## 搭配 FastAPI

```python
from fastapi import FastAPI
from azure.monitor.opentelemetry import configure_azure_monitor

configure_azure_monitor()

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

## 自訂追蹤 (Custom Traces)

```python
from opentelemetry import trace
from azure.monitor.opentelemetry import configure_azure_monitor

configure_azure_monitor()

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("my-operation") as span:
    span.set_attribute("custom.attribute", "value")
    # Do work...
```

## 自訂指標 (Custom Metrics)

```python
from opentelemetry import metrics
from azure.monitor.opentelemetry import configure_azure_monitor

configure_azure_monitor()

meter = metrics.get_meter(__name__)
counter = meter.create_counter("my_counter")

counter.add(1, {"dimension": "value"})
```

## 自訂日誌 (Custom Logs)

```python
import logging
from azure.monitor.opentelemetry import configure_azure_monitor

configure_azure_monitor()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

logger.info("This will appear in Application Insights")
logger.error("Errors are captured too", exc_info=True)
```

## 取樣 (Sampling)

```python
from azure.monitor.opentelemetry import configure_azure_monitor

# 取樣 10% 的請求
configure_azure_monitor(
    sampling_ratio=0.1
)
```

## 雲端角色名稱 (Cloud Role Name)

為 Application Map 設定雲端角色名稱：

```python
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME

configure_azure_monitor(
    resource=Resource.create({SERVICE_NAME: "my-service-name"})
)
```

## 停用特定檢測

```python
from azure.monitor.opentelemetry import configure_azure_monitor

configure_azure_monitor(
    instrumentations=["flask", "requests"]  # 僅啟用這些
)
```

## 啟用 Live Metrics

```python
from azure.monitor.opentelemetry import configure_azure_monitor

configure_azure_monitor(
    enable_live_metrics=True
)
```

## Azure AD 身份驗證

```python
from azure.monitor.opentelemetry import configure_azure_monitor
from azure.identity import DefaultAzureCredential

configure_azure_monitor(
    credential=DefaultAzureCredential()
)
```

## 包含的自動檢測

| 函式庫   | 遙測類型       |
| -------- | -------------- |
| Flask    | Traces (追蹤)  |
| Django   | Traces (追蹤)  |
| FastAPI  | Traces (追蹤)  |
| Requests | Traces (追蹤)  |
| urllib3  | Traces (追蹤)  |
| httpx    | Traces (追蹤)  |
| aiohttp  | Traces (追蹤)  |
| psycopg2 | Traces (追蹤)  |
| pymysql  | Traces (追蹤)  |
| pymongo  | Traces (追蹤)  |
| redis    | Traces (追蹤)  |

## 設定選項

| 參數                  | 描述                                   | 預設值        |
| --------------------- | -------------------------------------- | ------------- |
| `connection_string`   | Application Insights 連接字串          | 來自環境變數  |
| `credential`          | 用於 AAD 身份驗證的 Azure 憑證         | None          |
| `sampling_ratio`      | 取樣率 (0.0 到 1.0)                    | 1.0           |
| `resource`            | OpenTelemetry Resource                 | 自動偵測      |
| `instrumentations`    | 要啟用的檢測清單                       | 全部          |
| `enable_live_metrics` | 啟用 Live Metrics 串流                 | False         |

## 最佳實踐

1. **儘早呼叫 configure_azure_monitor()** — 在匯入被檢測的函式庫之前
2. **使用環境變數** 設定生產環境的連接字串
3. **設定雲端角色名稱** 用於多服務應用程式
4. **啟用取樣** 於高流量應用程式
5. **使用結構化日誌** 以獲得更好的日誌分析查詢體驗
6. **新增自訂屬性** 到 spans 以便於除錯
7. **使用 AAD 身份驗證** 於生產工作負載
