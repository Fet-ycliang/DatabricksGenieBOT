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
remote 啟動指令：
python -m aiohttp.web -H 0.0.0.0 -P 8000 app:init_func
DEBUG:asyncio:Using proactor: IocpProactor
======== Running on http://0.0.0.0:8000 ========
(Press CTRL+C to quit)

local 啟動指令：
python -m aiohttp.web -P 5168 app:init_func
DEBUG:asyncio:Using proactor: IocpProactor
======== Running on http://localhost:5168 ========
(Press CTRL+C to quit)
"""

from asyncio.log import logger
import os
import json
from collections import defaultdict
from functools import lru_cache
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
    ActivityTypes,
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
from graph_service import GraphService, get_teams_user_info
from chart_generator import create_chart_card_with_image, create_suggested_questions_card


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

# 初始化 Graph Service（如果啟用）
GRAPH_SERVICE = None
if CONFIG.ENABLE_GRAPH_API_AUTO_LOGIN and CONFIG.OAUTH_CONNECTION_NAME:
    GRAPH_SERVICE = GraphService(CONFIG.OAUTH_CONNECTION_NAME)
    logger.info(f"Graph API 自動登入已啟用，使用連線: {CONFIG.OAUTH_CONNECTION_NAME}")
else:
    logger.info("Graph API 自動登入已停用，將使用手動 email 輸入")


class MyBot(ActivityHandler):
    def __init__(self, genie_service: GenieService, graph_service: Optional[GraphService] = None):
        self.genie_service = genie_service
        self.graph_service = graph_service
        self.user_sessions: Dict[str, UserSession] = {}  # 將 Teams 使用者 ID 映射到 UserSession
        self.email_sessions: Dict[str, UserSession] = {}  # 將電子郵件映射到 UserSession 以便於查找
        self.message_feedback: Dict[str, Dict] = {}  # 追蹤每條訊息的回饋
        self.pending_email_input: Dict[str, bool] = {}  # 追蹤等待輸入電子郵件的使用者
        self._user_context_cache: Dict[str, Dict] = {}  # ✅ 用戶上下文快取

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
        
        # 如果啟用 Graph API，嘗試自動取得使用者資訊
        if self.graph_service:
            try:
                user_info = await self.graph_service.get_user_email_and_id(turn_context)
                if user_info and user_info.get('email'):
                    email = user_info['email']
                    name = user_info.get('name') or email.split('@')[0]
                    aad_object_id = user_info.get('id')
                    
                    # 建立新的使用者工作階段
                    session = UserSession(user_id, email, name)
                    session.aad_object_id = aad_object_id  # 儲存 OpenID
                    session.upn = user_info.get('upn')
                    
                    self.user_sessions[user_id] = session
                    self.email_sessions[email] = session
                    
                    logger.info(f"透過 Graph API 自動建立使用者工作階段: {session.get_display_name()}, AAD ID: {aad_object_id}")
                    return session
            except Exception as e:
                logger.warning(f"無法透過 Graph API 取得使用者資訊: {str(e)}")
        
        # 如果 Graph API 未啟用或失敗，嘗試從 Teams channel data 取得基本資訊
        try:
            teams_info = await get_teams_user_info(turn_context)
            if teams_info.get('email'):
                email = teams_info['email']
                name = teams_info.get('name') or email.split('@')[0]
                aad_object_id = teams_info.get('aad_object_id')
                
                session = UserSession(user_id, email, name)
                session.aad_object_id = aad_object_id
                
                self.user_sessions[user_id] = session
                self.email_sessions[email] = session
                
                logger.info(f"從 Teams channel data 建立使用者工作階段: {session.get_display_name()}")
                return session
        except Exception as e:
            logger.warning(f"無法從 Teams 取得使用者資訊: {str(e)}")
        
        # 如果所有自動方法都失敗，需要手動輸入電子郵件
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

    @lru_cache(maxsize=1000)
    def _get_cached_user_context(self, user_id: str, email: str) -> Dict:
        """預載並快取用戶上下文（使用 LRU 快取提升性能）"""
        cache_key = f"{user_id}:{email}"
        if cache_key not in self._user_context_cache:
            self._user_context_cache[cache_key] = {
                'last_question': None,
                'last_response_time': None,
                'last_conversation_id': None,
                'preferred_time_range': '7d',  # 預設偏好
                'query_count': 0,
                'cached_at': datetime.now(timezone.utc).isoformat()
            }
            logger.info(f"🔖 已快取用戶上下文: {email}")
        return self._user_context_cache[cache_key]

    def _invalidate_user_context_cache(self, user_id: str, email: str) -> None:
        """清除特定用戶的上下文快取"""
        cache_key = f"{user_id}:{email}"
        if cache_key in self._user_context_cache:
            del self._user_context_cache[cache_key]
            logger.info(f"🗑️ 已清除用戶上下文快取: {email}")
        # 清除 LRU 快取
        self._get_cached_user_context.cache_clear()

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
                
                # 處理建議問題按鈕點擊
                if action == "ask_question":
                    question = turn_context.activity.value.get("question")
                    if question:
                        # 將問題設為 turn_context.activity.text 並繼續處理
                        turn_context.activity.text = question
                        logger.info(f"偵測到建議問題點擊: {question}")
                    else:
                        logger.error("建議問題點擊中缺少問題內容")
                        return
                
                # 處理回饋按鈕點擊
                elif action == "feedback":
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
            self.graph_service,
        ):
            return
        
        # ✅ 發送 typing indicator
        typing_activity = Activity(
            type=ActivityTypes.typing,
            relates_to=turn_context.activity.relates_to
        )
        await turn_context.send_activity(typing_activity)
        
        # ✅ 立即發送處理中訊息
        await turn_context.send_activity(
            "⏳ **正在分析您的問題...**\n\n"
            "這通常需要 5-20 秒（取決於資料量）"
        )
        
        # 使用使用者上下文處理訊息
        try:
            # ✅ 新增：45秒超時保護
            answer, new_conversation_id, genie_message_id = await asyncio.wait_for(
                self.genie_service.ask(
                    question,
                    CONFIG.DATABRICKS_SPACE_ID,
                    user_session,
                    user_session.conversation_id,
                ),
                timeout=45.0
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
            
            # 如果有圖表信息，發送圖表卡片
            if 'chart_info' in answer_json and answer_json['chart_info'].get('suitable'):
                chart_card = create_chart_card_with_image(answer_json['chart_info'])
                if chart_card:
                    from botbuilder.schema import Attachment
                    chart_attachment = Attachment(
                        content_type="application/vnd.microsoft.card.adaptive",
                        content=chart_card
                    )
                    chart_message = Activity(
                        type=ActivityTypes.message,
                        attachments=[chart_attachment]
                    )
                    await turn_context.send_activity(chart_message)
            
            # 如果有建議問題，發送建議問題卡片
            if 'suggested_questions' in answer_json and answer_json['suggested_questions']:
                suggested_card = create_suggested_questions_card(answer_json['suggested_questions'])
                if suggested_card:
                    from botbuilder.schema import Attachment
                    suggested_attachment = Attachment(
                        content_type="application/vnd.microsoft.card.adaptive",
                        content=suggested_card
                    )
                    suggested_message = Activity(
                        type=ActivityTypes.message,
                        attachments=[suggested_attachment]
                    )
                    await turn_context.send_activity(suggested_message)
            
            # 作為單獨的訊息發送回饋卡
            await send_feedback_card(turn_context, user_session, CONFIG.ENABLE_FEEDBACK_CARDS)
            
        except asyncio.TimeoutError:
            # ✅ 處理超時錯誤
            logger.warning(f"查詢超時，使用者: {user_session.get_display_name()}, 問題: {question}")
            await turn_context.send_activity(
                f"**👤 {user_session.name}**\n\n"
                "⏱️ **查詢超時**\n\n"
                "請嘗試：\n"
                "• 更具體的篩選條件\n"
                "• 較短的時間範圍\n"
                "• 簡單的聚合（如總計）"
            )
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
        # 處理 Adaptive Card 按鈕點擊（回饋提交、建議問題等）
        try:
            action = invoke_value.get("action")
            
            # 處理點擊建議問題按鈕
            if action == "ask_suggested_question":
                question = invoke_value.get("question")
                if not question:
                    return InvokeResponse(status_code=400, body="Missing question data")
                
                logger.info(f"使用者點擊建議問題: {question}")
                
                # 將建議問題作為新的訊息發送到訊息處理流程
                # 建立新的 Activity，就像使用者輸入了這個問題
                suggested_message_activity = Activity(
                    type=ActivityTypes.message,
                    text=question,
                    from_property=turn_context.activity.from_property,
                    conversation=turn_context.activity.conversation,
                    channel_id=turn_context.activity.channel_id,
                    service_url=turn_context.activity.service_url,
                    timestamp=datetime.now(timezone.utc)
                )
                
                # 建立新的 turn context 來處理建議問題
                suggested_turn_context = TurnContext(
                    adapter=ADAPTER,
                    activity=suggested_message_activity,
                    on_send_activities=turn_context.on_send_activities,
                    on_update_activity=turn_context.on_update_activity,
                    on_delete_activity=turn_context.on_delete_activity
                )
                
                # 處理建議問題（遞迴調用 on_message_activity）
                await self.on_message_activity(suggested_turn_context)
                
                # 返回成功回應
                return InvokeResponse(
                    status_code=200,
                    body={"status": "success", "message": "建議問題已提交"}
                )
            
            # 處理回饋動作
            elif action == "feedback":
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
                
                # 🎫 如果 Graph API 已啟用且成功取得使用者資訊，顯示用戶資料卡片
                if user_session and self.graph_service and CONFIG.ENABLE_GRAPH_API_AUTO_LOGIN:
                    try:
                        user_info = await self.graph_service.get_user_email_and_id(turn_context)
                        if user_info and user_info.get('email'):
                            # 取得完整的使用者資料（如果可用）
                            token_response = await self.graph_service.get_user_token(turn_context)
                            if token_response:
                                full_profile = await self.graph_service.get_user_profile(token_response.token)
                                user_info.update(full_profile)
                            
                            # 創建並發送使用者資料卡片
                            from graph_service import GraphService
                            user_card = GraphService.create_user_profile_card(user_info)
                            
                            from botbuilder.schema import Attachment
                            card_attachment = Attachment(
                                content_type="application/vnd.microsoft.card.adaptive",
                                content=user_card
                            )
                            
                            card_activity = Activity(
                                type="message",
                                attachments=[card_attachment]
                            )
                            
                            await turn_context.send_activity(card_activity)
                            logger.info(f"✅ 已發送使用者資料卡片給 {user_session.get_display_name()}")
                    except Exception as e:
                        logger.warning(f"⚠️ 無法發送使用者資料卡片: {str(e)}")


BOT = MyBot(GENIE_SERVICE, GRAPH_SERVICE)


async def health_check(req: Request) -> Response:
    """
    Azure Web App Health Check 端點
    用於監控應用程式的健康狀態
    
    返回：
    - 200: 應用程式運行正常
    - 503: 應用程式異常
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {
                "app": "running",
                "databricks": "not_checked",
                "graph_api": "not_checked"
            }
        }
        
        # 檢查 Databricks 連接
        try:
            if GENIE_SERVICE and hasattr(GENIE_SERVICE, 'client'):
                health_status["checks"]["databricks"] = "connected"
            else:
                health_status["checks"]["databricks"] = "unavailable"
        except Exception as e:
            logger.warning(f"Databricks health check failed: {str(e)}")
            health_status["checks"]["databricks"] = "error"
        
        # 檢查 Graph API 連接
        try:
            if GRAPH_SERVICE and hasattr(GRAPH_SERVICE, 'client_id'):
                health_status["checks"]["graph_api"] = "configured"
            else:
                health_status["checks"]["graph_api"] = "not_configured"
        except Exception as e:
            logger.warning(f"Graph API health check failed: {str(e)}")
            health_status["checks"]["graph_api"] = "error"
        
        return json_response(data=health_status, status=200)
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        error_response = {
            "status": "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        }
        return json_response(data=error_response, status=503)


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
    # 健康檢查端點
    APP.router.add_get("/api/health", health_check)
    # Bot 訊息端點
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