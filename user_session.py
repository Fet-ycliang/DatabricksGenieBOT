"""Helpers for managing user session state."""

from __future__ import annotations

import re
from datetime import datetime, timezone, timedelta
from typing import List, Optional


class UserSession:
    """Represents a Teams user session."""

    def __init__(self, user_id: str, email: str, name: Optional[str] = None):
        self.user_id = user_id
        self.email = email
        self.name = name or email.split('@')[0]
        self.conversation_id: Optional[str] = None
        self.created_at = datetime.now(timezone.utc)
        self.last_activity = datetime.now(timezone.utc)
        self.is_authenticated = True
        self.user_context: dict = {}
        # 新增 AAD (Azure Active Directory) 相關資訊
        self.aad_object_id: Optional[str] = None  # OpenID / AAD Object ID
        self.upn: Optional[str] = None  # User Principal Name

    def update_activity(self) -> None:
        self.last_activity = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "email": self.email,
            "name": self.name,
            "conversation_id": self.conversation_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "is_authenticated": self.is_authenticated,
            "aad_object_id": self.aad_object_id,
            "upn": self.upn,
        }

    def get_display_name(self) -> str:
        return f"{self.name} ({self.email})"


def is_valid_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_conversation_timed_out(user_session: UserSession, timeout_hours: int = 4) -> bool:
    if not user_session:
        return False

    time_since_last = datetime.now(timezone.utc) - user_session.last_activity
    return time_since_last > timedelta(hours=timeout_hours)


def get_sample_questions(sample_questions: Optional[str]) -> List[str]:
    if sample_questions:
        questions = [q.strip() for q in sample_questions.split(';') if q.strip()]
        if questions:
            return questions
    return [
        "What data is available?",
        "Can you explain the datasets?",
        "What questions should I ask?",
    ]
