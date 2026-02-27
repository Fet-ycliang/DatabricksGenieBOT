"""結構化錯誤 Adaptive Card。

提供友善的錯誤訊息、重試按鈕和管理員聯絡資訊，
取代直接將 str(e) 顯示給使用者的做法。
"""

from __future__ import annotations

from typing import Dict, Optional

from bot.cards.card_builder import CardBuilder
from bot.cards.constants import EMOJI_ERROR, EMOJI_RETRY, EMOJI_WARNING


def create_user_error_card(
    message: str = "處理您的查詢時發生了問題。",
    admin_email: Optional[str] = None,
    show_retry: bool = True,
) -> Dict:
    """建立面向使用者的錯誤 Adaptive Card。

    不會包含任何內部錯誤細節，僅顯示友善的說明。
    """
    body = [
        CardBuilder.create_header(
            icon=EMOJI_ERROR,
            title="發生錯誤",
            subtitle=message,
            title_color="Attention",
        ),
    ]

    help_text = "請稍後再試一次。"
    if admin_email:
        help_text += f" 如問題持續，請聯絡管理員：{admin_email}"

    body.append(
        CardBuilder.text_block(
            help_text,
            size="Small",
            is_subtle=True,
            spacing="Medium",
        )
    )

    actions = []
    if show_retry:
        actions.append(
            CardBuilder.action_submit(
                title=f"{EMOJI_RETRY} 重試",
                data={"action": "retry"},
            )
        )

    return CardBuilder.create_card(body=body, actions=actions if actions else None)


def create_warning_card(message: str) -> Dict:
    """建立警告 Adaptive Card（非致命錯誤）。"""
    body = [
        CardBuilder.create_header(
            icon=EMOJI_WARNING,
            title="提示",
            subtitle=message,
            title_color="Warning",
        ),
    ]
    return CardBuilder.create_card(body=body)
