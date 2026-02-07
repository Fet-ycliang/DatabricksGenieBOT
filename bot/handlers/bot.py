from typing import Dict, List, Optional
from botbuilder.core import ActivityHandler, TurnContext, ConversationState, UserState, MessageFactory
from botbuilder.schema import ChannelAccount, Activity, ActivityTypes
from botbuilder.dialogs import Dialog, DialogSet, DialogTurnStatus

from app.core.config import DefaultConfig
from app.services.genie import GenieService
from app.models.user_session import UserSession, is_conversation_timed_out
from bot.handlers.commands import handle_special_commands
from bot.cards.welcome_messages import build_authenticated_welcome, build_unauthenticated_welcome
from bot.cards.feedback_cards import create_error_card
from bot.dialogs.sso_dialog import SSODialog
from bot.cards.chart_generator import create_suggested_questions_card
import traceback
import json

class MyBot(ActivityHandler):
    def __init__(
        self,
        config: DefaultConfig,
        genie_service: GenieService,
        conversation_state: ConversationState,
        user_state: UserState,
        dialog: Dialog,
    ):
        self.config = config
        self.genie_service = genie_service
        self.conversation_state = conversation_state
        self.user_state = user_state
        self.dialog = dialog
        self.dialog_set = DialogSet(self.conversation_state.create_property("DialogState"))
        self.dialog_set.add(self.dialog)

        # In-memory session management (consider moving to UserState if possible)
        self.user_sessions: Dict[str, UserSession] = {}

    async def on_turn(self, turn_context: TurnContext):
        await super().on_turn(turn_context)
        await self.conversation_state.save_changes(turn_context)
        await self.user_state.save_changes(turn_context)

    async def on_members_added_activity(
        self, members_added: List[ChannelAccount], turn_context: TurnContext
    ):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                # Try to get user session or prompt for login
                # For SSO, we might just show a welcome card with a sign-in button if needed,
                # or just wait for them to say something.
                # Let's show the unauthenticated welcome first, which might have a "Login" button triggers the SSO dialog.
                await turn_context.send_activity(build_unauthenticated_welcome())

    async def on_message_activity(self, turn_context: TurnContext):
        # Check for special commands first
        text = turn_context.activity.text
        if text and (text.lower() in ["/reset", "reset", "new chat"]):
            # Handle reset
             # ... implementation ...
            pass
            
        # Run the Dialog (SSO)
        await self._run_dialog(turn_context)

    async def on_token_response_event(self, turn_context: TurnContext):
        # Run the Dialog (SSO) to handle the token response
        await self._run_dialog(turn_context)

    async def _run_dialog(self, turn_context: TurnContext):
        dc = await self.dialog_set.create_context(turn_context)
        result = await dc.continue_dialog()
        
        if result.status == DialogTurnStatus.Empty:
            # If no active dialog, verify if we have a user session
            user_session = await self._get_user_session(turn_context)
            if not user_session:
                # Start SSO Dialog
                await dc.begin_dialog(self.dialog.id)
            else:
                 # Process the message with Genie
                 await self._process_genie_message(turn_context, user_session)

        elif result.status == DialogTurnStatus.Complete:
            # SSO completed
            token_response = result.result
            if token_response and token_response.token:
                # Create user session from token
                # In a real scenario, use graph to get email:
                # email = await get_user_email(token_response.token)
                
                # For now, we simulate or try to get from context if available
                # or just use a placeholder until graph skill is integrated
                user_id = turn_context.activity.from_property.id
                name = turn_context.activity.from_property.name or "User"
                email = f"{name}@example.com" # Placeholder if we don't call Graph
                
                # Create Session
                session = UserSession(user_id, email, name)
                self.user_sessions[user_id] = session
                
                await turn_context.send_activity(f"登入成功！歡迎 {name}。")
                await turn_context.send_activity(build_authenticated_welcome())
                
                # If there was a pending question (e.g. from before login), we could process it here
                # But typically we just let them ask again.

    async def _process_genie_message(self, turn_context: TurnContext, user_session: UserSession):
        # 顯示正在輸入
        await turn_context.send_activity(Activity(type=ActivityTypes.typing))

        question = turn_context.activity.text
        
        # 呼叫 Genie Service
        try:
            response_payload, conversation_id, message_id = await self.genie_service.ask(
                question=question,
                space_id=self.config.DATABRICKS_SPACE_ID,
                user_session=user_session,
                conversation_id=user_session.conversation_id
            )
            
            # 更新 Session
            if conversation_id:
                user_session.conversation_id = conversation_id
                
            # 處理回應 (這裡簡化，直接回傳 JSON 或解析後的文字)
            # 在完整實作中，這裡應該解析 response_payload 並使用 Adaptive Cards 顯示
            response_data = json.loads(response_payload)
            
            if "error" in response_data:
                 await turn_context.send_activity(f"Error: {response_data['error']}")
            elif "message" in response_data:
                 await turn_context.send_activity(response_data["message"])
                 
                 # 處理建議問題
                 if "suggested_questions" in response_data and response_data["suggested_questions"]:
                     card = create_suggested_questions_card(response_data["suggested_questions"])
                     if card:
                         await turn_context.send_activity(MessageFactory.attachment(card))
            elif "data" in response_data:
                 # 處理資料表格
                 await turn_context.send_activity("收到資料結果 (Data Result)")
                 
        except Exception as e:
            traceback.print_exc()
            await turn_context.send_activity("發生錯誤，請稍後再試。")

    async def _get_user_session(self, turn_context: TurnContext) -> Optional[UserSession]:
        user_id = turn_context.activity.from_property.id
        return self.user_sessions.get(user_id)
