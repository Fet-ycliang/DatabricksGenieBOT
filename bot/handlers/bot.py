"""Bot handler — 處理 Teams 訊息路由和對話流程。

UI 渲染邏輯已抽取至 bot.cards.query_result_renderer，
此模組僅負責訊息路由、Dialog 管理和 Session 管理。
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

from botbuilder.core import (
    ActivityHandler,
    ConversationState,
    MessageFactory,
    TurnContext,
    UserState,
)
from botbuilder.dialogs import Dialog, DialogSet, DialogTurnStatus
from botbuilder.schema import (
    Activity,
    ActivityTypes,
    ChannelAccount,
    InvokeResponse,
)

from app.core.config import DefaultConfig
from app.models.user_session import UserSession, is_conversation_timed_out
from app.services.genie import GenieService
from app.utils.email_extractor import EmailExtractor
from bot.cards.constants import ADAPTIVE_CARD_VERSION
from bot.cards.feedback_cards import create_error_card, create_thank_you_card, send_feedback_card
from bot.cards.query_result_renderer import render_response
from bot.cards.welcome_messages import build_authenticated_welcome, build_unauthenticated_welcome
from bot.handlers.commands import handle_special_commands

logger = logging.getLogger(__name__)


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

        self.user_sessions: Dict[str, UserSession] = {}
        self.email_sessions: Dict[str, UserSession] = {}
        try:
            self._local_tz = ZoneInfo(self.config.TIMEZONE)
        except Exception:
            self._local_tz = timezone.utc

    async def on_turn(self, turn_context: TurnContext):
        await super().on_turn(turn_context)
        await self.conversation_state.save_changes(turn_context)
        await self.user_state.save_changes(turn_context)

    async def on_members_added_activity(
        self, members_added: List[ChannelAccount], turn_context: TurnContext
    ):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                is_emulator = turn_context.activity.channel_id == "emulator"
                await turn_context.send_activity(
                    build_unauthenticated_welcome(is_emulator, self.config)
                )

    async def on_message_activity(self, turn_context: TurnContext):
        text = turn_context.activity.text

        # Adaptive Card Submit（Emulator 中以 message 形式抵達）
        if not text and turn_context.activity.value:
            invoke_value = turn_context.activity.value or {}
            if invoke_value.get("action") in {"feedback", "ask_suggested_question"}:
                await self.on_adaptive_card_invoke(turn_context, invoke_value)
                return

        if text and (text.lower() in ["/reset", "reset", "new chat"]):
            pass

        # Emulator: 允許在建立 session 前使用 /setuser
        if turn_context.activity.channel_id == "emulator" and text:
            if text.lower().startswith("/setuser "):
                temp_session = UserSession(
                    turn_context.activity.from_property.id,
                    "temp@localhost",
                    turn_context.activity.from_property.name or "User",
                )
                if await handle_special_commands(
                    turn_context, text, temp_session, self.config,
                    self._format_local_timestamp, self.user_sessions, self.email_sessions,
                ):
                    return

        await self._run_dialog(turn_context)

    async def on_invoke_activity(self, turn_context: TurnContext) -> InvokeResponse:
        try:
            if turn_context.activity.name == "adaptiveCard/action":
                invoke_value = turn_context.activity.value or {}
                return await self.on_adaptive_card_invoke(turn_context, invoke_value)
            return InvokeResponse(status=200, body="OK")
        except Exception:
            return InvokeResponse(status=500, body="Error processing invoke activity")

    async def on_adaptive_card_invoke(
        self, turn_context: TurnContext, invoke_value: Dict
    ) -> InvokeResponse:
        try:
            action = invoke_value.get("action")

            if action == "ask_suggested_question":
                return await self._handle_suggested_question(turn_context, invoke_value)

            if action == "feedback":
                return await self._handle_feedback(turn_context, invoke_value)

            return InvokeResponse(status=400, body="Unknown action")
        except Exception:
            return InvokeResponse(status=500, body="Error processing feedback")

    async def _handle_suggested_question(
        self, turn_context: TurnContext, invoke_value: Dict
    ) -> InvokeResponse:
        question = invoke_value.get("question")
        if not question:
            return InvokeResponse(status=400, body="Missing question data")

        user_session = await self._get_user_session(turn_context)
        if not user_session:
            user_session = await self._create_local_session(turn_context)

        await turn_context.send_activity(f"\U0001F4AD {question}")
        await self._process_genie_question(turn_context, user_session, question)
        return InvokeResponse(status=200, body={"status": "success"})

    async def _handle_feedback(
        self, turn_context: TurnContext, invoke_value: Dict
    ) -> InvokeResponse:
        message_id = invoke_value.get("messageId")
        user_id = invoke_value.get("userId")
        feedback = invoke_value.get("feedback")

        if not all([message_id, user_id, feedback]):
            return InvokeResponse(status=400, body="Missing required feedback data")

        user_session = self.user_sessions.get(user_id)
        try:
            await self.genie_service.send_feedback(user_session, message_id, feedback)
            updated_card = create_thank_you_card()
            return InvokeResponse(
                status=200,
                body={
                    "type": "AdaptiveCard",
                    "version": ADAPTIVE_CARD_VERSION,
                    "body": updated_card["body"],
                },
            )
        except Exception:
            error_card = create_error_card("提交回饋失敗。請再試一次。")
            return InvokeResponse(
                status=200,
                body={
                    "type": "AdaptiveCard",
                    "version": ADAPTIVE_CARD_VERSION,
                    "body": error_card["body"],
                },
            )

    async def on_token_response_event(self, turn_context: TurnContext):
        await self._run_dialog(turn_context)

    async def _run_dialog(self, turn_context: TurnContext):
        dc = await self.dialog_set.create_context(turn_context)
        result = await dc.continue_dialog()

        if result.status == DialogTurnStatus.Empty:
            user_session = await self._get_user_session(turn_context)
            if not user_session:
                if not self.config.APP_ID or not self.config.APP_PASSWORD:
                    is_emulator = turn_context.activity.channel_id == "emulator"
                    await turn_context.send_activity(
                        build_unauthenticated_welcome(is_emulator, self.config)
                    )
                    return
                await dc.begin_dialog(self.dialog.id)
            else:
                await self._process_genie_message(turn_context, user_session)

        elif result.status == DialogTurnStatus.Complete:
            token_response = result.result
            if token_response and token_response.token:
                user_id = turn_context.activity.from_property.id
                name = turn_context.activity.from_property.name or "User"
                email = await EmailExtractor.get_email(
                    turn_context, token_response, fallback_name=name, use_graph_api=True
                )
                session = UserSession(user_id, email, name)
                self.user_sessions[user_id] = session

                await turn_context.send_activity(f"登入成功！歡迎 {name}。")
                is_emulator = turn_context.activity.channel_id == "emulator"
                await turn_context.send_activity(
                    build_authenticated_welcome(session, is_emulator, self.config)
                )

    async def _process_genie_message(
        self, turn_context: TurnContext, user_session: UserSession
    ):
        question = turn_context.activity.text
        if not question:
            await turn_context.send_activity("請輸入問題內容。")
            return
        await self._process_genie_question(turn_context, user_session, question)

    async def _process_genie_question(
        self, turn_context: TurnContext, user_session: UserSession, question: str
    ):
        """處理 Genie 查詢：路由 → API 呼叫 → 委託 renderer 處理 UI。"""
        # 顯示正在輸入
        await turn_context.send_activity(Activity(type=ActivityTypes.typing))

        # 處理特殊指令
        if await handle_special_commands(
            turn_context, question, user_session, self.config,
            self._format_local_timestamp, self.user_sessions, self.email_sessions,
        ):
            return

        # 呼叫 Genie Service
        try:
            response_payload, conversation_id, message_id = await self.genie_service.ask(
                question=question,
                space_id=self.config.DATABRICKS_SPACE_ID,
                user_session=user_session,
                conversation_id=user_session.conversation_id,
            )

            # 更新 Session
            if conversation_id:
                user_session.conversation_id = conversation_id
            if message_id:
                user_session.user_context["last_genie_message_id"] = message_id

            # 委託 renderer 處理所有 UI 渲染
            response_data = json.loads(response_payload)
            await render_response(
                turn_context=turn_context,
                response_data=response_data,
                user_session=user_session,
                enable_feedback_cards=self.config.ENABLE_FEEDBACK_CARDS,
            )

        except Exception as e:
            logger.error(f"處理查詢時發生錯誤: {e}", exc_info=True)
            error_msg = (
                "很抱歉，處理您的查詢時發生了問題。\n\n"
                "請稍後再試，或聯絡管理員取得協助。\n"
                f"管理員：{self.config.ADMIN_CONTACT_EMAIL}"
            )
            await turn_context.send_activity(error_msg)

    def _format_local_timestamp(self, dt: Optional[datetime]) -> str:
        if not dt:
            return "N/A"
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        localized = dt.astimezone(self._local_tz)
        return localized.strftime("%Y-%m-%d %H:%M:%S")

    async def _create_local_session(self, turn_context: TurnContext) -> UserSession:
        user_id = turn_context.activity.from_property.id
        name = turn_context.activity.from_property.name or "User"
        email = f"{name}@localhost"
        session = UserSession(user_id, email, name)
        self.user_sessions[user_id] = session
        return session

    async def _get_user_session(
        self, turn_context: TurnContext
    ) -> Optional[UserSession]:
        user_id = turn_context.activity.from_property.id
        return self.user_sessions.get(user_id)
