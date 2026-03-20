"""
日誌中介軟體

提供統一的日誌和請求追蹤功能。
"""

import time
import logging
from uuid import uuid4
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    請求日誌中介軟體

    為每個請求生成唯一的 request_id，記錄請求和回應資訊。
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        處理請求並記錄日誌

        Args:
            request: FastAPI 請求物件
            call_next: 下一個中介軟體或路由處理器

        Returns:
            Response 物件
        """
        # 生成請求 ID
        request_id = str(uuid4())
        request.state.request_id = request_id

        # 記錄請求開始
        start_time = time.time()

        # 取得客戶端 IP（考慮代理）
        client_ip = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()

        # 記錄請求資訊
        logger.info(
            f"[{request_id}] --> {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query": str(request.url.query) if request.url.query else None,
                "client_ip": client_ip,
                "user_agent": request.headers.get("User-Agent"),
            },
        )

        # 處理請求
        try:
            response = await call_next(request)

            # 計算處理時間
            duration_ms = int((time.time() - start_time) * 1000)

            # 記錄回應資訊
            logger.info(
                f"[{request_id}] <-- {request.method} {request.url.path} "
                f"{response.status_code} ({duration_ms}ms)",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                },
            )

            # 將 request_id 加入回應 header
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as exc:
            # 計算處理時間（包含錯誤處理）
            duration_ms = int((time.time() - start_time) * 1000)

            # 記錄錯誤
            logger.error(
                f"[{request_id}] <-- {request.method} {request.url.path} "
                f"ERROR ({duration_ms}ms): {type(exc).__name__}: {str(exc)}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                    "duration_ms": duration_ms,
                },
                exc_info=True,
            )

            # 重新拋出異常讓全域異常處理器處理
            raise


class StructuredLogger:
    """
    結構化日誌輔助類別

    提供一致的日誌格式和上下文管理。
    """

    def __init__(self, name: str):
        """
        初始化結構化日誌器

        Args:
            name: 日誌器名稱（通常是模組名稱）
        """
        self.logger = logging.getLogger(name)
        self.name = name

    def _log_with_context(
        self,
        level: int,
        message: str,
        request_id: str = None,
        **kwargs,
    ) -> None:
        """
        記錄帶上下文的日誌

        Args:
            level: 日誌級別
            message: 日誌訊息
            request_id: 請求 ID（可選）
            **kwargs: 額外的上下文資訊
        """
        extra = {"logger_name": self.name}

        if request_id:
            extra["request_id"] = request_id
            message = f"[{request_id}] {message}"

        # 合併額外的上下文
        extra.update(kwargs)

        self.logger.log(level, message, extra=extra)

    def debug(self, message: str, request_id: str = None, **kwargs) -> None:
        """記錄 DEBUG 級別日誌"""
        self._log_with_context(logging.DEBUG, message, request_id, **kwargs)

    def info(self, message: str, request_id: str = None, **kwargs) -> None:
        """記錄 INFO 級別日誌"""
        self._log_with_context(logging.INFO, message, request_id, **kwargs)

    def warning(self, message: str, request_id: str = None, **kwargs) -> None:
        """記錄 WARNING 級別日誌"""
        self._log_with_context(logging.WARNING, message, request_id, **kwargs)

    def error(self, message: str, request_id: str = None, exc_info=False, **kwargs) -> None:
        """記錄 ERROR 級別日誌"""
        if exc_info:
            self.logger.error(
                f"[{request_id}] {message}" if request_id else message,
                extra={"request_id": request_id, "logger_name": self.name, **kwargs},
                exc_info=True,
            )
        else:
            self._log_with_context(logging.ERROR, message, request_id, **kwargs)

    def critical(self, message: str, request_id: str = None, **kwargs) -> None:
        """記錄 CRITICAL 級別日誌"""
        self._log_with_context(logging.CRITICAL, message, request_id, **kwargs)


def get_request_id(request: Request) -> str:
    """
    從 Request 物件中取得 request_id

    Args:
        request: FastAPI Request 物件

    Returns:
        request_id 字串，如果不存在則返回 "no-request-id"
    """
    return getattr(request.state, "request_id", "no-request-id")


# 便利函數：建立結構化日誌器
def get_logger(name: str) -> StructuredLogger:
    """
    建立結構化日誌器

    Args:
        name: 日誌器名稱（通常使用 __name__）

    Returns:
        StructuredLogger 實例

    Example:
        ```python
        from app.core.logging_middleware import get_logger

        logger = get_logger(__name__)
        logger.info("處理請求", request_id="abc-123", user_id="user-456")
        ```
    """
    return StructuredLogger(name)


# JSON 格式化器（可選，用於結構化日誌輸出）
class JSONFormatter(logging.Formatter):
    """
    JSON 格式化器

    將日誌輸出為 JSON 格式，便於日誌收集系統處理。
    """

    def format(self, record: logging.LogRecord) -> str:
        """格式化日誌記錄為 JSON"""
        import json
        from datetime import datetime

        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 加入額外的上下文資訊
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        if hasattr(record, "method"):
            log_data["method"] = record.method

        if hasattr(record, "path"):
            log_data["path"] = record.path

        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code

        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms

        if hasattr(record, "client_ip"):
            log_data["client_ip"] = record.client_ip

        # 如果有異常資訊，加入堆疊追蹤
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


def configure_json_logging(log_file: str = None) -> None:
    """
    配置 JSON 格式日誌

    Args:
        log_file: JSON 日誌檔案路徑（可選）

    Example:
        ```python
        from app.core.logging_middleware import configure_json_logging

        # 配置 JSON 日誌輸出到檔案
        configure_json_logging("logs/app.json")
        ```
    """
    if log_file:
        json_handler = logging.FileHandler(log_file, encoding="utf-8")
        json_handler.setFormatter(JSONFormatter())
        logging.getLogger().addHandler(json_handler)
