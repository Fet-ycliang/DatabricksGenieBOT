"""
Databricks Genie 機器人

作者: Luiz Carrossoni Neto, Ryan Bates
修訂版本: 1.2

此腳本實作了一個與 Databricks Genie API 互動的實驗性聊天機器人。該機器人透過聊天介面促進與 Databricks AI 助理 Genie 的對話。

注意：這是實驗性程式碼，不適用於生產環境使用。
這是一個測試


5 月 2 日更新以反映 Databricks API 變更 https://www.databricks.com/blog/genie-conversation-apis-public-preview
8 月 5 日更新以反映 Microsoft Azure 不再支援多租戶機器人
10 月 8 日更新以加入使用者工作階段管理、使用者上下文和 Genie API 回饋功能
"""

"""
啟動指令：
python3 -m aiohttp.web -H 0.0.0.0 -P 8000 app:init_func

"""

from asyncio.log import logger
import os
import json
from typing import Dict, List, Optional
from aiohttp import web
import asyncio
import traceback
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from aiohttp.web import Request, Response, json_response
from botbuilder.core import (
    BotFrameworkAdapterSettings,
    BotFrameworkAdapter,
    ActivityHandler,
    TurnContext,
)
from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.integration.aiohttp import (
    CloudAdapter,
    ConfigurationBotFrameworkAuthentication,
)
from botbuilder.schema import (
    Activity,
    ChannelAccount,
    InvokeResponse,
)

from config import DefaultConfig
from genie_service import GenieService, process_query_results
from user_session import (
    UserSession,
    get_sample_questions,
    is_conversation_timed_out,
    is_valid_email,
)
from identity_flow import handle_pending_email_input, handle_user_identification
from command_handler import handle_special_commands
from feedback_cards import create_error_card, create_thank_you_card, send_feedback_card
from welcome_messages import build_authenticated_welcome, build_unauthenticated_welcome


CONFIG = DefaultConfig()

try:
    LOCAL_TIMEZONE = ZoneInfo(CONFIG.TIMEZONE)
    LOCAL_TIMEZONE_LABEL = CONFIG.TIMEZONE
except Exception as tz_error:
    logger.warning(
        "Invalid TIMEZONE %s supplied, falling back to UTC (%s)",
        CONFIG.TIMEZONE,
        tz_error,
    )
    LOCAL_TIMEZONE = timezone.utc
    LOCAL_TIMEZONE_LABEL = "UTC"


def format_local_timestamp(dt: Optional[datetime]) -> str:
    """Format timestamps in the configured timezone for user-facing text."""
    if not dt:
        return "N/A"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    localized = dt.astimezone(LOCAL_TIMEZONE)
    return localized.strftime('%Y-%m-%d %H:%M:%S ') + LOCAL_TIMEZONE_LABEL


# 用於使用 Bot Framework Emulator 進行本地開發，使用 BotFrameworkAdapter
if CONFIG.APP_ID and CONFIG.APP_PASSWORD:
    # 生產環境：使用 CloudAdapter
    ADAPTER = CloudAdapter(ConfigurationBotFrameworkAuthentication(CONFIG))
else:
    # 本地測試：使用帶有空憑證的 BotFrameworkAdapter
    SETTINGS = BotFrameworkAdapterSettings("", "")
    ADAPTER = BotFrameworkAdapter(SETTINGS)


async def on_error(context: TurnContext, error: Exception):
    # 此檢查將錯誤寫入控制台日誌與 App Insights。
    # 注意：在生產環境中，您應該考慮將此記錄到 Azure
    #       Application Insights。
    logger.error(f"機器人發生未處理的錯誤: {str(error)}")
    traceback.print_exc()

    # 不要向使用者發送錯誤訊息 - 僅記錄錯誤
    # 這可以防止出現「機器人遇到錯誤」的訊息
    logger.info("錯誤已記錄，但未顯示給使用者以避免困惑")


ADAPTER.on_turn_error = on_error

GENIE_SERVICE = GenieService(CONFIG)



