"""
測試 EmailExtractor 工具
"""

import pytest
import jwt
import asyncio
from unittest.mock import Mock
from botbuilder.core import TurnContext
from botbuilder.schema import Activity, ChannelAccount, TokenResponse
from app.utils.email_extractor import EmailExtractor


def test_from_token_valid_email_claim():
    """測試從 JWT Token 提取 email（email claim）"""
    payload = {
        "email": "user@example.com",
        "name": "Test User",
        "aud": "test-audience"
    }
    token = jwt.encode(payload, "secret", algorithm="HS256")

    email = EmailExtractor.from_token(token)
    assert email == "user@example.com"


def test_from_token_preferred_username():
    """測試從 JWT Token 提取 email（preferred_username claim）"""
    payload = {
        "preferred_username": "user@company.com",
        "name": "Test User"
    }
    token = jwt.encode(payload, "secret", algorithm="HS256")

    email = EmailExtractor.from_token(token)
    assert email == "user@company.com"


def test_from_token_upn():
    """測試從 JWT Token 提取 email（upn claim）"""
    payload = {
        "upn": "user.principal@domain.com",
        "name": "Test User"
    }
    token = jwt.encode(payload, "secret", algorithm="HS256")

    email = EmailExtractor.from_token(token)
    assert email == "user.principal@domain.com"


def test_from_token_unique_name():
    """測試從 JWT Token 提取 email（unique_name claim）"""
    payload = {
        "unique_name": "legacy.user@example.com"
    }
    token = jwt.encode(payload, "secret", algorithm="HS256")

    email = EmailExtractor.from_token(token)
    assert email == "legacy.user@example.com"


def test_from_token_priority_order():
    """測試多個 claim 存在時的優先級"""
    payload = {
        "email": "email@example.com",
        "preferred_username": "preferred@example.com",
        "upn": "upn@example.com",
        "unique_name": "unique@example.com"
    }
    token = jwt.encode(payload, "secret", algorithm="HS256")

    email = EmailExtractor.from_token(token)
    # 應該優先使用 email
    assert email == "email@example.com"


def test_from_token_no_at_symbol():
    """測試不包含 @ 的值應該被拒絕"""
    payload = {
        "email": "not-an-email",
        "preferred_username": "also-not-email"
    }
    token = jwt.encode(payload, "secret", algorithm="HS256")

    email = EmailExtractor.from_token(token)
    assert email is None


def test_from_token_invalid_jwt():
    """測試無效的 JWT token"""
    email = EmailExtractor.from_token("not-a-valid-jwt-token")
    assert email is None


def test_from_token_empty_string():
    """測試空字串 token"""
    email = EmailExtractor.from_token("")
    assert email is None


def test_from_activity_from_property():
    """測試從 Activity 的 from_property.properties 提取 email"""
    turn_context = Mock(spec=TurnContext)
    activity = Mock(spec=Activity)
    from_property = Mock(spec=ChannelAccount)

    from_property.properties = {"email": "user@teams.com"}
    activity.from_property = from_property
    activity.channel_data = None
    turn_context.activity = activity

    email = EmailExtractor.from_activity(turn_context)
    assert email == "user@teams.com"


def test_from_activity_channel_data_upn():
    """測試從 channel_data 的 userPrincipalName 提取 email"""
    turn_context = Mock(spec=TurnContext)
    activity = Mock(spec=Activity)
    from_property = Mock(spec=ChannelAccount)

    from_property.properties = {}
    activity.from_property = from_property
    activity.channel_data = {
        "userPrincipalName": "user@company.com",
        "tenant": {"id": "tenant-123"}
    }
    turn_context.activity = activity

    email = EmailExtractor.from_activity(turn_context)
    assert email == "user@company.com"


def test_from_activity_channel_data_email():
    """測試從 channel_data 的 email 欄位提取"""
    turn_context = Mock(spec=TurnContext)
    activity = Mock(spec=Activity)
    from_property = Mock(spec=ChannelAccount)

    from_property.properties = {}
    activity.from_property = from_property
    activity.channel_data = {"email": "direct.email@test.com"}
    turn_context.activity = activity

    email = EmailExtractor.from_activity(turn_context)
    assert email == "direct.email@test.com"


def test_from_activity_no_email():
    """測試 Activity 中沒有 email"""
    turn_context = Mock(spec=TurnContext)
    activity = Mock(spec=Activity)
    from_property = Mock(spec=ChannelAccount)

    from_property.properties = {}
    activity.from_property = from_property
    activity.channel_data = {}
    turn_context.activity = activity

    email = EmailExtractor.from_activity(turn_context)
    assert email is None


def test_from_activity_exception_handling():
    """測試 Activity 處理異常"""
    turn_context = Mock(spec=TurnContext)
    turn_context.activity = None

    email = EmailExtractor.from_activity(turn_context)
    assert email is None


def test_get_email_from_token_success():
    """測試 get_email 從 token 成功取得（最快路徑）"""
    turn_context = Mock(spec=TurnContext)
    token_response = Mock(spec=TokenResponse)

    payload = {"email": "token.user@example.com"}
    token_response.token = jwt.encode(payload, "secret", algorithm="HS256")

    email = asyncio.run(
        EmailExtractor.get_email(
            turn_context,
            token_response,
            fallback_name="FallbackUser"
        )
    )

    assert email == "token.user@example.com"


def test_get_email_fallback_to_activity():
    """測試 get_email 從 token 失敗後使用 activity"""
    turn_context = Mock(spec=TurnContext)
    activity = Mock(spec=Activity)
    from_property = Mock(spec=ChannelAccount)

    token_response = Mock(spec=TokenResponse)
    token_response.token = "invalid-token"

    from_property.properties = {"email": "activity.user@example.com"}
    activity.from_property = from_property
    activity.channel_data = None
    turn_context.activity = activity

    email = asyncio.run(
        EmailExtractor.get_email(
            turn_context,
            token_response,
            fallback_name="FallbackUser"
        )
    )

    assert email == "activity.user@example.com"


def test_get_email_use_placeholder():
    """測試 get_email 所有方法都失敗時使用 placeholder"""
    turn_context = Mock(spec=TurnContext)
    activity = Mock(spec=Activity)
    from_property = Mock(spec=ChannelAccount)

    token_response = Mock(spec=TokenResponse)
    token_response.token = "invalid-token"

    from_property.properties = {}
    activity.from_property = from_property
    activity.channel_data = {}
    turn_context.activity = activity

    email = asyncio.run(
        EmailExtractor.get_email(
            turn_context,
            token_response,
            fallback_name="TestUser",
            use_graph_api=False
        )
    )

    assert email == "TestUser@example.com"


def test_get_display_name_from_token():
    """測試從 token 取得顯示名稱"""
    payload = {
        "name": "John Doe",
        "email": "john@example.com"
    }
    token = jwt.encode(payload, "secret", algorithm="HS256")

    name = EmailExtractor.get_display_name_from_token(token)
    assert name == "John Doe"


def test_get_display_name_from_token_given_name():
    """測試從 token 取得 given_name"""
    payload = {
        "given_name": "Jane",
        "family_name": "Smith"
    }
    token = jwt.encode(payload, "secret", algorithm="HS256")

    name = EmailExtractor.get_display_name_from_token(token)
    assert name == "Jane"


def test_get_display_name_from_token_no_name():
    """測試 token 沒有名稱資訊"""
    payload = {
        "email": "user@example.com"
    }
    token = jwt.encode(payload, "secret", algorithm="HS256")

    name = EmailExtractor.get_display_name_from_token(token)
    assert name is None
