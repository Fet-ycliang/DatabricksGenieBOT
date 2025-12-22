"""Helpers for handling user identification and email capture flows."""

from __future__ import annotations

from typing import Awaitable, Callable, Dict, List

from botbuilder.core import TurnContext

from user_session import UserSession


async def handle_pending_email_input(
    user_id: str,
    question: str,
    turn_context: TurnContext,
    pending_email_input: Dict[str, bool],
    create_session_func: Callable[[TurnContext, str], Awaitable[UserSession]],
    is_valid_email_func: Callable[[str], bool],
    sample_questions: List[str],
) -> bool:
    if user_id not in pending_email_input:
        return False

    lowered = question.lower()
    if lowered == "cancel":
        del pending_email_input[user_id]
        await turn_context.send_activity(
            "❌ **電子郵件輸入已取消**\n\n"
            "您可以稍後輸入任何訊息再試一次。如果需要，我會再次詢問您的電子郵件。"
        )
        return True

    if is_valid_email_func(question):
        user_session = await create_session_func(turn_context, question)
        questions_text = "\n".join([f"- {q}" for q in sample_questions])
        await turn_context.send_activity(
            f"✅ **電子郵件已確認！**\n\n"
            f"歡迎，{user_session.name}！我已成功將您登入為 {user_session.email}。\n\n"
            f"現在您可以詢問有關您資料的問題。試著問類似這樣的問題：\n"
            f"{questions_text}"
        )
        return True

    await turn_context.send_activity(
        "❌ **無效的電子郵件格式**\n\n"
        "請提供有效的電子郵件地址（例如：john.doe@company.com）。\n\n"
        "輸入 `cancel` 停止電子郵件輸入過程。"
    )
    return True


async def handle_user_identification(
    turn_context: TurnContext,
    question: str,
    config,
    pending_email_input: Dict[str, bool],
) -> None:
    user_id = turn_context.activity.from_property.id
    lowered = question.lower()

    if lowered in ["help", "/help", "commands", "/commands"]:
        await turn_context.send_activity(
            "🤖 **Databricks Genie 機器人資訊**\n\n"
            "**我能做什麼：**\n"
            "我是一個 Teams 機器人，連接到 Databricks Genie Space，讓您可以直接在 Teams 中透過自然語言查詢與您的資料互動。\n\n"
            "**我如何運作：**\n"
            "    • 我使用設定的憑證連接到您的 Databricks 工作區\n"
            "    • 您的對話上下文會在工作階段之間保留，以保持連續性\n"
            "    • 我會記住我們的對話歷史，以提供更好的後續回應\n\n"
            "**工作階段管理：**\n"
            "    • 對話在閒置 **4 小時** 後會自動重置\n"
            "    • 您可以隨時輸入 `reset` 或 `new chat` 手動重置\n"
            "    • 您的電子郵件 **僅用於在 Genie 中記錄查詢** - 不用於 AI 處理\n\n"
            "**可用指令：**\n"
            "    • `help` - 顯示此資訊\n"
            "    • `info` - 獲取入門協助\n"
            "    • `whoami` - 顯示您的使用者資訊\n"
            "    • `reset` - 開始新的對話\n"
            "    • `new chat` - 開始新的對話\n"
            "    • `logout` - 清除您的工作階段\n\n"
            "**需要協助？**\n"
            f"請聯絡機器人管理員：{config.ADMIN_CONTACT_EMAIL}"
        )
        return

    if lowered in ["info", "/info"]:
        await turn_context.send_activity(
            "🤖 **歡迎使用 Genie 機器人 - 需要使用者登入**\n\n"
            "我需要您的電子郵件地址來記錄 Genie 中的查詢以進行追蹤。\n\n"
            "**快速開始：**\n"
            "- 輸入 `email` 提供您的電子郵件地址\n"
            "- 我將驗證格式並建立您的工作階段\n\n"
            "**接下來會發生什麼：**\n"
            "- 登入後，您可以詢問有關您資料的問題\n"
            "- 我會記住我們的對話上下文\n"
            "- 您可以詢問後續問題\n\n"
            "**了解更多：**\n"
            "- 輸入 `help` 了解更多關於 Genie 機器人的資訊\n"
            "- 輸入 `info` 獲取入門協助\n\n"
            "準備好開始了嗎？輸入 `email` 提供您的電子郵件地址！"
        )
        return

    if lowered in ["email", "provide email", "enter email"]:
        pending_email_input[user_id] = True
        await turn_context.send_activity(
            "📧 **Genie 使用者登入**\n\n"
            "請提供您的電子郵件地址（例如：captain.planet@company.com）。\n\n"
            "如果您想停止此過程，請輸入 `cancel`。"
        )
        return

    await turn_context.send_activity(
        "🤖 **歡迎使用 Genie 機器人**\n\n"
        "我需要您的電子郵件地址來記錄 Genie 中的查詢以進行追蹤。\n\n"
        "**快速選項：**\n"
        "- 輸入 `email` 提供您的電子郵件地址\n"
        "- 輸入 `help` 了解更多關於 Genie 機器人的資訊\n"
        "- 輸入 `info` 獲取入門協助\n\n"
        "登入後，您就可以詢問有關您資料的問題！"
    )
