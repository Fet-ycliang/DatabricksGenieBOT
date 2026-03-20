"""
測試 UserSession 模型
"""

import pytest
from datetime import datetime, timezone, timedelta
from app.models.user_session import (
    UserSession,
    is_valid_email,
    is_conversation_timed_out,
    get_sample_questions,
)


def test_user_session_initialization():
    """測試 UserSession 初始化"""
    session = UserSession(
        user_id="test-user-123",
        email="test@example.com",
        name="Test User"
    )

    assert session.user_id == "test-user-123"
    assert session.email == "test@example.com"
    assert session.name == "Test User"
    assert session.conversation_id is None
    assert session.is_authenticated is True
    assert session.aad_object_id is None
    assert session.upn is None
    assert isinstance(session.created_at, datetime)
    assert isinstance(session.last_activity, datetime)
    assert isinstance(session.user_context, dict)


def test_user_session_default_name():
    """測試 UserSession 預設名稱（從 email 提取）"""
    session = UserSession(
        user_id="user-456",
        email="john.doe@company.com"
    )

    # 應該使用 email @ 前面的部分作為預設名稱
    assert session.name == "john.doe"


def test_user_session_update_activity():
    """測試更新活動時間"""
    session = UserSession("user-1", "user@test.com")

    original_time = session.last_activity

    # 等待一小段時間
    import time
    time.sleep(0.01)

    session.update_activity()

    # last_activity 應該已更新
    assert session.last_activity > original_time


def test_user_session_to_dict():
    """測試 to_dict 序列化"""
    session = UserSession(
        user_id="user-789",
        email="jane@example.com",
        name="Jane Doe"
    )
    session.conversation_id = "conv-123"
    session.aad_object_id = "aad-456"
    session.upn = "jane@company.com"

    result = session.to_dict()

    assert result["user_id"] == "user-789"
    assert result["email"] == "jane@example.com"
    assert result["name"] == "Jane Doe"
    assert result["conversation_id"] == "conv-123"
    assert result["is_authenticated"] is True
    assert result["aad_object_id"] == "aad-456"
    assert result["upn"] == "jane@company.com"
    assert "created_at" in result
    assert "last_activity" in result
    # ISO format 檢查
    assert "T" in result["created_at"]


def test_user_session_get_display_name():
    """測試顯示名稱"""
    session = UserSession(
        user_id="user-1",
        email="test@example.com",
        name="Test User"
    )

    display_name = session.get_display_name()
    assert display_name == "Test User (test@example.com)"


def test_is_valid_email():
    """測試 email 驗證"""
    # 有效的 email
    assert is_valid_email("user@example.com") is True
    assert is_valid_email("john.doe@company.co.uk") is True
    assert is_valid_email("test+tag@domain.org") is True
    assert is_valid_email("user_123@test-domain.com") is True

    # 無效的 email
    assert is_valid_email("invalid") is False
    assert is_valid_email("@example.com") is False
    assert is_valid_email("user@") is False
    assert is_valid_email("user @example.com") is False
    assert is_valid_email("") is False


def test_is_conversation_timed_out():
    """測試對話超時檢查"""
    # 新建的 session 不應該超時
    session = UserSession("user-1", "user@test.com")
    assert is_conversation_timed_out(session, timeout_hours=4) is False

    # 模擬舊的 session（超過 4 小時）
    old_session = UserSession("user-2", "user2@test.com")
    old_session.last_activity = datetime.now(timezone.utc) - timedelta(hours=5)
    assert is_conversation_timed_out(old_session, timeout_hours=4) is True

    # 邊界情況：正好 4 小時
    boundary_session = UserSession("user-3", "user3@test.com")
    boundary_session.last_activity = datetime.now(timezone.utc) - timedelta(hours=4, seconds=1)
    assert is_conversation_timed_out(boundary_session, timeout_hours=4) is True

    # None session 應該返回 False
    assert is_conversation_timed_out(None, timeout_hours=4) is False


def test_is_conversation_timed_out_custom_timeout():
    """測試自訂超時時間"""
    session = UserSession("user-1", "user@test.com")
    session.last_activity = datetime.now(timezone.utc) - timedelta(hours=2)

    # 1 小時超時：應該超時
    assert is_conversation_timed_out(session, timeout_hours=1) is True

    # 3 小時超時：不應該超時
    assert is_conversation_timed_out(session, timeout_hours=3) is False


def test_get_sample_questions_default():
    """測試預設範例問題"""
    questions = get_sample_questions(None)

    assert len(questions) == 3
    assert "What data is available?" in questions
    assert "Can you explain the datasets?" in questions
    assert "What questions should I ask?" in questions


def test_get_sample_questions_custom():
    """測試自訂範例問題"""
    custom = "Question 1; Question 2; Question 3"
    questions = get_sample_questions(custom)

    assert len(questions) == 3
    assert "Question 1" in questions
    assert "Question 2" in questions
    assert "Question 3" in questions


def test_get_sample_questions_with_whitespace():
    """測試帶空白的範例問題"""
    custom = "  Question A  ;  Question B  ;  Question C  "
    questions = get_sample_questions(custom)

    assert len(questions) == 3
    assert "Question A" in questions  # 應該去除空白
    assert "Question B" in questions
    assert "Question C" in questions


def test_get_sample_questions_empty_string():
    """測試空字串範例問題"""
    questions = get_sample_questions("")

    # 應該返回預設問題
    assert len(questions) == 3
    assert "What data is available?" in questions


def test_get_sample_questions_with_empty_entries():
    """測試包含空項目的範例問題"""
    custom = "Question 1;;Question 2;  ;Question 3"
    questions = get_sample_questions(custom)

    # 空項目應該被過濾掉
    assert len(questions) == 3
    assert "" not in questions
    assert "Question 1" in questions
    assert "Question 2" in questions
    assert "Question 3" in questions


def test_user_session_aad_fields():
    """測試 Azure AD 欄位"""
    session = UserSession("user-1", "user@test.com")

    # 初始應該是 None
    assert session.aad_object_id is None
    assert session.upn is None

    # 設定值
    session.aad_object_id = "00000000-0000-0000-0000-000000000000"
    session.upn = "user@company.onmicrosoft.com"

    assert session.aad_object_id == "00000000-0000-0000-0000-000000000000"
    assert session.upn == "user@company.onmicrosoft.com"


def test_user_session_user_context():
    """測試 user_context 字典"""
    session = UserSession("user-1", "user@test.com")

    # 初始應該是空字典
    assert session.user_context == {}

    # 可以存儲自訂資料
    session.user_context["preference"] = "dark_mode"
    session.user_context["language"] = "zh-TW"

    assert session.user_context["preference"] == "dark_mode"
    assert session.user_context["language"] == "zh-TW"
