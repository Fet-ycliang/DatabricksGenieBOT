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
import logging
from typing import Dict, List, Optional
from dotenv import load_dotenv
from aiohttp import web
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.dashboards import GenieAPI
import asyncio
import sys
import traceback
from datetime import datetime, timezone, timedelta
from http import HTTPStatus
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
    ConversationReference,
    ActivityTypes,
    ChannelAccount,
    InvokeResponse,
)
import requests
import re

from config import DefaultConfig


CONFIG = DefaultConfig()


class UserSession:
    # 代表一個使用者工作階段，使用電子郵件作為識別
    def __init__(self, user_id: str, email: str, name: str = None):
        self.user_id = user_id  # Teams 使用者 ID
        self.email = email
        self.name = name or email.split('@')[0]  # 如果沒有提供名稱，使用電子郵件前綴作為名稱
        self.conversation_id = None
        self.created_at = datetime.now(timezone.utc)
        self.last_activity = datetime.now(timezone.utc)
        self.is_authenticated = True  # 對於 Teams 使用者總是為真
        self.user_context = {}
    
    def update_activity(self):
        # 更新最後活動時間戳記
        self.last_activity = datetime.now(timezone.utc)
    
    def to_dict(self):
        # 將工作階段轉換為字典以進行記錄/除錯
        return {
            "user_id": self.user_id,
            "email": self.email,
            "name": self.name,
            "conversation_id": self.conversation_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "is_authenticated": self.is_authenticated
        }
    
    def get_display_name(self):
        # 獲取使用者的友善顯示名稱
        return f"{self.name} ({self.email})"

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

# 初始化帶有錯誤處理的 Databricks 客戶端
def get_databricks_client():
    # 獲取具有適當錯誤處理的 Databricks WorkspaceClient
    try:
        # 除錯環境變數載入
        logger.info(f"正在載入 Databricks 配置...")
        logger.info(f"DATABRICKS_HOST: {CONFIG.DATABRICKS_HOST}")
        logger.info(f"DATABRICKS_TOKEN 存在: {bool(CONFIG.DATABRICKS_TOKEN)}")
        logger.info(f"DATABRICKS_TOKEN 長度: {len(CONFIG.DATABRICKS_TOKEN) if CONFIG.DATABRICKS_TOKEN else 0}")
        
        if not CONFIG.DATABRICKS_TOKEN:
            raise ValueError("DATABRICKS_TOKEN environment variable is not set")
        
        client = WorkspaceClient(
            host=CONFIG.DATABRICKS_HOST, 
            token=CONFIG.DATABRICKS_TOKEN
        )
        logger.info("Databricks 客戶端初始化成功")
        return client
    except Exception as e:
        logger.error(f"初始化 Databricks 客戶端失敗: {str(e)}")
        raise

# 初始化客戶端
workspace_client = get_databricks_client()
genie_api = GenieAPI(workspace_client.api_client)