class MyBot(ActivityHandler):
    def __init__(self, genie_service: GenieService):
        self.genie_service = genie_service
        self.user_sessions: Dict[str, UserSession] = {}  # 將 Teams 使用者 ID 映射到 UserSession
        self.email_sessions: Dict[str, UserSession] = {}  # 將電子郵件映射到 UserSession 以便於查找
        self.message_feedback: Dict[str, Dict] = {}  # 追蹤每條訊息的回饋
        self.pending_email_input: Dict[str, bool] = {}  # 追蹤等待輸入電子郵件的使用者

    async def get_or_create_user_session(self, turn_context: TurnContext) -> UserSession:
        # 根據 Teams 使用者資訊獲取或建立使用者工作階段
        user_id = turn_context.activity.from_property.id
        
        # 檢查我們是否已經有此使用者的工作階段
        if user_id in self.user_sessions:
            session = self.user_sessions[user_id]
            
            # 檢查對話是否已超時（4 小時）
            if is_conversation_timed_out(session):
                logger.info(f"使用者 {session.get_display_name()} 的對話已超時，正在重置對話")
                # 重置對話 ID 和使用者上下文以重新開始
                session.conversation_id = None
                session.user_context.pop('last_conversation_id', None)
                # 更新活動時間
                session.update_activity()
                return session
            else:
                # 更新活動工作階段的活動時間
                session.update_activity()
                return session
        
        # 對於所有環境，需要手動輸入電子郵件
        # 這確保了模擬器和 Teams 之間的一致行為
        return None

    async def _create_session_with_manual_email(self, turn_context: TurnContext, email: str) -> UserSession:
        # 使用手動提供的電子郵件建立使用者工作階段
        user_id = turn_context.activity.from_property.id
        user_name = getattr(turn_context.activity.from_property, 'name', None) or email.split('@')[0]
        
        # 建立新的使用者工作階段
        session = UserSession(user_id, email, user_name)
        self.user_sessions[user_id] = session
        self.email_sessions[email] = session
        
        # 從待處理電子郵件輸入中移除
        if user_id in self.pending_email_input:
            del self.pending_email_input[user_id]
        
        logger.info(f"已為 {session.get_display_name()} 建立帶有手動電子郵件的使用者工作階段")
        return session

    async def on_message_activity(self, turn_context: TurnContext):
        # 記錄所有訊息活動的除錯日誌
        logger.info(f"訊息活動類型: {turn_context.activity.type}")
        logger.info(f"訊息活動名稱: {turn_context.activity.name}")
        logger.info(f"訊息活動值: {turn_context.activity.value}")
        logger.info(f"訊息活動文字: {turn_context.activity.text}")
        
        # 處理文字可能為 None 的情況（例如，Adaptive Card 互動）
        if not turn_context.activity.text:
            # 檢查這是否是 Adaptive Card 按鈕點擊
            if turn_context.activity.value and isinstance(turn_context.activity.value, dict):
                action = turn_context.activity.value.get("action")
                if action == "feedback":
                    logger.info("在訊息活動中偵測到 Adaptive Card 回饋按鈕點擊")
                    # 作為回饋提交處理
                    try:
                        message_id = turn_context.activity.value.get("messageId")
                        user_id = turn_context.activity.value.get("userId")
                        feedback = turn_context.activity.value.get("feedback")
                        
                        if not all([message_id, user_id, feedback]):
                            logger.error("訊息活動中缺少必要的回饋資料")
                            return
                        
                        # 儲存回饋資料
                        feedback_key = f"{user_id}_{message_id}"
                        user_session = self.user_sessions.get(user_id)
                        self.message_feedback[feedback_key] = {
                            "message_id": message_id,
                            "user_id": user_id,
                            "feedback": feedback,
                            "conversation_id": user_session.conversation_id if user_session else None,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "user_session": user_session.to_dict() if user_session else None
                        }
                        
                        # 發送回饋到 Databricks Genie API
                        try:
                            await self.genie_service.send_feedback(
                                user_session,
                                message_id,
                                feedback,
                            )

                            # 發送感謝訊息
                            await turn_context.send_activity("✅ 感謝您的回饋！")

                        except Exception as e:
                            logger.error(f"發送回饋到 Genie API 失敗: {str(e)}")
                            await turn_context.send_activity("❌ 提交回饋失敗。請再試一次。")
                        
                        return
                        
                    except Exception as e:
                        logger.error(f"處理訊息活動中的回饋時發生錯誤: {str(e)}")
                        return
            
            logger.info("收到沒有文字內容的訊息活動，跳過")
            return
            
        question = turn_context.activity.text.strip()
        user_id = turn_context.activity.from_property.id
        
        sample_questions = get_sample_questions(CONFIG.SAMPLE_QUESTIONS)
        handled_pending_email = await handle_pending_email_input(
            user_id,
            question,
            turn_context,
            self.pending_email_input,
            self._create_session_with_manual_email,
            is_valid_email,
            sample_questions,
        )
        if handled_pending_email:
            return
        
        # 獲取或建立使用者工作階段
        user_session = await self.get_or_create_user_session(turn_context)
        
        # 如果我們無法建立工作階段（沒有電子郵件），要求使用者識別自己
        if not user_session:
            await handle_user_identification(turn_context, question, CONFIG, self.pending_email_input)
            return
        
        # 首先處理特殊指令（在檢查超時重置之前）
        if await handle_special_commands(
            turn_context,
            question,
            user_session,
            CONFIG,
            format_local_timestamp,
            self.user_sessions,
            self.email_sessions,
        ):
            return
        
        # 檢查對話是否因超時而重置（僅針對資料問題，不針對指令）
        if user_session.conversation_id is None and user_session.user_id in self.user_sessions:
            # 這意味著對話因超時而重置
            await turn_context.send_activity(
                "⏰ **對話已重置**\n\n"
                "您之前的對話已過期（超過 4 小時無活動）。"
                "正在使用新的對話上下文重新開始。\n\n"
                "我現在正在處理您的回答！"
            )
        
        # 使用使用者上下文處理訊息
        try:
            answer, new_conversation_id, genie_message_id = await self.genie_service.ask(
                question,
                CONFIG.DATABRICKS_SPACE_ID,
                user_session,
                user_session.conversation_id,
            )
            
            # 更新使用者工作階段的新對話 ID 並儲存特定訊息 ID 以供回饋
            user_session.conversation_id = new_conversation_id
            user_session.user_context['last_question'] = question
            user_session.user_context['last_response_time'] = datetime.now(timezone.utc).isoformat()
            user_session.user_context['last_genie_message_id'] = genie_message_id

            answer_json = json.loads(answer)
            response = process_query_results(answer_json)
            
            # 將使用者上下文添加到回應中
            response = f"**👤 {user_session.name}**\n\n{response}"

            # 發送主要回應
            await turn_context.send_activity(response)
            
            # 作為單獨的訊息發送回饋卡
            await send_feedback_card(turn_context, user_session, CONFIG.ENABLE_FEEDBACK_CARDS)
            
        except json.JSONDecodeError:
            await turn_context.send_activity(
                f"**👤 {user_session.name}**\n\n❌ 無法解碼伺服器的回應。"
            )
            await send_feedback_card(turn_context, user_session, CONFIG.ENABLE_FEEDBACK_CARDS)
        except Exception as e:
            logger.error(f"處理使用者 {user_session.get_display_name()} 的訊息時發生錯誤: {str(e)}")
            await turn_context.send_activity(
                f"**👤 {user_session.name}**\n\n❌ 處理您的請求時發生錯誤。"
            )
            await send_feedback_card(turn_context, user_session, CONFIG.ENABLE_FEEDBACK_CARDS)

    async def on_invoke_activity(self, turn_context: TurnContext) -> InvokeResponse:
        # 處理調用活動（如 Adaptive Card 按鈕點擊）
        try:
            logger.info(f"Received invoke activity: {turn_context.activity.name}")
            logger.info(f"Invoke activity value: {turn_context.activity.value}")
            
            # 檢查這是否是 Adaptive Card 調用
            if turn_context.activity.name == "adaptiveCard/action":
                invoke_value = turn_context.activity.value
                logger.info(f"正在處理 Adaptive Card 調用，值為: {invoke_value}")
                return await self.on_adaptive_card_invoke(turn_context, invoke_value)
            
            # 如果需要，處理其他調用活動
            logger.info(f"未處理的調用活動類型: {turn_context.activity.name}")
            return InvokeResponse(status_code=200, body="OK")
            
        except Exception as e:
            logger.error(f"處理調用活動時發生錯誤: {str(e)}")
            return InvokeResponse(status_code=500, body="Error processing invoke activity")

    async def on_adaptive_card_invoke(self, turn_context: TurnContext, invoke_value: Dict) -> InvokeResponse:
        # 處理 Adaptive Card 按鈕點擊（回饋提交）
        try:
            action = invoke_value.get("action")
            
            if action == "feedback":
                message_id = invoke_value.get("messageId")
                user_id = invoke_value.get("userId")
                feedback = invoke_value.get("feedback")
                
                if not all([message_id, user_id, feedback]):
                    return InvokeResponse(status_code=400, body="Missing required feedback data")
                
                # 儲存回饋資料
                feedback_key = f"{user_id}_{message_id}"
                user_session = self.user_sessions.get(user_id)
                self.message_feedback[feedback_key] = {
                    "message_id": message_id,
                    "user_id": user_id,
                    "feedback": feedback,
                    "conversation_id": user_session.conversation_id if user_session else None,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "user_session": user_session.to_dict() if user_session else None
                }
                
                # 發送回饋到 Databricks Genie API
                try:
                    await self.genie_service.send_feedback(user_session, message_id, feedback)

                    # 返回帶有感謝訊息的更新卡片
                    updated_card = create_thank_you_card()

                    return InvokeResponse(
                        status_code=200,
                        body={
                            "type": "AdaptiveCard",
                            "version": "1.3",
                            "body": updated_card["body"],
                        },
                    )
                except Exception as e:
                    logger.error(f"發送回饋到 Genie API 失敗: {str(e)}")

                    # 返回錯誤卡片
                    error_card = create_error_card("提交回饋失敗。請再試一次。")

                    return InvokeResponse(
                        status_code=200,
                        body={
                            "type": "AdaptiveCard",
                            "version": "1.3",
                            "body": error_card["body"],
                        },
                    )
            
            return InvokeResponse(status_code=400, body="Unknown action")
            
        except Exception as e:
            logger.error(f"處理 Adaptive Card 調用時發生錯誤: {str(e)}")
            return InvokeResponse(status_code=500, body="Error processing feedback")

    async def on_members_added_activity(
        self, members_added: List[ChannelAccount], turn_context: TurnContext
    ):
        ## 列印 "Members added" 以便除錯
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
            # 嘗試取得使用者資訊以提供個人化歡迎
                user_session = await self.get_or_create_user_session(turn_context)
                
                is_emulator = turn_context.activity.channel_id == "emulator"
                if user_session:
                    welcome_message = build_authenticated_welcome(user_session, is_emulator, CONFIG)
                else:
                    welcome_message = build_unauthenticated_welcome(is_emulator, CONFIG)

                await turn_context.send_activity(welcome_message)


