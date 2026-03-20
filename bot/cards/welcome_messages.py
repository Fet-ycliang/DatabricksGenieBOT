"""Welcome message builders for new members.

使用 Adaptive Card 格式取代純 Markdown 字串，提供豐富的 UI 功能
（按鈕互動、佈局控制、品牌一致性）。
"""

from __future__ import annotations

from typing import Any, Dict, List

from botbuilder.core import MessageFactory
from botbuilder.schema import Activity, ActivityTypes

from app.models.user_session import UserSession
from bot.cards.card_builder import CardBuilder
from bot.cards.constants import EMOJI_BOT, EMOJI_GEAR, EMOJI_ROCKET, EMOJI_USER


def _quick_command_actions() -> List[Dict[str, Any]]:
    """建立常用指令的快速按鈕。"""
    return [
        CardBuilder.action_submit(
            title="help - 使用說明",
            data={"action": "ask_suggested_question", "question": "help"},
        ),
        CardBuilder.action_submit(
            title="info - 上手協助",
            data={"action": "ask_suggested_question", "question": "info"},
        ),
        CardBuilder.action_submit(
            title="whoami - 使用者資訊",
            data={"action": "ask_suggested_question", "question": "whoami"},
        ),
    ]


def build_authenticated_welcome_card(
    user_session: UserSession,
    is_emulator: bool,
    config: Any,
) -> Dict[str, Any]:
    """建立已認證使用者的歡迎 Adaptive Card。"""
    body: List[Dict[str, Any]] = [
        CardBuilder.create_header(
            icon=EMOJI_BOT,
            title=f"歡迎，{user_session.name}！",
            subtitle="Databricks Genie 機器人",
        ),
        CardBuilder.text_block(
            "我可以透過自然語言協助你分析資料，並會記住我們的對話上下文，方便你提出後續問題。",
            spacing="Medium",
        ),
        CardBuilder.text_block(
            f"{EMOJI_USER} **目前身分：** {user_session.get_display_name()}",
            spacing="Small",
        ),
    ]

    if is_emulator:
        body.append(
            CardBuilder.text_block(
                f"{EMOJI_GEAR} **模擬器測試：** 可透過 `/setuser your.email@company.com Your Name` 變更身分",
                size="Small",
                is_subtle=True,
                spacing="Medium",
            )
        )

    body.append(
        CardBuilder.text_block(
            f"{EMOJI_ROCKET} 準備好了嗎？直接問我一個問題吧！",
            spacing="Medium",
            weight="Bolder",
        )
    )

    card = CardBuilder.create_card(body=body, actions=_quick_command_actions())
    return CardBuilder.wrap_as_attachment(card)


def build_unauthenticated_welcome_card(
    is_emulator: bool,
    config: Any,
) -> Dict[str, Any]:
    """建立未認證使用者的歡迎 Adaptive Card。"""
    body: List[Dict[str, Any]] = [
        CardBuilder.create_header(
            icon=EMOJI_BOT,
            title="您好！我是 Databricks Genie 機器人",
            subtitle="透過自然語言分析您的資料",
        ),
        CardBuilder.text_block(
            "我可以透過自然語言協助你分析資料，並會記住我們的對話上下文，方便你提出後續問題。",
            spacing="Medium",
        ),
    ]

    if is_emulator:
        body.append(
            CardBuilder.text_block(
                f"{EMOJI_GEAR} **模擬器測試：** 請透過下列指令設定身分：\n"
                "`/setuser your.email@company.com Your Name`\n"
                "範例：`/setuser john.doe@company.com John Doe`",
                size="Small",
                is_subtle=True,
                spacing="Medium",
            )
        )
    else:
        body.append(
            CardBuilder.text_block(
                "請提供你的電子郵件，以便在 Genie 中記錄查詢以供追蹤。",
                spacing="Medium",
            )
        )

    card = CardBuilder.create_card(body=body, actions=_quick_command_actions())
    return CardBuilder.wrap_as_attachment(card)


# 向後相容：保留原有函式簽名，使呼叫端可以無縫遷移
def build_authenticated_welcome(
    user_session: UserSession,
    is_emulator: bool,
    config: Any,
) -> Activity:
    """建立已認證使用者的歡迎訊息（以 Activity 形式回傳）。"""
    attachment = build_authenticated_welcome_card(user_session, is_emulator, config)
    return MessageFactory.attachment(attachment)


def build_unauthenticated_welcome(is_emulator: bool, config: Any) -> Activity:
    """建立未認證使用者的歡迎訊息（以 Activity 形式回傳）。"""
    attachment = build_unauthenticated_welcome_card(is_emulator, config)
    return MessageFactory.attachment(attachment)
