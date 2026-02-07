from botbuilder.dialogs import (
    ComponentDialog,
    OAuthPrompt,
    OAuthPromptSettings,
    WaterfallDialog,
    WaterfallStepContext,
    DialogTurnResult
)
from botbuilder.core import MessageFactory
from botbuilder.schema import TokenResponse
from app.core.config import DefaultConfig

class SSODialog(ComponentDialog):
    def __init__(self, connection_name: str):
        super(SSODialog, self).__init__(SSODialog.__name__)

        self.connection_name = connection_name

        self.add_dialog(
            OAuthPrompt(
                OAuthPrompt.__name__,
                OAuthPromptSettings(
                    connection_name=connection_name,
                    text="請登入 (Please sign in)",
                    title="登入 (Sign In)",
                    timeout=300000,
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
        token_response: TokenResponse = step_context.result
        if token_response and token_response.token:
            # We have the token, we can get user info here if needed
            # For now, just return the token to the parent dialog or handler
            return await step_context.end_dialog(token_response)

        await step_context.context.send_activity("登入失敗或已取消。")
        return await step_context.end_dialog(None)
