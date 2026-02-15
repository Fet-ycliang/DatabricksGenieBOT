from typing import Dict, List, Optional
from botbuilder.core import ActivityHandler, TurnContext, ConversationState, UserState, MessageFactory
from botbuilder.schema import ChannelAccount, Activity, ActivityTypes, InvokeResponse
from botbuilder.dialogs import Dialog, DialogSet, DialogTurnStatus

from app.core.config import DefaultConfig
from app.services.genie import GenieService
from app.models.user_session import UserSession, is_conversation_timed_out
from app.utils.chart_analyzer import ChartAnalyzer
from app.utils.email_extractor import EmailExtractor
from bot.handlers.commands import handle_special_commands
from bot.cards.welcome_messages import build_authenticated_welcome, build_unauthenticated_welcome
from bot.cards.feedback_cards import create_error_card, create_thank_you_card, send_feedback_card
from bot.dialogs.sso_dialog import SSODialog
from bot.cards.chart_generator import create_suggested_questions_card, create_chart_card_with_image
import traceback
import json
import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

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

        # In-memory session management (consider moving to UserState if possible)
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
                # Try to get user session or prompt for login
                # For SSO, we might just show a welcome card with a sign-in button if needed,
                # or just wait for them to say something.
                # Let's show the unauthenticated welcome first, which might have a "Login" button triggers the SSO dialog.
                is_emulator = turn_context.activity.channel_id == "emulator"
                await turn_context.send_activity(build_unauthenticated_welcome(is_emulator, self.config))

    async def on_message_activity(self, turn_context: TurnContext):
        # Check for special commands first
        text = turn_context.activity.text
        # Adaptive Card Submit in Emulator can arrive as message with no text
        if not text and turn_context.activity.value:
            invoke_value = turn_context.activity.value or {}
            if invoke_value.get("action") in {"feedback", "ask_suggested_question"}:
                await self.on_adaptive_card_invoke(turn_context, invoke_value)
                return
        if text and (text.lower() in ["/reset", "reset", "new chat"]):
            # Handle reset
             # ... implementation ...
            pass

        # Emulator: allow /setuser before any session is created
        if turn_context.activity.channel_id == "emulator" and text:
            if text.lower().startswith("/setuser "):
                temp_session = UserSession(
                    turn_context.activity.from_property.id,
                    "temp@localhost",
                    turn_context.activity.from_property.name or "User",
                )
                if await handle_special_commands(
                    turn_context,
                    text,
                    temp_session,
                    self.config,
                    self._format_local_timestamp,
                    self.user_sessions,
                    self.email_sessions,
                ):
                    return
            
        # Run the Dialog (SSO)
        await self._run_dialog(turn_context)

    async def on_invoke_activity(self, turn_context: TurnContext) -> InvokeResponse:
        try:
            if turn_context.activity.name == "adaptiveCard/action":
                invoke_value = turn_context.activity.value or {}
                return await self.on_adaptive_card_invoke(turn_context, invoke_value)

            return InvokeResponse(status=200, body="OK")
        except Exception:
            return InvokeResponse(status=500, body="Error processing invoke activity")

    async def on_adaptive_card_invoke(self, turn_context: TurnContext, invoke_value: Dict) -> InvokeResponse:
        try:
            action = invoke_value.get("action")

            if action == "ask_suggested_question":
                question = invoke_value.get("question")
                if not question:
                    return InvokeResponse(status=400, body="Missing question data")

                user_session = await self._get_user_session(turn_context)
                if not user_session:
                    user_session = await self._create_local_session(turn_context)

                # 發送建議的問題文本到聊天窗口，而不是直接執行
                await turn_context.send_activity(f"💭 {question}")
                
                # 然後執行查詢
                await self._process_genie_question(turn_context, user_session, question)
                return InvokeResponse(status=200, body={"status": "success"})

            if action == "feedback":
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
                            "version": "1.3",
                            "body": updated_card["body"],
                        },
                    )
                except Exception:
                    error_card = create_error_card("提交回饋失敗。請再試一次。")
                    return InvokeResponse(
                        status=200,
                        body={
                            "type": "AdaptiveCard",
                            "version": "1.3",
                            "body": error_card["body"],
                        },
                    )

            return InvokeResponse(status=400, body="Unknown action")
        except Exception:
            return InvokeResponse(status=500, body="Error processing feedback")

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
                # Local emulator mode: bypass SSO when no AppId/Password configured
                if not self.config.APP_ID or not self.config.APP_PASSWORD:
                    is_emulator = turn_context.activity.channel_id == "emulator"
                    await turn_context.send_activity(
                        build_unauthenticated_welcome(is_emulator, self.config)
                    )
                    return
                # Start SSO Dialog
                await dc.begin_dialog(self.dialog.id)
            else:
                 # Process the message with Genie
                 await self._process_genie_message(turn_context, user_session)

        elif result.status == DialogTurnStatus.Complete:
            # SSO completed
            token_response = result.result
            if token_response and token_response.token:
                user_id = turn_context.activity.from_property.id

                # 使用混合策略取得用戶 email
                # 優先級：JWT Token → Activity Channel Data → Graph API → Placeholder
                name = turn_context.activity.from_property.name or "User"
                email = await EmailExtractor.get_email(
                    turn_context,
                    token_response,
                    fallback_name=name,
                    use_graph_api=True  # 可透過環境變數控制
                )

                # Create Session
                session = UserSession(user_id, email, name)
                self.user_sessions[user_id] = session
                
                await turn_context.send_activity(f"登入成功！歡迎 {name}。")
                is_emulator = turn_context.activity.channel_id == "emulator"
                await turn_context.send_activity(
                    build_authenticated_welcome(session, is_emulator, self.config)
                )
                
                # If there was a pending question (e.g. from before login), we could process it here
                # But typically we just let them ask again.

    async def _process_genie_message(self, turn_context: TurnContext, user_session: UserSession):
        question = turn_context.activity.text
        if not question:
            await turn_context.send_activity("請輸入問題內容。")
            return

        await self._process_genie_question(turn_context, user_session, question)

    async def _process_genie_question(self, turn_context: TurnContext, user_session: UserSession, question: str):
        # 顯示正在輸入
        await turn_context.send_activity(Activity(type=ActivityTypes.typing))

        # 先處理特殊指令
        if await handle_special_commands(
            turn_context,
            question,
            user_session,
            self.config,
            self._format_local_timestamp,
            self.user_sessions,
            self.email_sessions,
        ):
            return
        
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
            if message_id:
                user_session.user_context["last_genie_message_id"] = message_id
                
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
                await send_feedback_card(turn_context, user_session, self.config.ENABLE_FEEDBACK_CARDS)
            elif "data" in response_data:
                # 處理資料表格 - 顯示查詢描述和建議問題
                if "query_description" in response_data and response_data["query_description"]:
                    await turn_context.send_activity(f"📊 {response_data['query_description']}")

                # 分析圖表適用性
                if "columns" in response_data and "data" in response_data:
                    logger.debug(f"開始分析圖表適用性...")
                    logger.debug(f"列信息: {response_data.get('columns')}")
                    logger.debug(f"數據行數: {len(response_data.get('data', {}).get('data_array', []))}")
                    
                    chart_info = ChartAnalyzer.analyze_suitability(response_data["columns"], response_data["data"])
                    if chart_info.get('suitable'):
                        response_data['chart_info'] = chart_info
                        logger.info(f"✅ 圖表適用: {chart_info.get('chart_type')} 圖 (類別: {chart_info.get('category_column')}, 數值: {chart_info.get('value_column')})")
                    else:
                        logger.warning(f"❌ 數據不適合繪製圖表: {chart_info}")

                # 構建並發送資料表格卡片
                if "columns" in response_data and "data" in response_data:
                    try:
                        data_obj = response_data["data"]
                        columns = response_data["columns"]

                        # 從 data object 中提取資料
                        if isinstance(data_obj, dict) and "data_array" in data_obj:
                            data_array = data_obj["data_array"]
                            if data_array:
                                # 構建簡單的表格文字表示 (可選：使用 Adaptive Card)
                                message = "📈 **查詢結果：**\n\n"
                                if columns and isinstance(columns, dict) and "columns" in columns:
                                    col_names = [col.get("name", "Col") for col in columns["columns"][:10]]
                                    message += f"欄位: {', '.join(col_names)}\n\n"

                                    # 顯示前 5 筆資料
                                    message += "```\n"
                                    for i, row in enumerate(data_array[:5]):
                                        message += f"{i+1}. {row}\n"
                                    if len(data_array) > 5:
                                        message += f"... (共 {len(data_array)} 筆資料)\n"
                                    message += "```"

                                await turn_context.send_activity(message)
                            else:
                                await turn_context.send_activity("✅ 查詢成功，但沒有資料返回")
                        else:
                            await turn_context.send_activity("✅ 查詢成功")
                    except Exception as table_error:
                        await turn_context.send_activity(f"顯示資料時發生錯誤: {str(table_error)}")
                
                # 檢查並生成圖表
                if "chart_info" in response_data and response_data["chart_info"]:
                    logger.info(f"🎯 發現圖表信息: {response_data.get('chart_info', {}).get('chart_type')} 圖")
                    logger.debug(f"   數據點數: {len(response_data.get('chart_info', {}).get('data_for_chart', []))}")
                    try:
                        from bot.cards.chart_generator import generate_chart_image
                        from botbuilder.schema import Attachment
                        import base64
                        
                        # 生成圖表圖像
                        image_base64 = generate_chart_image(response_data["chart_info"])
                        image_bytes = base64.b64decode(image_base64)
                        
                        # 方法 1: 發送純圖片附件（適用於模擬器）
                        image_attachment = Attachment(
                            name="chart.png",
                            content_type="image/png",
                            content_url=f"data:image/png;base64,{image_base64}"
                        )
                        
                        chart_type = response_data["chart_info"].get("chart_type", "bar")
                        category_col = response_data["chart_info"].get("category_column", "")
                        value_col = response_data["chart_info"].get("value_column", "")
                        chart_icons = {'bar': '📊', 'pie': '🥧', 'line': '📈'}
                        chart_icon = chart_icons.get(chart_type, '📊')
                        
                        # 發送標題文字
                        await turn_context.send_activity(f"{chart_icon} **{category_col} vs {value_col}**")
                        
                        # 發送圖片
                        await turn_context.send_activity(MessageFactory.attachment(image_attachment))
                        logger.info("✅ 圖表卡片已發送")
                    except Exception as chart_error:
                        logger.error(f"❌ 生成圖表時發生錯誤: {str(chart_error)}", exc_info=True)
                else:
                    logger.debug(f"⏭️ 未發現圖表信息 (chart_info={'chart_info' in response_data})")
                
                # 發送反饋卡片
                await send_feedback_card(turn_context, user_session, self.config.ENABLE_FEEDBACK_CARDS)

                # 處理建議問題
                if "suggested_questions" in response_data and response_data["suggested_questions"]:
                    card = create_suggested_questions_card(response_data["suggested_questions"])
                    if card:
                        await turn_context.send_activity(MessageFactory.attachment(card))
            else:
                await send_feedback_card(turn_context, user_session, self.config.ENABLE_FEEDBACK_CARDS)
                 
        except Exception as e:
            traceback.print_exc()
            error_msg = f"❌ 發生錯誤：{str(e)}\n\n請稍後再試或聯絡管理員 {self.config.ADMIN_CONTACT_EMAIL}"
            await turn_context.send_activity(error_msg)
            await send_feedback_card(turn_context, user_session, self.config.ENABLE_FEEDBACK_CARDS)

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

    async def _get_user_session(self, turn_context: TurnContext) -> Optional[UserSession]:
        user_id = turn_context.activity.from_property.id
        return self.user_sessions.get(user_id)