---
name: databricks-bot-dev
description: |
  DatabricksGenieBOT 專案開發助手。提供 FastAPI、Bot Framework、Databricks SDK、
  Azure Identity 和圖表生成的開發模式。基於 pyproject.toml 的技術棧。
  觸發：「新增功能」「建立 API」「新增測試」「FastAPI endpoint」「Bot handler」
---

# DatabricksGenieBOT Developer Assistant

## 專案技術棧（from pyproject.toml）

```toml
核心框架:
- FastAPI >= 0.112.0 (Web 框架)
- Bot Framework SDK >= 4.15.0 (Teams Bot)
- Databricks SDK >= 0.12.0 (資料平台)
- Azure Identity >= 1.15.0 (認證)
- Microsoft Graph Core >= 0.2.0 (M365 整合)

資料與視覺化:
- Matplotlib >= 3.7.0, Seaborn >= 0.12.0 (圖表)
- NumPy >= 1.24.0 (數值運算)
- Pydantic >= 2.0.0 (資料驗證)

Python: >=3.11
```

---

## 快速開發模板

### 1. FastAPI Endpoint (API 端點)

**使用時機**: 建立新的 REST API 端點

```python
"""新功能 API 端點"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import logging

router = APIRouter(prefix="/api/feature", tags=["feature"])
logger = logging.getLogger(__name__)


class FeatureRequest(BaseModel):
    """請求模型"""
    user_id: str = Field(..., description="使用者 ID")
    query: str = Field(..., description="查詢內容")


class FeatureResponse(BaseModel):
    """回應模型"""
    success: bool
    data: dict | None = None
    message: str


@router.post("/process", response_model=FeatureResponse)
async def process_feature(request: FeatureRequest):
    """處理功能請求"""
    try:
        logger.info(f"處理請求: {request.user_id}")

        # TODO: 實作邏輯
        result = {"status": "success"}

        return FeatureResponse(
            success=True,
            data=result,
            message="處理成功"
        )
    except Exception as e:
        logger.error(f"處理失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

**註冊路由** (app/main.py):
```python
from app.api import feature
app.include_router(feature.router)
```

---

### 2. Service Module (服務模組)

**使用時機**: 整合外部 API 或業務邏輯

```python
"""功能服務模組"""
import logging
import httpx
from typing import Optional, Dict, Any
from app.core.config import DefaultConfig
from app.core.exceptions import ServiceError

logger = logging.getLogger(__name__)


class FeatureService:
    """功能服務"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or DefaultConfig.FEATURE_API_KEY
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """取得 HTTP 客戶端（連接池）"""
        if not self._client:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(5.0, read=10.0),
                limits=httpx.Limits(
                    max_keepalive_connections=5,
                    max_connections=10
                )
            )
        return self._client

    async def process(
        self,
        user_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """處理請求"""
        try:
            client = await self._get_client()
            response = await client.post(
                f"{self.endpoint}/process",
                json=data,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise ServiceError(f"API 錯誤: {e.response.text}")
        except Exception as e:
            logger.error(f"服務錯誤: {e}", exc_info=True)
            raise ServiceError(str(e))

    async def close(self):
        """關閉客戶端"""
        if self._client:
            await self._client.aclose()
```

---

### 3. Bot Framework Handler (Bot 處理器)

**使用時機**: 處理 Teams 訊息或互動

```python
"""Bot 訊息處理器"""
from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import ChannelAccount, Activity
import logging

logger = logging.getLogger(__name__)


class FeatureBotHandler(ActivityHandler):
    """功能 Bot 處理器"""

    async def on_message_activity(self, turn_context: TurnContext):
        """處理訊息"""
        user_message = turn_context.activity.text
        user_id = turn_context.activity.from_property.id

        logger.info(f"收到訊息: user={user_id}, msg={user_message}")

        # TODO: 實作訊息處理邏輯
        response = f"您說: {user_message}"

        await turn_context.send_activity(response)

    async def on_members_added_activity(
        self,
        members_added: list[ChannelAccount],
        turn_context: TurnContext
    ):
        """處理成員加入"""
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("歡迎使用！")
```

---

### 4. Unit Test (單元測試)

**使用時機**: 測試功能模組

```python
"""測試功能模組"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock


def test_feature_init():
    """測試初始化"""
    from app.services.feature import FeatureService
    service = FeatureService(api_key="test-key")
    assert service.api_key == "test-key"


def test_feature_async():
    """測試非同步操作"""
    from app.services.feature import FeatureService

    async def run_test():
        service = FeatureService()
        result = await service.process("user-123", {"data": "test"})
        return result

    result = asyncio.run(run_test())
    assert result is not None


@pytest.mark.parametrize("input,expected", [
    ("data1", "result1"),
    ("data2", "result2"),
])
def test_feature_parametrized(input, expected):
    """參數化測試"""
    # TODO: 實作測試
    assert True


def test_feature_with_mock():
    """Mock 測試"""
    with patch('app.services.feature.httpx.AsyncClient') as mock_client:
        mock_response = Mock()
        mock_response.json.return_value = {"status": "success"}
        mock_response.status_code = 200

        mock_instance = AsyncMock()
        mock_instance.post.return_value = mock_response
        mock_client.return_value = mock_instance

        # 執行測試
        from app.services.feature import FeatureService
        service = FeatureService()

        async def run():
            return await service.process("user-123", {})

        result = asyncio.run(run())
        assert result["status"] == "success"
```

---

### 5. Adaptive Card (Teams 卡片)

**使用時機**: 在 Teams 顯示互動式卡片

```python
"""Adaptive Card 生成"""
from botbuilder.schema import Attachment


def create_feature_card(
    title: str,
    data: dict,
    actions: list[dict] = None
) -> Attachment:
    """建立功能卡片"""

    card_body = [
        {
            "type": "TextBlock",
            "text": title,
            "size": "Large",
            "weight": "Bolder"
        },
        {
            "type": "FactSet",
            "facts": [
                {"title": k, "value": str(v)}
                for k, v in data.items()
            ]
        }
    ]

    card_actions = []
    if actions:
        for action in actions:
            card_actions.append({
                "type": "Action.Submit",
                "title": action.get("title", "Action"),
                "data": action.get("data", {})
            })

    adaptive_card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": card_body,
        "actions": card_actions
    }

    return Attachment(
        content_type="application/vnd.microsoft.card.adaptive",
        content=adaptive_card
    )
```

---

### 6. Databricks SDK Usage (Databricks 整合)

**使用時機**: 呼叫 Databricks Genie API

```python
"""Databricks Genie 整合"""
import httpx
from app.core.config import DefaultConfig

