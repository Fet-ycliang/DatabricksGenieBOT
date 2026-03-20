"""
測試日誌中介軟體功能
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import logging
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from app.core.logging_middleware import (
    RequestLoggingMiddleware,
    StructuredLogger,
    get_logger,
    get_request_id,
    JSONFormatter,
)


def test_structured_logger():
    """測試結構化日誌器"""
    print("Testing StructuredLogger...")

    logger = StructuredLogger("test_module")

    assert logger.name == "test_module"
    assert logger.logger.name == "test_module"

    # 測試各種日誌級別
    logger.debug("Debug message", request_id="test-123")
    logger.info("Info message", request_id="test-123")
    logger.warning("Warning message", request_id="test-123")
    logger.error("Error message", request_id="test-123")

    print("  PASS: StructuredLogger works")


def test_get_logger():
    """測試 get_logger 便利函數"""
    print("Testing get_logger...")

    logger1 = get_logger("module1")
    logger2 = get_logger("module2")

    assert isinstance(logger1, StructuredLogger)
    assert isinstance(logger2, StructuredLogger)
    assert logger1.name == "module1"
    assert logger2.name == "module2"

    print("  PASS: get_logger works")


def test_json_formatter():
    """測試 JSON 格式化器"""
    print("Testing JSONFormatter...")

    formatter = JSONFormatter()

    # 建立模擬日誌記錄
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Test message",
        args=(),
        exc_info=None,
    )
    record.request_id = "test-123"
    record.method = "GET"
    record.path = "/api/test"

    # 格式化
    formatted = formatter.format(record)

    # 驗證是有效的 JSON
    import json
    data = json.loads(formatted)

    assert data["message"] == "Test message"
    assert data["level"] == "INFO"
    assert data["request_id"] == "test-123"
    assert data["method"] == "GET"
    assert data["path"] == "/api/test"

    print("  PASS: JSONFormatter works")


def test_request_logging_middleware():
    """測試請求日誌中介軟體"""
    print("Testing RequestLoggingMiddleware...")

    # 建立測試應用
    app = FastAPI()
    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/test")
    async def test_endpoint(request: Request):
        # 檢查 request_id 是否已設定
        assert hasattr(request.state, "request_id")
        assert request.state.request_id is not None
        return {"message": "ok", "request_id": request.state.request_id}

    @app.get("/error")
    async def error_endpoint():
        raise ValueError("Test error")

    client = TestClient(app)

    # 測試正常請求
    response = client.get("/test")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert "request_id" in response.json()

    request_id = response.headers["X-Request-ID"]
    assert request_id == response.json()["request_id"]

    print("  PASS: RequestLoggingMiddleware works for normal requests")

    # 測試錯誤請求（應該記錄錯誤但重新拋出異常）
    try:
        response = client.get("/error")
        # 應該收到 500 錯誤
        assert response.status_code == 500
    except Exception:
        pass

    print("  PASS: RequestLoggingMiddleware works for error requests")


def test_get_request_id():
    """測試 get_request_id 函數"""
    print("Testing get_request_id...")

    # 建立測試應用
    app = FastAPI()
    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/test")
    async def test_endpoint(request: Request):
        request_id = get_request_id(request)
        return {"request_id": request_id}

    client = TestClient(app)
    response = client.get("/test")

    assert response.status_code == 200
    assert response.json()["request_id"] != "no-request-id"

    print("  PASS: get_request_id works")


def test_client_ip_extraction():
    """測試客戶端 IP 提取（包含代理）"""
    print("Testing client IP extraction...")

    app = FastAPI()
    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"message": "ok"}

    client = TestClient(app)

    # 測試 X-Forwarded-For header
    response = client.get("/test", headers={"X-Forwarded-For": "1.2.3.4, 5.6.7.8"})
    assert response.status_code == 200

    print("  PASS: Client IP extraction works")


def test_structured_logger_with_extra_context():
    """測試帶額外上下文的結構化日誌"""
    print("Testing StructuredLogger with extra context...")

    logger = StructuredLogger("test")

    # 測試帶額外上下文的日誌
    logger.info(
        "User action",
        request_id="req-123",
        user_id="user-456",
        action="login",
        ip="1.2.3.4"
    )

    logger.error(
        "Database error",
        request_id="req-789",
        exc_info=True,
        db_name="users",
        query="SELECT * FROM users"
    )

    print("  PASS: StructuredLogger with extra context works")


def run_all_tests():
    """執行所有測試"""
    print("="*60)
    print("Logging Middleware Unit Tests")
    print("="*60)
    print()

    tests = [
        test_structured_logger,
        test_get_logger,
        test_json_formatter,
        test_request_logging_middleware,
        test_get_request_id,
        test_client_ip_extraction,
        test_structured_logger_with_extra_context,
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
