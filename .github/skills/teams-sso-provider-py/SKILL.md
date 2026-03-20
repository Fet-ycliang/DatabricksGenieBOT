---
name: teams-sso-provider-py
description: 使用 Bot Framework 實作 Teams 單一登入 (SSO)。涵蓋 OAuthPrompt、Token Exchange 和 On-Behalf-Of 流程。
---

# Teams SSO Provider (Python)

使用 Azure AD 在 Microsoft Teams 中實作靜默身份驗證。

## 前置條件：Azure AD 應用程式註冊

1.  **Expose an API**: 設定 Application ID URI 為 `api://botid-{app-id}`。
2.  **Scopes**: 新增 `access_as_user` scope。
3.  **Authorized Client Applications**: 新增 Teams Mobile/Desktop (`1fec8e78-bce4-4aaf-ab1b-5451cc387264`) 和 Teams Web (`5e3ce6c0-2b1f-4285-8d4b-75ee78787346`)。
4.  **Manifest**: 在 `manifest.json` 中，設定 `webApplicationInfo`：
    ```json
    "webApplicationInfo": {
        "id": "{app-id}",
        "resource": "api://botid-{app-id}"
    }
    ```

## 1. 設定 OAuth Prompt

在你的 Dialog (例如 `MainDialog`) 中：

```python
from botbuilder.dialogs import (
    ComponentDialog,
    OAuthPrompt,
    OAuthPromptSettings,
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult
)

class MainDialog(ComponentDialog):
    def __init__(self, connection_name: str):
        super().__init__(MainDialog.__name__)

        self.add_dialog(
            OAuthPrompt(
                OAuthPrompt.__name__,
                OAuthPromptSettings(
                    connection_name=connection_name,
                    text="Please sign in",
                    title="Sign In",
                    timeout=30000,
                ),
            )
        )
        self.add_dialog(
            WaterfallDialog(
                "WFDialog",
                [
                    self.prompt_step,
                    self.login_step
                ]
            )
        )
        self.initial_dialog_id = "WFDialog"

    async def prompt_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        return await step_context.begin_dialog(OAuthPrompt.__name__)

    async def login_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        # Get the token from the result
        token_response = step_context.result
        if token_response:
            await step_context.context.send_activity(f"You are logged in! Token: {token_response.token}")
            return await step_context.end_dialog()

        await step_context.context.send_activity("Login failed or cancelled.")
        return await step_context.end_dialog()
```

## 2. 處理 Token Exchange (Invoke)

這對於靜默 SSO 至關重要。你必須在 Activity Handler 解覆寫 `on_invoke_activity`。

```python
from botbuilder.core import TurnContext
from botbuilder.schema import ActivityTypes
from botbuilder.dialogs import Dialog, DialogSet, DialogTurnStatus

class TeamsBot(ActivityHandler):
    def __init__(self, conversation_state, user_state, dialog):
        self.conversation_state = conversation_state
        self.user_state = user_state
        self.dialog = dialog
        self.dialog_set = DialogSet(conversation_state.create_property("DialogState"))
        self.dialog_set.add(dialog)

    async def on_turn(self, turn_context: TurnContext):
        await super().on_turn(turn_context)
        await self.conversation_state.save_changes(turn_context)
        await self.user_state.save_changes(turn_context)

    async def on_invoke_activity(self, turn_context: TurnContext):
        # Handle Teams Signin Verify State (Invoke)
        if turn_context.activity.name == "signin/verifyState":
            await self._run_dialog(turn_context)
            return InvokeResponse(status=200)

        # Handle SSO Token Exchange
        if turn_context.activity.name == "signin/tokenExchange":
            await self._run_dialog(turn_context)
            return InvokeResponse(status=200)

        return await super().on_invoke_activity(turn_context)

    async def _run_dialog(self, turn_context: TurnContext):
        # Helper to run the dialog stack
        dc = await self.dialog_set.create_context(turn_context)
        result = await dc.continue_dialog()
        if result.status == DialogTurnStatus.Empty:
            await dc.begin_dialog(self.dialog.id)
```

## 3. Azure Bot Service 設定 (關鍵)

你必須在 Azure Portal 中設定 OAuth Connection。

1.  前往 Azure Portal 中的 **Azure Bot** 資源。
2.  瀏覽至 **Settings** -> **Configuration** (或 **OAuth Connection Settings**)。
3.  點擊 **Add Setting**。
4.  **Name**: 輸入名稱 (例如 `MyTeamsSSOConnection`)。**複製此名稱**。
5.  **Service Provider**: 選擇 `Azure Active Directory v2`。
6.  **Client id**: 你的 Azure AD App ID。
7.  **Client secret**: 你的 Azure AD App Secret。
8.  **Token Exchange URL**: 留空或是使用 `api://botid-{app-id}`。
9.  **Tenant ID**: `common` (用於多租戶) 或你的特定 Tenant ID。
10. **Scopes**: `User.Read` (以及其他你需要的)。
11. 點擊 **Save**。

此 **Name** 即你在程式碼中引用的 `ConnectionName`。

## 4. 設定

確保你的 `.env` 包含：

```bash
ConnectionName=MyTeamsSSOConnection
MicrosoftAppId=<app-id>
MicrosoftAppPassword=<app-password>
```
