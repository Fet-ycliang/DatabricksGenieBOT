"""共用訊息模板。

集中管理 help、info 等常用訊息的內容，
避免在 identity.py 和 commands.py 中重複維護。
"""

from __future__ import annotations


def build_help_message(admin_email: str) -> str:
    """建立 help 訊息。"""
    return (
        "\U0001F916 **Databricks Genie 機器人資訊**\n\n"
        "**我能做什麼：**\n"
        "我是一個 Teams 聊天機器人，會自動連接到 Databricks Genie Space，"
        "讓您可以直接在 Teams 中透過自然語言來查詢，與您的資料互動。\n\n"
        "**我如何運作：**\n\n"
        "    \u2022 我使用預先設定的憑證連接到您的 Databricks 工作區\n\n"
        "    \u2022 您的對話上下文會在工作階段之間保留，以保持連續性\n\n"
        "    \u2022 我會記住我們的對話歷史，以提供更好的後續回應\n\n"
        "**工作階段管理：**\n\n"
        "    \u2022 對話在閒置 **4 小時** 後會自動重置\n\n"
        "    \u2022 您可以隨時輸入 `reset` 或 `new chat` 手動重置\n"
        "    \u2022 您的電子郵件 **僅用於在 Genie 中記錄查詢** - 不用於 AI 處理\n\n"
        "**可用指令：**\n\n"
        "    \u2022 `help` - 顯示此資訊\n\n"
        "    \u2022 `info` - 獲取入門協助\n\n"
        "    \u2022 `whoami` 或 `/me` - 顯示您的使用者資訊和 Graph API 資料\n\n"
        "    \u2022 `reset` - 開始新的對話\n\n"
        "    \u2022 `new chat` - 開始新的對話\n\n"
        "    \u2022 `logout` - 清除您的工作階段\n\n"
        "**需要協助？**\n"
        f"請聯絡機器人管理員：{admin_email}"
    )