async def ask_genie(
    question: str, space_id: str, user_session: UserSession, conversation_id: Optional[str] = None
) -> tuple[str, str, str]:
    try:
        # 將使用者上下文添加到問題中，以便在 Databricks 中進行更好的追蹤
        contextual_question = f"[{user_session.email}] {question}"
        
        loop = asyncio.get_running_loop()
        if conversation_id is None:
            # 開始一個新的對話
            initial_message = await loop.run_in_executor(
                None, genie_api.start_conversation_and_wait, space_id, contextual_question
            )
            conversation_id = initial_message.conversation_id
        else:
            # 使用新訊息繼續現有的對話
            initial_message = await loop.run_in_executor(
                None, genie_api.create_message_and_wait, space_id, conversation_id, contextual_question
            )
           
        query_result = None
        if initial_message.query_result is not None:
            query_result = await loop.run_in_executor(
                None,
                genie_api.get_message_attachment_query_result,
                #genie_api.get_message_query_result,
                space_id,
                initial_message.conversation_id,
                initial_message.message_id,
                initial_message.attachments[0].attachment_id,
           )
        message_content = await loop.run_in_executor(
            None,
            genie_api.get_message,
            space_id,
            initial_message.conversation_id,
            initial_message.message_id,
        )
        if query_result and query_result.statement_response:
            results = await loop.run_in_executor(
                None,
                workspace_client.statement_execution.get_statement,
                query_result.statement_response.statement_id,
            )

            query_description = ""
            for attachment in message_content.attachments:
                if attachment.query and attachment.query.description:
                    query_description = attachment.query.description
                    break

            return (
                json.dumps(
                    {
                        "columns": results.manifest.schema.as_dict(),
                        "data": results.result.as_dict(),
                        "query_description": query_description,
                    }
                ),
                conversation_id,
                initial_message.message_id,
            )

        if message_content.attachments:
            for attachment in message_content.attachments:
                if attachment.text and attachment.text.content:
                    return (
                        json.dumps({"message": attachment.text.content}),
                        conversation_id,
                        initial_message.message_id,
                    )

        return json.dumps({"message": message_content.content}), conversation_id, initial_message.message_id
    except Exception as e:
        error_str = str(e).lower()  # 轉換為小寫以進行不區分大小寫的匹配
        error_original = str(e)  # 保留原始錯誤訊息以進行記錄
        logger.error(f"ask_genie 為使用者 {user_session.get_display_name()} 處理時發生錯誤: {error_original}")
        
        # 檢查 IP ACL 封鎖 - 尋找 "blocked" + "ip acl" 模式
        # 錯誤訊息格式："Source IP address: X.X.X.X is blocked by Databricks IP ACL for workspace"
        if "ip acl" in error_str and "blocked" in error_str:
            logger.error(f"偵測到 IP ACL 封鎖: {error_original}")
            return (
                json.dumps({
                    "error": "⚠️ **IP 存取被封鎖**\n\n"
                            "機器人的 IP 地址被 Databricks 帳戶 IP 存取控制清單 (ACL) 封鎖。\n\n"
                            "**需要管理員操作：**\n"
                            "請查看 TROUBLESHOOTING.md 文件，以獲取有關將機器人的 IP 地址添加到 Databricks 帳戶 IP 允許清單的說明。"
                }),
                conversation_id,
                None,
            )
        
        # 其他情況的通用錯誤
        return (
            json.dumps({"error": "處理您的請求時發生錯誤。"}),
            conversation_id,
            None,
        )


def process_query_results(answer_json: Dict) -> str:
    response = ""
    if "query_description" in answer_json and answer_json["query_description"]:
        response += f"## 查詢說明\n\n{answer_json['query_description']}\n\n"

    if "columns" in answer_json and "data" in answer_json:
        response += "## 查詢結果\n\n"
        columns = answer_json["columns"]
        data = answer_json["data"]
        if isinstance(columns, dict) and "columns" in columns:
            header = "| " + " | ".join(col["name"] for col in columns["columns"]) + " |"
            separator = "|" + "|".join(["---" for _ in columns["columns"]]) + "|"
            response += header + "\n" + separator + "\n"
            for row in data["data_array"]:
                formatted_row = []
                for value, col in zip(row, columns["columns"]):
                    if value is None:
                        formatted_value = "NULL"
                    elif col["type_name"] in ["DECIMAL", "DOUBLE", "FLOAT"]:
                        formatted_value = f"{float(value):,.2f}"
                    elif col["type_name"] in ["INT", "BIGINT", "LONG"]:
                        formatted_value = f"{int(value):,}"
                    else:
                        formatted_value = str(value)
                    formatted_row.append(formatted_value)
                response += "| " + " | ".join(formatted_row) + " |\n"
        else:
            response += f"Unexpected column format: {columns}\n\n"
    elif "error" in answer_json:
        response += f"{answer_json['error']}\n\n"
    elif "message" in answer_json:
        response += f"{answer_json['message']}\n\n"
    else:
        response += "無可用資料。\n\n"

    return response


