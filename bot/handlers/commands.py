"""Command handling utilities for MyBot."""

from __future__ import annotations

from typing import Dict

from botbuilder.core import TurnContext
from botbuilder.schema import Activity, ActivityTypes

from botbuilder.schema import Activity, ActivityTypes

from app.models.user_session import UserSession


async def handle_special_commands(
    turn_context: TurnContext,
    question: str,
    user_session: UserSession,
    config,
    format_timestamp,
    user_sessions: Dict[str, UserSession],
    email_sessions: Dict[str, UserSession],
    graph_service=None,
) -> bool:
    lowered = question.lower()

    if lowered.startswith("/setuser ") and turn_context.activity.channel_id == "emulator":
        parts = question.split(" ", 2)
        if len(parts) >= 2:
            email = parts[1]
            name = parts[2] if len(parts) > 2 else email.split('@')[0]
            session = UserSession(turn_context.activity.from_property.id, email, name)
            user_sessions[session.user_id] = session
            email_sessions[email] = session
            await turn_context.send_activity(
                "✅ **Identity Updated!**\n\n"
                f"**Name:** {session.name}\n"
                f"**Email:** {session.email}\n\n"
                "You can now ask me questions about your data!"
            )
            return True
        await turn_context.send_activity(
            "❌ **Invalid format**\n\n"
            "Use: `/setuser your.email@company.com Your Name`\n"
            "Example: `/setuser john.doe@company.com John Doe`"
        )
        return True

    if lowered in ["info", "/info"]:
        is_emulator = turn_context.activity.channel_id == "emulator"
        info_text = (
            "🤖 **Databricks Genie 機器人指令**\n\n"
            f"**👤 使用者：** {user_session.get_display_name()}\n\n"
            "**開始新對話：**\n"
            "- `reset` 或 `new chat`\n\n"
            "**使用者指令：**\n"
            "- `whoami` 或 `/me` - 顯示您的使用者資訊（包括 Graph API 資料卡片）\n"
            "- `help` - 顯示詳細的機器人資訊\n"
            "- `logout` - 清除您的工作階段（您將在下一條訊息中重新識別）"
        )
        if is_emulator:
            info_text += (
                "\n\n**🔧 模擬器測試指令：**\n"
                "- `/setuser your.email@company.com 您的名稱` - 設定您的身分以進行測試\n"
                "- 範例：`/setuser john.doe@company.com John Doe`"
            )
        info_text += (
            "\n\n**一般用法：**\n"
            "- 詢問我任何有關您資料的問題\n"
            "- 我會記住我們的對話上下文\n"
            "- 需要時使用上述指令重新開始\n\n"
            f"**目前狀態：** {'新對話' if user_session.conversation_id is None else '繼續現有對話'}\n\n"
            "**需要協助？**\n"
            f"請聯絡機器人管理員：{config.ADMIN_CONTACT_EMAIL}"
        )
        await turn_context.send_activity(info_text)
        return True

    if lowered in ["whoami", "/whoami", "who am i", "me", "/me"]:
        created_local = format_timestamp(user_session.created_at)
        last_local = format_timestamp(user_session.last_activity)
        user_info = (
            "👤 **您的資訊**\n\n"
            f"**名稱：** {user_session.name}\n\n"
            f"**電子郵件：** {user_session.email}\n\n"
            f"**使用者 ID：** {user_session.user_id}\n\n"
            f"**工作階段建立時間：** {created_local}\n\n"
            f"**最後活動時間：** {last_local}\n\n"
            f"**對話 ID：** {user_session.conversation_id or '無 (新對話)'}"
        )
        activity = Activity(type=ActivityTypes.message, text=user_info, text_format="markdown")
        await turn_context.send_activity(activity)
        
        # 🎫 如果 Graph Service 可用，嘗試發送用戶資料卡片
        if graph_service and config.ENABLE_GRAPH_API_AUTO_LOGIN:
            try:
                from botbuilder.schema import Attachment
                
                # 取得完整的使用者資料
                user_detail = await graph_service.get_user_email_and_id(turn_context)
                token_response = await graph_service.get_user_token(turn_context)
                
                if token_response and user_detail:
                    full_profile = await graph_service.get_user_profile(token_response.token)
                    user_detail.update(full_profile)
                    
                    # 創建用戶資料卡片
                    from app.services.graph import GraphService
                    user_card = GraphService.create_user_profile_card(user_detail)
                    
                    card_attachment = Attachment(
                        content_type="application/vnd.microsoft.card.adaptive",
                        content=user_card
                    )
                    
                    card_activity = Activity(
                        type=ActivityTypes.message,
                        attachments=[card_attachment]
                    )
                    
                    await turn_context.send_activity(card_activity)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"⚠️ 無法發送使用者資料卡片: {str(e)}")
        
        return True

    if lowered in ["logout", "/logout", "sign out", "disconnect"]:
        user_id = user_session.user_id
        email = user_session.email
        user_sessions.pop(user_id, None)
        email_sessions.pop(email, None)
        await turn_context.send_activity(
            f"👋 **再見 {user_session.name}！**\n\n"
            "您的工作階段已清除。當您發送下一條訊息時，將重新識別您的身分。"
        )
        return True

    if lowered in ["help", "/help", "commands", "/commands", "information", "about", "what is this"]:
        await turn_context.send_activity(
            "🤖 **Databricks Genie 機器人資訊**\n\n"
            "**我能做什麼：**\n"
            "我是一個 Teams 聊天機器人，會自動連接到 Databricks Genie Space，讓您可以直接在 Teams 中透過自然語言來查詢，與您的資料互動。\n\n"
            "**我如何運作：**\n\n"
            "    • 我使用預先設定的憑證連接到您的 Databricks 工作區\n\n"
            "    • 您的對話上下文會在工作階段之間保留，以保持連續性\n\n"
            "    • 我會記住我們的對話歷史，以提供更好的後續回應\n\n"
            "**工作階段管理：**\n\n"
            "    • 對話在閒置 **4 小時** 後會自動重置\n\n"
            "    • 您可以隨時輸入 `reset` 或 `new chat` 手動重置\n"
            "    • 您的電子郵件 **僅用於在 Genie 中記錄查詢** - 不用於 AI 處理\n\n"
            "**可用指令：**\n\n"
            "    • `help` - 顯示此資訊\n\n"
            "    • `info` - 獲取入門協助\n\n"
            "    • `whoami` 或 `/me` - 顯示您的使用者資訊和 Graph API 資料\n\n"
            "    • `reset` - 開始新的對話\n\n"
            "    • `new chat` - 開始新的對話\n\n"
            "    • `logout` - 清除您的工作階段\n\n"
            "**需要協助？**\n"
            f"請聯絡機器人管理員：{config.ADMIN_CONTACT_EMAIL}"
        )
        return True

    new_conversation_triggers = [
        "new conversation",
        "new chat",
        "start over",
        "reset",
        "clear conversation",
        "/new",
        "/reset",
        "/clear",
        "/start",
        "begin again",
        "fresh start",
    ]
    if lowered in [trigger.lower() for trigger in new_conversation_triggers]:
        user_session.conversation_id = None
        user_session.user_context.pop('last_conversation_id', None)
        await turn_context.send_activity(
            f"🔄 **正在開始新對話，{user_session.name}！**\n\n"
            "您現在可以詢問我任何有關您關心的資料問題。"
        )
        return True

    return False