BOT = MyBot(GENIE_SERVICE)


async def messages(req: Request) -> Response:
    if "application/json" in req.headers["Content-Type"]:
        body = await req.json()
    else:
        return Response(status=415)

    activity = Activity().deserialize(body)
    auth_header = req.headers.get("Authorization", "")

    try:
        # 處理不同的介面卡類型
        if hasattr(ADAPTER, 'process'):
            # CloudAdapter
            response = await ADAPTER.process(req, BOT)
            if response:
                return json_response(data=response.body, status=response.status)
            return Response(status=201)
        else:
            # BotFrameworkAdapter - 使用正確簽章的 process_activity 方法
            response = await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
            if response:
                return json_response(data=response.body, status=response.status)
            return Response(status=201)
    except Exception as e:
        logger.error(f"處理請求時發生錯誤: {str(e)}")
        return Response(status=500)


def init_func(argv):
    APP = web.Application(middlewares=[aiohttp_error_middleware])
    APP.router.add_post("/api/messages", messages)
    return APP


if __name__ == "__main__":
    APP = init_func(None)
    try:
        HOST = "0.0.0.0"
        PORT = int(os.environ.get("PORT", CONFIG.PORT))
        web.run_app(APP, host=HOST, port=PORT)
    except Exception as error:
        raise error