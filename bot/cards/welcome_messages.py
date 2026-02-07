"""Welcome message builders for new members."""

from __future__ import annotations

from app.models.user_session import UserSession


def build_authenticated_welcome(user_session: UserSession, is_emulator: bool, config) -> str:
    message = (
        f"🤖 **{user_session.name}: 歡迎您使用 Databricks Genie 機器人!**\n\n"
        "我可以透過自然語言協助你分析資料，並會記住我們的對話上下文，方便你提出後續問題。\n\n"
        f"**👤 目前身分：** {user_session.get_display_name()}"
    )
    if is_emulator:
        message += (
            "\n\n**🔧 模擬器測試：**\n"
            "你目前使用 Bot Emulator 進行測試，可隨時透過下列指令變更身分：\n"
            "`/setuser your.email@company.com Your Name`"
        )
    message += (
        "\n\n**快速指令：**\n"
        "- `help` - 查看詳細的使用說明資訊\n"
        "- `info` - 取得上手協助\n"
        "- `whoami` - 查看你的使用者資訊  \n"
        "- `reset` 或 `new chat` - 重新開始新的聊天內容\n"
        "- 隨時問我任何跟資料相關的問題！\n\n"
        "準備好了嗎？直接問我一個問題吧！"
    )
    return message


def build_unauthenticated_welcome(is_emulator: bool, config) -> str:
    message = (
        "🤖 **您好！我是 Databricks Genie 機器人。**\n\n"
        "我可以透過自然語言協助你分析資料，並會記住我們的對話上下文，方便你提出後續問題。\n\n"
        "**📧 第一次使用：**\n"
        "請提供你的電子郵件，以便在 Genie 中記錄查詢以供追蹤。"
    )
    if is_emulator:
        message += (
            "\n\n**🔧 模擬器測試：**\n"
            "由於你正在使用 Bot Emulator，請透過下列指令設定身分：\n"
            "`/setuser your.email@company.com Your Name`\n"
            "範例：`/setuser john.doe@company.com John Doe`"
        )
    else:
        message += (
            "\n\n**如何開始：**\n"
            "- 輸入 `email` 提供你的電子郵件\n"
            "- 輸入 `info` 取得上手協助"
        )
    message += (
        "\n\n**快速指令：**\n"
        "- `help` - 查看詳細的使用說明資訊\n"
        "- `info` - 取得上手協助\n"
        "- `whoami` - 查看你的使用者資訊  \n"
        "- `reset` 或 `new chat` - 重新開始新的聊天內容\n"
        "- 隨時問我任何跟資料相關的問題！\n\n"
        "準備好了嗎？輸入 `email` 就可以開始！"
    )
    return message