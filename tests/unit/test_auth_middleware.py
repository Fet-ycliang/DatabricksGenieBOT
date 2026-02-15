"""
測試認證中介軟體功能
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pytest
from fastapi import HTTPException
from unittest.mock import Mock, patch, AsyncMock
from app.core.auth_middleware import (
    verify_bot_framework_signature,
    verify_azure_ad_token,
    get_current_user
)


def test_missing_authorization_header():
    """測試缺少 Authorization header"""
    print("Testing missing authorization header...")

    # 測試 Bot Framework 簽名驗證
    try:
        import asyncio
        asyncio.run(verify_bot_framework_signature(authorization=None))
        assert False, "Should raise HTTPException"
    except HTTPException as e:
        assert e.status_code == 401
        assert "未提供認證憑證" in e.detail
        print("  PASS: Missing authorization header detected")


def test_invalid_authorization_format():
    """測試無效的 Authorization 格式"""
    print("Testing invalid authorization format...")

    # 不以 "Bearer " 開頭
    try:
        import asyncio
        asyncio.run(verify_bot_framework_signature(authorization="InvalidToken"))
        assert False, "Should raise HTTPException"
    except HTTPException as e:
        assert e.status_code == 401
        assert "無效的認證格式" in e.detail
        print("  PASS: Invalid format detected")


def test_valid_authorization_format():
    """測試有效的 Authorization 格式（跳過實際驗證）"""
    print("Testing valid authorization format...")

    import asyncio
    result = asyncio.run(
        verify_bot_framework_signature(authorization="Bearer test_token")
    )

    assert result is not None
    assert "validated" in result
    print("  PASS: Valid format accepted (signature validation skipped)")


def test_get_current_user():
    """測試從 token payload 提取用戶資訊"""
    print("Testing get_current_user...")

    # Mock token payload
    mock_payload = {
        "oid": "user-123",
        "preferred_username": "user@example.com",
        "name": "Test User",
        "tid": "tenant-456"
    }

    import asyncio
    user_info = asyncio.run(get_current_user(token_payload=mock_payload))

    assert user_info["user_id"] == "user-123"
    assert user_info["email"] == "user@example.com"
    assert user_info["name"] == "Test User"
    assert user_info["tenant_id"] == "tenant-456"

    print("  PASS: User info extracted correctly")


def test_get_current_user_missing_oid():
    """測試缺少 user_id (oid) 的情況"""
    print("Testing get_current_user with missing oid...")

    # Token payload 缺少 oid
    mock_payload = {
        "preferred_username": "user@example.com",
        "name": "Test User"
    }

    try:
        import asyncio
        asyncio.run(get_current_user(token_payload=mock_payload))
        assert False, "Should raise HTTPException"
    except HTTPException as e:
        assert e.status_code == 401
        print("  PASS: Missing oid detected")


def test_get_current_user_fallback_email():
    """測試 email 欄位的備用邏輯"""
    print("Testing email fallback...")

    # 使用 email 而非 preferred_username
    mock_payload = {
        "oid": "user-123",
        "email": "fallback@example.com",
        "name": "Test User",
        "tid": "tenant-456"
    }

    import asyncio
    user_info = asyncio.run(get_current_user(token_payload=mock_payload))

    assert user_info["email"] == "fallback@example.com"
    print("  PASS: Email fallback works")


def run_all_tests():
    """執行所有測試"""
    print("="*60)
    print("Authentication Middleware Unit Tests")
    print("="*60)
    print()

    tests = [
        test_missing_authorization_header,
        test_invalid_authorization_format,
        test_valid_authorization_format,
        test_get_current_user,
        test_get_current_user_missing_oid,
        test_get_current_user_fallback_email,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print()
    print("="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
