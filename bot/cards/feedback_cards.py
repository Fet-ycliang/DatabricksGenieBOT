"""Adaptive Card builders for feedback collection."""

from __future__ import annotations

from datetime import datetime
from typing import Dict

from botbuilder.core import TurnContext
from botbuilder.schema import Activity, ActivityTypes

from app.models.user_session import UserSession


def create_feedback_card(message_id: str, user_id: str) -> Dict:
    return {
        "type": "AdaptiveCard",
        "version": "1.3",
        "body": [
            {
                "type": "TextBlock",
                "text": "這個回應有幫助嗎？",
                "size": "Small",
                "color": "Default",
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
                    "feedback": "positive",
                },
            },
            {
                "type": "Action.Submit",
                "title": "👎",
                "data": {
                    "action": "feedback",
                    "messageId": message_id,
                    "userId": user_id,
                    "feedback": "negative",
                },
            },
        ],
    }


def create_thank_you_card() -> Dict:
    return {
        "type": "AdaptiveCard",
        "version": "1.3",
        "body": [
            {
                "type": "TextBlock",
                "text": "✅ 感謝您的回饋！",
                "size": "Small",
                "color": "Good",
            }
        ],
    }


def create_error_card(error_message: str) -> Dict:
    return {
        "type": "AdaptiveCard",
        "version": "1.3",
        "body": [
            {
                "type": "TextBlock",
                "text": f"❌ {error_message}",
                "size": "Small",
                "color": "Attention",
            }
        ],
    }


async def send_feedback_card(
    turn_context: TurnContext,
    user_session: UserSession,
    enable_feedback_cards: bool,
) -> None:
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
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": feedback_card,
            }
        ],
    )
    await turn_context.send_activity(activity)
