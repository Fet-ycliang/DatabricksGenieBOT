---
name: botbuilder-py
description: Microsoft Bot Framework SDK for Python (botbuilder-py). Use when developing chatbots, handling user activities, managing state, or sending Adaptive Cards.
---

# Microsoft Bot Framework SDK for Python

使用 Bot Framework SDK 建置對話式機器人。

## 安裝

```bash
pip install botbuilder-core botbuilder-integration-aiohttp botbuilder-schema
```

## 環境變數

```bash
APP_ID=<microsoft-app-id>
APP_PASSWORD=<microsoft-app-password>
```

## 身份驗證與 Adapter 設定

### Aiohttp 整合

```python
from botbuilder.core import BotFrameworkAdapterSettings, BotFrameworkAdapter
from botbuilder.integration.aiohttp import CloudAdapter, ConfigurationBotFrameworkAuthentication
from botbuilder.schema import Activity, ActivityTypes

# Production: CloudAdapter
ADAPTER = CloudAdapter(ConfigurationBotFrameworkAuthentication(config))

# Local Dev / Emulator: BotFrameworkAdapter
SETTINGS = BotFrameworkAdapterSettings("", "")
ADAPTER = BotFrameworkAdapter(SETTINGS)
```

## 核心工作流程：Active Handler

繼承 `ActivityHandler` 以管理事件驅動的對話。

```python
from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import Activity, ActivityTypes

class MyBot(ActivityHandler):
    async def on_message_activity(self, turn_context: TurnContext):
        # 處理使用者文字訊息
        text = turn_context.activity.text
        if text:
             await turn_context.send_activity(f"You said: {text}")
        else:
             # 處理其他訊息類型 (例如 adaptive card submit)
             if turn_context.activity.value:
                 await self._handle_card_submit(turn_context)

    async def on_members_added_activity(self, members_added, turn_context):
        # 歡迎新成員
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Welcome to the bot!")
```

## 發送 Adaptive Cards

Adaptive Cards 是標準的 JSON 序列化卡片物件。

```python
from botbuilder.schema import Attachment, Activity, ActivityTypes
import json

def create_adaptive_card():
    card_content = {
        "type": "AdaptiveCard",
        "version": "1.3",
        "body": [
            {
                "type": "TextBlock",
                "text": "Hello, Adaptive Card!"
            }
        ]
    }

    return Attachment(
        content_type="application/vnd.microsoft.card.adaptive",
        content=card_content
    )

async def send_card(turn_context: TurnContext):
    card_attachment = create_adaptive_card()
    message = Activity(
        type=ActivityTypes.message,
        attachments=[card_attachment]
    )
    await turn_context.send_activity(message)
```

## 錯誤處理

為 adapter 實作全域錯誤處理。

```python
async def on_error(context: TurnContext, error: Exception):
    print(f"CRITICAL ERROR: {error}")
    await context.send_activity("The bot encountered an error or bug.")

ADAPTER.on_turn_error = on_error
```

## 最佳實踐

1.  **狀態管理 (State Management)**：使用 `ConversationState` 和 `UserState` 跨回合 (turns) 持久化資料。
2.  **中介軟體 (Middleware)**：使用中介軟體 (例如 `TranscriptLoggerMiddleware`) 進行日誌記錄和檢查。
3.  **輸入指示器 (Typing Indicator)**：在長時間執行的操作 (>1s) 之前發送輸入活動 (`ActivityTypes.typing`)。
4.  **Async/Await**：SDK 是完全非同步的。務必 await `send_activity` 和其他 I/O 綁定呼叫。

## FastAPI 整合 (標準模式)

使用 FastAPI 時，只需在你的路由處理程序中呼叫 `process_activity`：

```python
# In your FastAPI route handler
async def messages(req: Request):
    # ... parse request ...
    response = await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
    return response
```

確保你的 `ADAPTER` 是配置了與 `aiohttp` 相容設定的 `CloudAdapter` (用於生產環境) 或 `BotFrameworkAdapter` (用於本地開發)，因為 FastAPI 以類似的方式處理底層非同步儲存。
