"""Adaptive Card builders for feedback collection.

使用統一的 Card 構建器和常數，提供更好的視覺設計。
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict

from botbuilder.core import TurnContext
from botbuilder.schema import Activity, ActivityTypes

from app.models.user_session import UserSession
from bot.cards.card_builder import CardBuilder
from bot.cards.constants import (
    ADAPTIVE_CARD_CONTENT_TYPE,
    EMOJI_ERROR,
    EMOJI_SUCCESS,
    EMOJI_THUMBS_DOWN,
    EMOJI_THUMBS_UP,
)


def create_feedback_card(message_id: str, user_id: str) -> Dict:
    """建立回饋收集 Adaptive Card。"""
    body = [
        CardBuilder.separator(),
        CardBuilder.text_block(
            "這個回應有幫助嗎？",
            size="Small",
            is_subtle=True,
        ),
    ]

    actions = [
        CardBuilder.action_submit(
            title=EMOJI_THUMBS_UP,
            data={
                "action": "feedback",
                "messageId": message_id,
                "userId": user_id,
                "feedback": "positive",
            },
        ),
        CardBuilder.action_submit(
            title=EMOJI_THUMBS_DOWN,
            data={
                "action": "feedback",
                "messageId": message_id,
                "userId": user_id,
                "feedback": "negative",
            },
        ),
    ]

    return CardBuilder.create_card(body=body, actions=actions)


def create_thank_you_card() -> Dict:
    """建立回饋感謝 Adaptive Card。"""
    body = [
        CardBuilder.text_block(
            f"{EMOJI_SUCCESS} 感謝您的回饋！",
            size="Small",
            color="Good",
        ),
    ]
    return CardBuilder.create_card(body=body)


def create_error_card(error_message: str) -> Dict:
    """建立回饋錯誤 Adaptive Card。"""
    body = [
        CardBuilder.text_block(
            f"{EMOJI_ERROR} {error_message}",
            size="Small",
            color="Attention",
        ),
    ]
    return CardBuilder.create_card(body=body)


async def send_feedback_card(
    turn_context: TurnContext,
    user_session: UserSession,
    enable_feedback_cards: bool,
) -> None:
    """發送回饋收集卡片。"""
    if not enable_feedback_cards:
        return

    genie_message_id = user_session.user_context.get('last_genie_message_id')
    if genie_message_id:
        message_id = genie_message_id
    else:
        message_id = f"msg_{int(datetime.now().timestamp() * 1000)}"

    feedback_card = create_feedback_card(message_id, user_session.user_id)
    activity = Activity(
        type=ActivityTypes.message,
        attachments=[
            {
                "contentType": ADAPTIVE_CARD_CONTENT_TYPE,
                "content": feedback_card,
            }
        ],
    )
    await turn_context.send_activity(activity)
