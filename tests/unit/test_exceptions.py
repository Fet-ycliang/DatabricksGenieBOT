"""
測試異常處理系統
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.core.exceptions import (
    ErrorCode,
    BotException,
    AuthenticationError,
    TokenExpiredError,
    GenieAPIError,
    ValidationError,
    ResourceNotFoundError,
    SystemInternalError,
)


def test_error_code_enum():
    """測試錯誤碼枚舉"""
    print("Testing ErrorCode enum...")

    assert ErrorCode.AUTH_FAILED.value == "AUTH_001"
    assert ErrorCode.GENIE_API_ERROR.value == "GENIE_001"
    assert ErrorCode.INPUT_VALIDATION_ERROR.value == "INPUT_001"
    assert ErrorCode.RESOURCE_NOT_FOUND.value == "RESOURCE_001"
    assert ErrorCode.SYSTEM_INTERNAL_ERROR.value == "SYSTEM_001"

    print("  PASS: ErrorCode enum works")


def test_bot_exception_basic():
    """測試基礎異常類別"""
    print("Testing BotException basic...")

    exc = BotException(
        code=ErrorCode.SYSTEM_INTERNAL_ERROR,
        message="Test error",
        details={"key": "value"},
        status_code=500
    )

    assert exc.code == ErrorCode.SYSTEM_INTERNAL_ERROR
    assert exc.message == "Test error"
    assert exc.details == {"key": "value"}
    assert exc.status_code == 500

    print("  PASS: BotException basic works")


def test_bot_exception_to_dict():
    """測試異常轉字典"""
    print("Testing BotException to_dict...")

    exc = BotException(
        code=ErrorCode.AUTH_FAILED,
        message="Authentication failed",
        details={"reason": "invalid_token"}
    )

    result = exc.to_dict()

    assert result["error_code"] == "AUTH_001"
    assert result["message"] == "Authentication failed"
    assert result["details"]["reason"] == "invalid_token"

    print("  PASS: to_dict works")


def test_authentication_error():
    """測試認證錯誤異常"""
    print("Testing AuthenticationError...")

    exc = AuthenticationError()

    assert exc.code == ErrorCode.AUTH_FAILED
    assert exc.status_code == 401
    assert "認證失敗" in exc.message

    # 自定義訊息
    exc2 = AuthenticationError(message="Custom auth error")
    assert exc2.message == "Custom auth error"

    print("  PASS: AuthenticationError works")


def test_token_expired_error():
    """測試 Token 過期異常"""
    print("Testing TokenExpiredError...")

    exc = TokenExpiredError()

    assert exc.code == ErrorCode.AUTH_TOKEN_EXPIRED
    assert exc.status_code == 401
    assert "過期" in exc.message

    print("  PASS: TokenExpiredError works")


def test_genie_api_error():
    """測試 Genie API 錯誤"""
    print("Testing GenieAPIError...")

    exc = GenieAPIError(
        message="API request failed",
        details={"error": "timeout"}
    )

    assert exc.code == ErrorCode.GENIE_API_ERROR
    assert exc.status_code == 502
    assert exc.details["error"] == "timeout"

    print("  PASS: GenieAPIError works")


def test_validation_error():
    """測試驗證錯誤"""
    print("Testing ValidationError...")

    exc = ValidationError(
        message="Invalid input",
        details={"field": "email", "error": "invalid format"}
    )

    assert exc.code == ErrorCode.INPUT_VALIDATION_ERROR
    assert exc.status_code == 400

    print("  PASS: ValidationError works")


def test_resource_not_found_error():
    """測試資源不存在錯誤"""
    print("Testing ResourceNotFoundError...")

    exc = ResourceNotFoundError(
        resource_type="User",
        resource_id="user123"
    )

    assert exc.code == ErrorCode.RESOURCE_NOT_FOUND
    assert exc.status_code == 404
    assert exc.details["resource_type"] == "User"
    assert exc.details["resource_id"] == "user123"
    assert "User" in exc.message
    assert "user123" in exc.message

    print("  PASS: ResourceNotFoundError works")


def test_system_internal_error():
    """測試系統內部錯誤"""
    print("Testing SystemInternalError...")

    exc = SystemInternalError()

    assert exc.code == ErrorCode.SYSTEM_INTERNAL_ERROR
    assert exc.status_code == 500

    print("  PASS: SystemInternalError works")


def test_exception_inheritance():
    """測試異常繼承關係"""
    print("Testing exception inheritance...")

    exc = AuthenticationError()

    assert isinstance(exc, BotException)
    assert isinstance(exc, Exception)

    print("  PASS: Exception inheritance works")


def test_custom_details():
    """測試自定義詳細資訊"""
    print("Testing custom details...")

    exc = GenieAPIError(
        message="API error",
        details={
            "status_code": 500,
            "response": {"error": "internal_error"},
            "retry_count": 3
        }
    )

    assert exc.details["status_code"] == 500
    assert exc.details["response"]["error"] == "internal_error"
    assert exc.details["retry_count"] == 3

    print("  PASS: Custom details work")


def run_all_tests():
    """執行所有測試"""
    print("="*60)
    print("Exception System Unit Tests")
    print("="*60)
    print()

    tests = [
        test_error_code_enum,
        test_bot_exception_basic,
        test_bot_exception_to_dict,
        test_authentication_error,
        test_token_expired_error,
        test_genie_api_error,
        test_validation_error,
        test_resource_not_found_error,
        test_system_internal_error,
        test_exception_inheritance,
        test_custom_details,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {e}")
            import traceback
            traceback.print_exc()
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
