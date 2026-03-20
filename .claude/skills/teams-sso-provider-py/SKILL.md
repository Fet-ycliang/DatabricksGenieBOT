---
name: teams-sso-provider-py
description: Implement Teams Single Sign-On (SSO) using Bot Framework. Covers OAuthPrompt, Token Exchange, and On-Behalf-Of flow.
---

# Teams SSO Provider (Python)

Implement silent authentication in Microsoft Teams using Azure AD.

## Prerequisite: Azure AD App Registration

1.  **Expose an API**: Set Application ID URI to `api://botid-{app-id}`.
2.  **Scopes**: Add `access_as_user` scope.
3.  **Authorized Client Applications**: Add Teams Mobile/Desktop (`1fec8e78-bce4-4aaf-ab1b-5451cc387264`) and Teams Web (`5e3ce6c0-2b1f-4285-8d4b-75ee78787346`).
4.  **Manifest**: in `manifest.json`, set `webApplicationInfo`:
    ```json
    "webApplicationInfo": {
        "id": "{app-id}",
        "resource": "api://botid-{app-id}"
    }
    ```

## 1. Setup OAuth Prompt

In your Dialog (e.g., `MainDialog`):

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

## 2. Handle Token Exchange (Invoke)

Crucial for silent SSO. You must override `on_invoke_activity` in your Activity Handler.

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

## 3. Azure Bot Service Configuration (Crucial)

You must configure the OAuth Connection in the Azure Portal.

1.  Go to your **Azure Bot** resource in Azure Portal.
2.  Navigate to **Settings** -> **Configuration** (or **OAuth Connection Settings**).
3.  Click **Add Setting**.
4.  **Name**: Enter a name (e.g., `MyTeamsSSOConnection`). **Copy this name**.
5.  **Service Provider**: Select `Azure Active Directory v2`.
6.  **Client id**: Your Azure AD App ID.
7.  **Client secret**: Your Azure AD App Secret.
8.  **Token Exchange URL**: Leave blank or use `api://botid-{app-id}`.
9.  **Tenant ID**: `common` (for multi-tenant) or your specific Tenant ID.
10. **Scopes**: `User.Read` (and any others you need).
11. Click **Save**.

This **Name** is what you refer to as `ConnectionName` in your code.

## 4. Configuration

Ensure your `.env` has:

```bash
ConnectionName=MyTeamsSSOConnection
MicrosoftAppId=<app-id>
MicrosoftAppPassword=<app-password>
```