async def query_genie(
    space_id: str,
    conversation_id: str,
    query: str
) -> dict:
    """查詢 Genie"""

    url = f"{DefaultConfig.DATABRICKS_HOST}/api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages"

    headers = {
        "Authorization": f"Bearer {DefaultConfig.DATABRICKS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {"content": query}

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
```

---

### 7. Azure Identity Authentication (Azure 認證)

**使用時機**: 使用 Azure 服務認證

```python
"""Azure 認證"""
from azure.identity import DefaultAzureCredential
from azure.core.credentials import TokenCredential


def get_azure_credential() -> TokenCredential:
    """
    取得 Azure 認證

    自動嘗試以下方式（按順序）：
    1. 環境變數 (AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID)
    2. Managed Identity (Azure 部署時)
    3. Azure CLI (本地開發)
    4. Visual Studio Code
    """
    return DefaultAzureCredential()


# 使用範例
async def call_azure_service():
    """呼叫 Azure 服務"""
    credential = get_azure_credential()

    # 取得 access token
    token = credential.get_token("https://graph.microsoft.com/.default")

    # 使用 token 呼叫 API
    headers = {"Authorization": f"Bearer {token.token}"}
    # ...
```

---

### 8. Chart Generation (圖表生成)

**使用時機**: 生成資料視覺化圖表

```python
"""圖表生成（Matplotlib + Seaborn）"""
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64


def generate_chart(
    data: list[dict],
    chart_type: str = "bar"
) -> str:
    """
    生成圖表並返回 base64 圖片

    Args:
        data: 資料 [{"label": "A", "value": 10}, ...]
        chart_type: 圖表類型 (bar, pie, line)

    Returns:
        str: Base64 編碼的圖片
    """
    # 設定中文字型
    plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']
    plt.rcParams['axes.unicode_minus'] = False

    # 準備資料
    labels = [item["label"] for item in data]
    values = [item["value"] for item in data]

    # 建立圖表
    fig, ax = plt.subplots(figsize=(10, 6))

    if chart_type == "bar":
        sns.barplot(x=labels, y=values, ax=ax, palette="viridis")
        ax.set_ylabel("數值")
    elif chart_type == "pie":
        ax.pie(values, labels=labels, autopct='%1.1f%%')
    elif chart_type == "line":
        sns.lineplot(x=labels, y=values, ax=ax, marker='o')

    ax.set_title(f"{chart_type.capitalize()} Chart")
    plt.tight_layout()

    # 轉換為 base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150)
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode()
    plt.close()

    return f"data:image/png;base64,{image_base64}"
```

---

## 專案架構速查

```
app/
├── main.py              # FastAPI 應用程式
├── api/                 # API 路由
│   ├── bot.py          # Bot Framework 端點
│   ├── genie.py        # Genie API 端點
│   └── health.py       # 健康檢查
├── services/           # 服務層
│   ├── genie.py        # Databricks Genie 整合
│   ├── graph.py        # Microsoft Graph
│   └── health_check.py
├── utils/              # 工具
│   ├── cache_utils.py      # 快取
│   ├── chart_analyzer.py   # 圖表
│   ├── email_extractor.py  # Email 提取
│   └── session_manager.py  # 會話管理
├── core/               # 核心
│   ├── config.py       # 配置
│   ├── adapter.py      # Bot Adapter
│   └── exceptions.py   # 異常
└── models/
    └── user_session.py # 會話模型

bot/
├── handlers/
│   ├── bot.py          # Bot 處理器
│   └── commands.py     # 命令處理
├── dialogs/
│   └── sso_dialog.py   # SSO 對話
└── cards/              # Adaptive Cards
```

---

## 開發工作流程

### 新增功能
```
1. 分析需求 → 確認功能範圍
2. 建立服務模組（如需） → app/services/
3. 建立 API 端點（如需） → app/api/
4. 建立測試 → tests/unit/
5. 執行測試 → pytest
6. 提交 → git commit
```

### 修改功能
```
1. 閱讀程式碼 → Read tool
2. 修改 → Edit tool
3. 更新測試
4. 執行測試
5. 提交
```

---

## 最佳實踐

### 1. 錯誤處理
```python
from app.core.exceptions import ServiceError, AuthenticationError

try:
    result = await service.process()
except httpx.HTTPStatusError as e:
    raise ServiceError(f"API 錯誤: {e.response.text}")
```

### 2. 日誌
```python
import logging
logger = logging.getLogger(__name__)

logger.info(f"操作: user_id={id}")
logger.error(f"錯誤: {e}", exc_info=True)
```

### 3. 配置
```python
from app.core.config import DefaultConfig

token = DefaultConfig.DATABRICKS_TOKEN
host = DefaultConfig.DATABRICKS_HOST
```

### 4. 類型提示
```python
from typing import Optional, Dict, List

async def process(
    user_id: str,
    data: Dict[str, Any],
    timeout: Optional[float] = None
) -> List[Dict]:
    pass
```

---

## 常用命令

```bash
# 執行應用程式
uv run uvicorn app.main:app --port 8000 --reload

# 執行測試
pytest
pytest tests/unit/test_feature.py
pytest --cov=app

# Git
git add <files>
git commit -m "feat: 新增功能"
git push
```

---

## 環境變數（.env）

```bash
# Databricks
DATABRICKS_TOKEN=dapi...
DATABRICKS_HOST=https://xxx.databricks.com
DATABRICKS_SPACE_ID=01abc...

# Azure Bot
APP_ID=your-app-id
APP_PASSWORD=your-password
APP_TENANTID=your-tenant-id

# 功能開關
ENABLE_GRAPH_API_AUTO_LOGIN=true
ENABLE_FEEDBACK_CARDS=true
```

---

## 參考文檔

- [CLAUDE.md](../../../CLAUDE.md) - 完整開發指南
- [README.md](../../../README.md) - 專案概覽
- [docs/architecture/](../../../docs/architecture/) - 架構文檔
- [docs/troubleshooting.md](../../../docs/troubleshooting.md) - 故障排除