class MyBot(ActivityHandler):
    def __init__(self):
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
            if self._is_conversation_timed_out(session):
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

    def _is_valid_email(self, email: str) -> bool:
        # 驗證電子郵件地址格式
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email) is not None

    def _is_conversation_timed_out(self, user_session: UserSession) -> bool:
        # 檢查對話是否已超時（4 小時）
        if not user_session:
            return False
        
        time_since_last_activity = datetime.now(timezone.utc) - user_session.last_activity
        timeout_threshold = timedelta(hours=4)
        
        return time_since_last_activity > timeout_threshold

    def _get_sample_questions(self) -> List[str]:
        # 從配置中解析範例問題（以分號分隔）
        questions_str = CONFIG.SAMPLE_QUESTIONS
        if questions_str:
            # 按分號分割並去除空白
            questions = [q.strip() for q in questions_str.split(';') if q.strip()]
            return questions if questions else [
                "What data is available?",
                "Can you explain the datasets?",
                "What questions should I ask?"
            ]
        else:
            # 後備預設問題
            return [
                "What data is available?",
                "Can you explain the datasets?",
                "What questions should I ask?"
            ]

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

    def create_feedback_card(self, message_id: str, user_id: str) -> Dict:
        # 建立帶有讚/倒讚回饋按鈕的 Adaptive Card
        return {
            "type": "AdaptiveCard",
            "version": "1.3",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "這個回應有幫助嗎？",
                    "size": "Small",
                    "color": "Default"
                }
            ],
            "actions": [
                {
                    "type": "Action.Submit",
                    "title": "👍",
                    "data": {
                        "action": "feedback",
                        "messageId": message_id,
                        "userId": user_id,
                        "feedback": "positive"
                    }
                },
                {
                    "type": "Action.Submit",
                    "title": "👎",
                    "data": {
                        "action": "feedback",
                        "messageId": message_id,
                        "userId": user_id,
                        "feedback": "negative"
                    }
                }
            ]
        }

    def create_thank_you_card(self) -> Dict:
        # 建立感謝卡以在提交後替換回饋按鈕
        return {
            "type": "AdaptiveCard",
            "version": "1.3",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "✅ 感謝您的回饋！",
                    "size": "Small",
                    "color": "Good"
                }
            ]
        }

    def create_error_card(self, error_message: str) -> Dict:
        # 建立錯誤卡以在回饋提交失敗時顯示
        return {
            "type": "AdaptiveCard",
            "version": "1.3",
            "body": [
                {
                    "type": "TextBlock",
                    "text": f"❌ {error_message}",
                    "size": "Small",
                    "color": "Attention"
                }
            ]
        }

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
                            await self._send_feedback_to_api(feedback_key, self.message_feedback[feedback_key])
                            
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
        
        # 檢查使用者是否正在等待手動提供電子郵件
        if user_id in self.pending_email_input:
            if question.lower() == "cancel":
                # 使用者想要取消電子郵件輸入
                del self.pending_email_input[user_id]
                await turn_context.send_activity(
                    "❌ **電子郵件輸入已取消**\n\n"
                    "您可以稍後輸入任何訊息再試一次。如果需要，我會再次詢問您的電子郵件。"
                )
                return
            elif self._is_valid_email(question):
                # 使用者提供了有效的電子郵件
                user_session = await self._create_session_with_manual_email(turn_context, question)
                
                # 根據空間 ID 獲取範例問題
                sample_questions = self._get_sample_questions()
                questions_text = "\n".join([f"- \"{q}\"" for q in sample_questions])
                
                await turn_context.send_activity(
                    f"✅ **電子郵件已確認！**\n\n"
                    f"歡迎，{user_session.name}！我已成功將您登入為 {user_session.email}。\n\n"
                    f"現在您可以詢問有關您資料的問題。試著問類似這樣的問題：\n"
                    f"{questions_text}"
                )
                return
            else:
                await turn_context.send_activity(
                    "❌ **無效的電子郵件格式**\n\n"
                    "請提供有效的電子郵件地址（例如：john.doe@company.com）。\n\n"
                    "輸入 `cancel` 停止電子郵件輸入過程。"
                )
                return
        
        # 獲取或建立使用者工作階段
        user_session = await self.get_or_create_user_session(turn_context)
        
        # 如果我們無法建立工作階段（沒有電子郵件），要求使用者識別自己
        if not user_session:
            await self._handle_user_identification(turn_context, question)
            return
        
        # 首先處理特殊指令（在檢查超時重置之前）
        if await self._handle_special_commands(turn_context, question, user_session):
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
            answer, new_conversation_id, genie_message_id = await ask_genie(
                question, CONFIG.DATABRICKS_SPACE_ID, user_session, user_session.conversation_id
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
            await self._send_feedback_card(turn_context, user_session)
            
        except json.JSONDecodeError:
            await turn_context.send_activity(
                f"**👤 {user_session.name}**\n\n❌ 無法解碼伺服器的回應。"
            )
            # 對於錯誤回應也發送回饋卡
            await self._send_feedback_card(turn_context, user_session)
        except Exception as e:
            logger.error(f"處理使用者 {user_session.get_display_name()} 的訊息時發生錯誤: {str(e)}")
            await turn_context.send_activity(
                f"**👤 {user_session.name}**\n\n❌ 處理您的請求時發生錯誤。"
            )
            # 對於錯誤回應也發送回饋卡
            await self._send_feedback_card(turn_context, user_session)

    async def _handle_user_identification(self, turn_context: TurnContext, question: str):
        # 處理無法獲取使用者電子郵件的情況
        user_id = turn_context.activity.from_property.id
        
        if question.lower() in ["help", "/help", "commands", "/commands"]:
            help_message = f"""🤖 **Databricks Genie 機器人資訊**

**我能做什麼：**
我是一個 Teams 機器人，連接到 Databricks Genie Space，讓您可以直接在 Teams 中透過自然語言查詢與您的資料互動。

**我如何運作：**
• 我使用設定的憑證連接到您的 Databricks 工作區
• 您的對話上下文會在工作階段之間保留，以保持連續性
• 我會記住我們的對話歷史，以提供更好的後續回應

**工作階段管理：**
• 對話在閒置 **4 小時** 後會自動重置
• 您可以隨時輸入 `reset` 或 `new chat` 手動重置
• 您的電子郵件 **僅用於在 Genie 中記錄查詢** - 不用於 AI 處理

**可用指令：**
• `help` - 顯示此資訊
• `info` - 獲取入門協助
• `whoami` - 顯示您的使用者資訊
• `reset` - 開始新的對話
• `new chat` - 開始新的對話
• `logout` - 清除您的工作階段

**需要協助？**
請聯絡機器人管理員：{CONFIG.ADMIN_CONTACT_EMAIL}"""
            
            await turn_context.send_activity(help_message)
        elif question.lower() in ["info", "/info"]:
            info_text = """🤖 **歡迎使用 Genie 機器人 - 需要使用者登入**

我需要您的電子郵件地址來記錄 Genie 中的查詢以進行追蹤。

**快速開始：**
- 輸入 `email` 提供您的電子郵件地址
- 我將驗證格式並建立您的工作階段

**接下來會發生什麼：**
- 登入後，您可以詢問有關您資料的問題
- 我會記住我們的對話上下文
- 您可以詢問後續問題

**了解更多：**
- 輸入 `help` 了解更多關於 Genie 機器人的資訊
- 輸入 `info` 獲取入門協助

準備好開始了嗎？輸入 `email` 提供您的電子郵件地址！"""
            await turn_context.send_activity(info_text)
        elif question.lower() in ["email", "provide email", "enter email"]:
            # 使用者想要手動提供電子郵件
            self.pending_email_input[user_id] = True
            await turn_context.send_activity(
                "📧 **Genie 使用者登入**\n\n"
                "請提供您的電子郵件地址（例如：captain.planet@company.com）。\n\n"
                "如果您想停止此過程，請輸入 `cancel`。"
            )
        else:
            await turn_context.send_activity(
                "🤖 **歡迎使用 Genie 機器人**\n\n"
                "我需要您的電子郵件地址來記錄 Genie 中的查詢以進行追蹤。\n\n"
                "**快速選項：**\n"
                "- 輸入 `email` 提供您的電子郵件地址\n"
                "- 輸入 `help` 了解更多關於 Genie 機器人的資訊\n"
                "- 輸入 `info` 獲取入門協助\n\n"
                "登入後，您就可以詢問有關您資料的問題！"
            )

    async def _handle_special_commands(self, turn_context: TurnContext, question: str, user_session: UserSession) -> bool:
        # 處理特殊指令。如果指令已處理，則返回 True。
        
        # 用於設定身分的特殊模擬器指令
        if question.lower().startswith("/setuser ") and turn_context.activity.channel_id == "emulator":
            # 格式：/setuser john.doe@company.com John Doe
            parts = question.split(" ", 2)
            if len(parts) >= 2:
                email = parts[1]
                name = parts[2] if len(parts) > 2 else email.split('@')[0]
                
                # 更新現有工作階段或建立新工作階段
                user_id = turn_context.activity.from_property.id
                session = UserSession(user_id, email, name)
                self.user_sessions[user_id] = session
                self.email_sessions[email] = session
                
                await turn_context.send_activity(
                    f"✅ **Identity Updated!**\n\n"
                    f"**Name:** {session.name}\n"
                    f"**Email:** {session.email}\n\n"
                    f"You can now ask me questions about your data!"
                )
                return True
            else:
                await turn_context.send_activity(
                    "❌ **Invalid format**\n\n"
                    "Use: `/setuser your.email@company.com Your Name`\n"
                    "Example: `/setuser john.doe@company.com John Doe`"
                )
                return True
        
        # Info 指令
        if question.lower() in ["info", "/info"]:
            is_emulator = turn_context.activity.channel_id == "emulator"
            
            info_text = f"""🤖 **Databricks Genie 機器人指令**

**👤 使用者：** {user_session.get_display_name()}

**開始新對話：**
- `reset` 或 `new chat`

**使用者指令：**
- `whoami` - 顯示您的使用者資訊
- `help` - 顯示詳細的機器人資訊
- `logout` - 清除您的工作階段（您將在下一條訊息中重新識別）"""

            if is_emulator:
                info_text += """

**🔧 模擬器測試指令：**
- `/setuser your.email@company.com 您的名稱` - 設定您的身分以進行測試
- 範例：`/setuser john.doe@company.com John Doe`"""

            info_text += f"""

**一般用法：**
- 詢問我任何有關您資料的問題
- 我會記住我們的對話上下文
- 需要時使用上述指令重新開始

**目前狀態：** {"新對話" if user_session.conversation_id is None else "繼續現有對話"}

**需要協助？**
請聯絡機器人管理員：{CONFIG.ADMIN_CONTACT_EMAIL}"""
            
            await turn_context.send_activity(info_text)
            return True

        # Whoami 指令
        if question.lower() in ["whoami", "/whoami", "who am i", "me"]:
            user_info = f"""👤 **您的資訊**

**名稱：** {user_session.name}
**電子郵件：** {user_session.email}
**使用者 ID：** {user_session.user_id}
**工作階段建立時間：** {user_session.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}
**最後活動時間：** {user_session.last_activity.strftime('%Y-%m-%d %H:%M:%S UTC')}
**對話 ID：** {user_session.conversation_id or '無 (新對話)'}"""
            await turn_context.send_activity(user_info)
            return True

        # Logout 指令
        if question.lower() in ["logout", "/logout", "sign out", "disconnect"]:
            # 清除使用者工作階段
            user_id = user_session.user_id
            email = user_session.email
            
            if user_id in self.user_sessions:
                del self.user_sessions[user_id]
            if email in self.email_sessions:
                del self.email_sessions[email]
            
            await turn_context.send_activity(
                f"👋 **再見 {user_session.name}！**\n\n"
                "您的工作階段已清除。當您發送下一條訊息時，將重新識別您的身分。"
            )
            return True

        # Help 指令
        if question.lower() in ["help", "/help", "commands", "/commands", "information", "about", "what is this"]:
            help_message = f"""🤖 **Databricks Genie 機器人資訊**

**我能做什麼：**
我是一個 Teams 機器人，連接到 Databricks Genie Space，讓您可以直接在 Teams 中透過自然語言查詢與您的資料互動。

**我如何運作：**
• 我使用設定的憑證連接到您的 Databricks 工作區
• 您的對話上下文會在工作階段之間保留，以保持連續性
• 我會記住我們的對話歷史，以提供更好的後續回應

**工作階段管理：**
• 對話在閒置 **4 小時** 後會自動重置
• 您可以隨時輸入 `reset` 或 `new chat` 手動重置
• 您的電子郵件 **僅用於在 Genie 中記錄查詢** - 不用於 AI 處理

**可用指令：**
• `help` - 顯示此資訊
• `info` - 獲取入門協助
• `whoami` - 顯示您的使用者資訊
• `reset` - 開始新的對話
• `new chat` - 開始新的對話
• `logout` - 清除您的工作階段

**需要協助？**
請聯絡機器人管理員：{CONFIG.ADMIN_CONTACT_EMAIL}"""
            
            await turn_context.send_activity(help_message)
            return True

        # 新對話觸發器
        new_conversation_triggers = [
            "new conversation", "new chat", "start over", "reset", "clear conversation",
            "/new", "/reset", "/clear", "/start", "begin again", "fresh start"
        ]
        
        if question.lower() in [trigger.lower() for trigger in new_conversation_triggers]:
            user_session.conversation_id = None
            user_session.user_context.pop('last_conversation_id', None)
            await turn_context.send_activity(
                f"🔄 **正在開始新對話，{user_session.name}！**\n\n"
                "您現在可以詢問我任何有關您資料的問題。"
            )
            return True

        return False

    async def on_invoke_activity(self, turn_context: TurnContext) -> InvokeResponse:
        # 處理調用活動（如 Adaptive Card 按鈕點擊）
        try:
            logger.info(f"收到調用活動: {turn_context.activity.name}")
            logger.info(f"調用活動值: {turn_context.activity.value}")
            
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
                    await self._send_feedback_to_api(feedback_key, self.message_feedback[feedback_key])
                    
                    # 返回帶有感謝訊息的更新卡片
                    updated_card = self.create_thank_you_card()
                    
                    return InvokeResponse(
                        status_code=200,
                        body={
                            "type": "AdaptiveCard",
                            "version": "1.3",
                            "body": updated_card["body"]
                        }
                    )
                except Exception as e:
                    logger.error(f"發送回饋到 Genie API 失敗: {str(e)}")
                    
                    # 返回錯誤卡片
                    error_card = self.create_error_card("提交回饋失敗。請再試一次。")
                    
                    return InvokeResponse(
                        status_code=200,
                        body={
                            "type": "AdaptiveCard",
                            "version": "1.3",
                            "body": error_card["body"]
                        }
                    )
            
            return InvokeResponse(status_code=400, body="Unknown action")
            
        except Exception as e:
            logger.error(f"處理 Adaptive Card 調用時發生錯誤: {str(e)}")
            return InvokeResponse(status_code=500, body="Error processing feedback")

    async def _send_feedback_to_api(self, feedback_key: str, feedback_data: Dict):
        # 發送回饋到 Databricks Genie 發送訊息回饋 API
        try:
            logger.info(f"收到回饋: {feedback_data}")
            
            # 檢查 Genie 回饋 API 是否啟用
            if not CONFIG.ENABLE_GENIE_FEEDBACK_API:
                logger.info("Genie 回饋 API 已停用，跳過 API 呼叫")
                return
            
            # 提取訊息 ID 和使用者工作階段資訊
            message_id = feedback_data.get("message_id")
            user_id = feedback_data.get("user_id")
            feedback_type = feedback_data.get("feedback")
            user_session_data = feedback_data.get("user_session")
            
            if not all([message_id, user_id, feedback_type]):
                logger.error(f"缺少必要的回饋資料: {feedback_data}")
                return
            
            # 獲取使用者工作階段以存取 conversation_id
            user_session = self.user_sessions.get(user_id)
            if not user_session or not user_session.conversation_id:
                logger.error(f"找不到使用者 {user_id} 的活動對話")
                return
            
            # 將回饋類型轉換為 Genie API 格式
            # positive -> POSITIVE, negative -> NEGATIVE
            genie_feedback_type = "POSITIVE" if feedback_type == "positive" else "NEGATIVE"
            
            # 呼叫 Databricks Genie 發送訊息回饋 API
            logger.info(f"正在為對話 {user_session.conversation_id} 中的特定訊息 ID {message_id} 發送回饋")
            await self._send_genie_feedback(
                space_id=CONFIG.DATABRICKS_SPACE_ID,
                conversation_id=user_session.conversation_id,
                message_id=message_id,
                feedback_type=genie_feedback_type
            )
            
            logger.info(f"成功發送回饋到 Genie API，鍵值為 {feedback_key}")
            
        except Exception as e:
            logger.error(f"發送回饋到 Genie API 時發生錯誤: {str(e)}")
            raise

    async def _send_genie_feedback(self, space_id: str, conversation_id: str, message_id: str, feedback_type: str):
        # 發送回饋到 Databricks Genie API
        try:
            loop = asyncio.get_running_loop()
            
            # 使用 Genie API 發送訊息回饋
            # 注意：確切的方法名稱可能因 API 版本而異
            # 這假設方法稱為 send_message_feedback
            await loop.run_in_executor(
                None,
                genie_api.send_message_feedback,
                space_id,
                conversation_id,
                message_id,
                feedback_type
            )
            
            logger.info(f"成功為對話 {conversation_id} 中的訊息 {message_id} 發送 {feedback_type} 回饋")
            
        except AttributeError:
            # 如果 send_message_feedback 方法不存在，嘗試替代方法名稱
            logger.warning(f"找不到 send_message_feedback 方法，嘗試替代方法")
            await self._send_genie_feedback_alternative(space_id, conversation_id, message_id, feedback_type)
        except Exception as e:
            logger.error(f"呼叫 Genie API 進行回饋時發生錯誤: {str(e)}")
            raise

    async def _send_genie_feedback_alternative(self, space_id: str, conversation_id: str, message_id: str, feedback_type: str):
        # 如果直接 API 方法不可用，則使用替代方法發送回饋
        try:
            # 如果直接 API 方法不可用，我們可以使用工作區客戶端
            # 對 Genie 回饋端點進行直接 HTTP 請求
            import aiohttp
            
            # 建構 API 端點 URL
            base_url = CONFIG.DATABRICKS_HOST.rstrip('/')
            api_endpoint = f"{base_url}/api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}/feedback"
            
            # 準備請求負載
            payload = {
                "rating": feedback_type
            }
            
            # 準備標頭
            headers = {
                "Authorization": f"Bearer {CONFIG.DATABRICKS_TOKEN}",
                "Content-Type": "application/json"
            }
            
            # 進行 HTTP 請求
            logger.info(f"正在發送回饋到: {api_endpoint}")
            logger.info(f"負載: {payload}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(api_endpoint, json=payload, headers=headers) as response:
                    response_text = await response.text()
                    if response.status == 200:
                        logger.info(f"透過 HTTP API 成功發送 {feedback_type} 回饋")
                    else:
                        logger.error(f"透過 HTTP API 發送回饋失敗: {response.status} - {response_text}")
                        raise Exception(f"HTTP {response.status}: {response_text}")
                        
        except Exception as e:
            logger.error(f"替代回饋方法發生錯誤: {str(e)}")
            raise

    async def _get_last_genie_message_id(self, conversation_id: str) -> Optional[str]:
        # 從 Genie 對話中獲取最後一條訊息 ID
        try:
            if not conversation_id:
                return None
                
            loop = asyncio.get_running_loop()
            # 嘗試不同的方法名稱來列出訊息
            try:
                # 首先嘗試 list_conversation_messages
                messages = await loop.run_in_executor(
                    None,
                    genie_api.list_conversation_messages,
                    CONFIG.DATABRICKS_SPACE_ID,
                    conversation_id,
                )
            except AttributeError:
                try:
                    # 嘗試 get_conversation_messages
                    messages = await loop.run_in_executor(
                        None,
                        genie_api.get_conversation_messages,
                        CONFIG.DATABRICKS_SPACE_ID,
                        conversation_id,
                    )
                except AttributeError:
                    # 如果兩種方法都不存在，返回 None 並記錄警告
                    logger.warning("找不到適合列出 Genie 對話訊息的方法")
                    return None
            
            # 處理不同的回應類型
            if messages:
                logger.info(f"訊息回應類型: {type(messages)}")
                logger.info(f"訊息回應屬性: {dir(messages)}")
                
                # 檢查它是否是具有 messages 屬性的回應物件
                if hasattr(messages, 'messages') and messages.messages:
                    logger.info(f"在 response.messages 中找到 {len(messages.messages)} 條訊息")
                    # 按時間戳記排序訊息以獲取最新的訊息
                    try:
                        sorted_messages = sorted(messages.messages, key=lambda x: getattr(x, 'created_at', 0), reverse=True)
                        if sorted_messages:
                            latest_message = sorted_messages[0]
                            logger.info(f"最新訊息 ID: {latest_message.message_id}")
                            return latest_message.message_id
                    except Exception as e:
                        logger.warning(f"無法按時間戳記排序訊息: {e}，使用最後一條訊息")
                        return messages.messages[-1].message_id
                # 檢查它是否是類似列表的物件
                elif hasattr(messages, '__len__') and len(messages) > 0:
                    logger.info(f"在回應中找到 {len(messages)} 條訊息 (類似列表)")
                    # 按時間戳記排序訊息以獲取最新的訊息
                    try:
                        sorted_messages = sorted(messages, key=lambda x: getattr(x, 'created_at', 0), reverse=True)
                        if sorted_messages:
                            latest_message = sorted_messages[0]
                            logger.info(f"最新訊息 ID: {latest_message.message_id}")
                            return latest_message.message_id
                    except Exception as e:
                        logger.warning(f"無法按時間戳記排序訊息: {e}，使用最後一條訊息")
                        return messages[-1].message_id
                # 檢查它是否可迭代
                elif hasattr(messages, '__iter__'):
                    message_list = list(messages)
                    if message_list:
                        logger.info(f"在回應中找到 {len(message_list)} 條訊息 (可迭代)")
                        # 按時間戳記排序訊息以獲取最新的訊息
                        try:
                            sorted_messages = sorted(message_list, key=lambda x: getattr(x, 'created_at', 0), reverse=True)
                            if sorted_messages:
                                latest_message = sorted_messages[0]
                                logger.info(f"最新訊息 ID: {latest_message.message_id}")
                                return latest_message.message_id
                        except Exception as e:
                            logger.warning(f"無法按時間戳記排序訊息: {e}，使用最後一條訊息")
                            return message_list[-1].message_id
                else:
                    logger.warning(f"無法從類型為 {type(messages)} 的回應中提取訊息")
            return None
            
        except Exception as e:
            logger.error(f"獲取最後一條 Genie 訊息 ID 時發生錯誤: {str(e)}")
            return None

    async def _send_feedback_card(self, turn_context: TurnContext, user_session: UserSession):
        # 在機器人回應後發送回饋卡
        try:
            # 檢查回饋卡是否啟用
            if not CONFIG.ENABLE_FEEDBACK_CARDS:
                return
                
            # 如果可用，使用實際的 Genie 訊息 ID，否則生成後備 ID
            genie_message_id = user_session.user_context.get('last_genie_message_id')
            if genie_message_id:
                message_id = genie_message_id
                logger.info(f"正在為特定 Genie 訊息 ID 建立回饋卡: {message_id}")
            else:
                # 如果我們沒有 Genie 訊息 ID，則回退到生成的 ID
                message_id = f"msg_{int(datetime.now().timestamp() * 1000)}"
                logger.warning(f"使用者 {user_session.get_display_name()} 沒有可用的 Genie 訊息 ID，使用後備 ID: {message_id}")
            
            # 建立回饋卡
            feedback_card = self.create_feedback_card(message_id, user_session.user_id)
            
            # 將卡片作為附件發送
            activity = Activity(
                type=ActivityTypes.message,
                attachments=[{
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": feedback_card
                }]
            )
            
            await turn_context.send_activity(activity)
            
        except Exception as e:
            logger.error(f"發送回饋卡時發生錯誤: {str(e)}")

    async def on_members_added_activity(
        self, members_added: List[ChannelAccount], turn_context: TurnContext
    ):
        for member_added in members_added:
            if member_added.id != turn_context.activity.recipient.id:
                # 根據空間 ID 獲取範例問題
                sample_questions = self._get_sample_questions()
                questions_text = "\n".join([f"- \"{q}\"" for q in sample_questions])
                
                await turn_context.send_activity(
                    f"🤖 **您好！我是 Databricks Genie 機器人。**\n\n"
                    f"我可以協助您回答有關 Databricks 中資料的問題。\n\n"
                    f"**開始使用：**\n"
                    f"我需要驗證您的電子郵件地址以記錄您的查詢。\n"
                    f"只需發送訊息給我，我將引導您完成此過程！\n\n"
                    f"**登入後，您可以詢問類似這樣的問題：**\n"
                    f"{questions_text}"
                )

# 建立機器人
bot = MyBot()

async def messages(req: Request) -> Response:
    # 主要機器人訊息處理常式
    if "application/json" in req.headers["Content-Type"]:
        body = await req.json()
    else:
        return Response(status=415)

    activity = Activity().deserialize(body)
    auth_header = req.headers.get("Authorization", "")

    try:
        response = await ADAPTER.process_activity(activity, auth_header, bot.on_turn)
        if response:
            return json_response(data=response.body, status=response.status)
        return Response(status=201)
    except Exception as exception:
        logger.error(f"處理活動時發生錯誤: {str(exception)}")
        raise exception

# 初始化應用程式
app = web.Application()
app.router.add_post("/api/messages", messages)

if __name__ == "__main__":
    try:
        # 執行應用程式
        web.run_app(app, host="0.0.0.0", port=CONFIG.PORT)
    except Exception as error:
        raise error
