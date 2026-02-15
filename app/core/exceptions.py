"""
統一異常處理系統

定義應用程式的異常類別和錯誤碼，提供一致的錯誤回應格式。
"""

from enum import Enum
from typing import Optional, Dict, Any
from fastapi import status


class ErrorCode(Enum):
    """
    錯誤碼枚舉

    格式：<模組>_<編號>
    - AUTH_xxx: 認證相關錯誤
    - GENIE_xxx: Databricks Genie API 相關錯誤
    - M365_xxx: Microsoft 365 相關錯誤
    - INPUT_xxx: 輸入驗證錯誤
    - RESOURCE_xxx: 資源相關錯誤
    - SYSTEM_xxx: 系統錯誤
    """

    # 認證錯誤 (401)
    AUTH_FAILED = "AUTH_001"
    AUTH_TOKEN_EXPIRED = "AUTH_002"
    AUTH_TOKEN_INVALID = "AUTH_003"
    AUTH_MISSING_CREDENTIALS = "AUTH_004"

    # Genie API 錯誤 (502/503)
    GENIE_API_ERROR = "GENIE_001"
    GENIE_TIMEOUT = "GENIE_002"
    GENIE_CONVERSATION_NOT_FOUND = "GENIE_003"
    GENIE_QUERY_FAILED = "GENIE_004"

    # M365 錯誤 (502/503)
    M365_API_ERROR = "M365_001"
    M365_GRAPH_TIMEOUT = "M365_002"
    M365_PERMISSION_DENIED = "M365_003"

    # 輸入驗證錯誤 (400)
    INPUT_VALIDATION_ERROR = "INPUT_001"
    INPUT_MISSING_REQUIRED_FIELD = "INPUT_002"
    INPUT_INVALID_FORMAT = "INPUT_003"

    # 資源錯誤 (404)
    RESOURCE_NOT_FOUND = "RESOURCE_001"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_002"

    # 系統錯誤 (500)
    SYSTEM_INTERNAL_ERROR = "SYSTEM_001"
    SYSTEM_SERVICE_UNAVAILABLE = "SYSTEM_002"
    SYSTEM_CONFIGURATION_ERROR = "SYSTEM_003"


class BotException(Exception):
    """
    應用程式基礎異常類別

    所有自定義異常都應繼承此類別。
    """

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    ):
        """
        初始化異常

        Args:
            code: 錯誤碼
            message: 使用者友善的錯誤訊息
            details: 額外的錯誤詳細資訊（不應包含敏感資訊）
            status_code: HTTP 狀態碼
        """
        self.code = code
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """轉換為字典格式（用於 API 回應）"""
        return {
            "error_code": self.code.value,
            "message": self.message,
            "details": self.details,
        }


# ==================== 認證異常 ====================


class AuthenticationError(BotException):
    """認證失敗異常"""

    def __init__(
        self,
        message: str = "認證失敗",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            code=ErrorCode.AUTH_FAILED,
            message=message,
            details=details,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class TokenExpiredError(BotException):
    """Token 過期異常"""

    def __init__(
        self,
        message: str = "認證 Token 已過期",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            code=ErrorCode.AUTH_TOKEN_EXPIRED,
            message=message,
            details=details,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class TokenInvalidError(BotException):
    """Token 無效異常"""

    def __init__(
        self,
        message: str = "認證 Token 無效",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            code=ErrorCode.AUTH_TOKEN_INVALID,
            message=message,
            details=details,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class MissingCredentialsError(BotException):
    """缺少認證憑證異常"""

    def __init__(
        self,
        message: str = "未提供認證憑證",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            code=ErrorCode.AUTH_MISSING_CREDENTIALS,
            message=message,
            details=details,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


# ==================== Genie API 異常 ====================


class GenieAPIError(BotException):
    """Genie API 錯誤異常"""

    def __init__(
        self,
        message: str = "Databricks Genie API 發生錯誤",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            code=ErrorCode.GENIE_API_ERROR,
            message=message,
            details=details,
            status_code=status.HTTP_502_BAD_GATEWAY,
        )


class GenieTimeoutError(BotException):
    """Genie API 超時異常"""

    def __init__(
        self,
        message: str = "Databricks Genie API 請求超時",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            code=ErrorCode.GENIE_TIMEOUT,
            message=message,
            details=details,
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        )


class GenieConversationNotFoundError(BotException):
    """Genie 對話不存在異常"""

    def __init__(
        self,
        message: str = "找不到指定的對話",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            code=ErrorCode.GENIE_CONVERSATION_NOT_FOUND,
            message=message,
            details=details,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class GenieQueryFailedError(BotException):
    """Genie 查詢失敗異常"""

    def __init__(
        self,
        message: str = "查詢執行失敗",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            code=ErrorCode.GENIE_QUERY_FAILED,
            message=message,
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ==================== M365 異常 ====================


class M365APIError(BotException):
    """Microsoft 365 API 錯誤異常"""

    def __init__(
        self,
        message: str = "Microsoft 365 API 發生錯誤",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            code=ErrorCode.M365_API_ERROR,
            message=message,
            details=details,
            status_code=status.HTTP_502_BAD_GATEWAY,
        )


class M365GraphTimeoutError(BotException):
    """Microsoft Graph API 超時異常"""

    def __init__(
        self,
        message: str = "Microsoft Graph API 請求超時",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            code=ErrorCode.M365_GRAPH_TIMEOUT,
            message=message,
            details=details,
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        )


class M365PermissionDeniedError(BotException):
    """Microsoft 365 權限拒絕異常"""

    def __init__(
        self,
        message: str = "沒有權限執行此操作",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            code=ErrorCode.M365_PERMISSION_DENIED,
            message=message,
            details=details,
            status_code=status.HTTP_403_FORBIDDEN,
        )


# ==================== 輸入驗證異常 ====================


class ValidationError(BotException):
    """輸入驗證錯誤異常"""

    def __init__(
        self,
        message: str = "輸入驗證失敗",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            code=ErrorCode.INPUT_VALIDATION_ERROR,
            message=message,
            details=details,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class MissingRequiredFieldError(BotException):
    """缺少必填欄位異常"""

    def __init__(
        self,
        field_name: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        if message is None:
            message = f"缺少必填欄位: {field_name}"

        if details is None:
            details = {}
        details["field_name"] = field_name

        super().__init__(
            code=ErrorCode.INPUT_MISSING_REQUIRED_FIELD,
            message=message,
            details=details,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class InvalidFormatError(BotException):
    """格式錯誤異常"""

    def __init__(
        self,
        field_name: str,
        expected_format: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        if message is None:
            message = f"欄位 '{field_name}' 格式錯誤，預期格式: {expected_format}"

        if details is None:
            details = {}
        details["field_name"] = field_name
        details["expected_format"] = expected_format

        super().__init__(
            code=ErrorCode.INPUT_INVALID_FORMAT,
            message=message,
            details=details,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


# ==================== 資源異常 ====================


class ResourceNotFoundError(BotException):
    """資源不存在異常"""

    def __init__(
        self,
        resource_type: str,
        resource_id: Optional[str] = None,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        if message is None:
            if resource_id:
                message = f"找不到 {resource_type}: {resource_id}"
            else:
                message = f"找不到 {resource_type}"

        if details is None:
            details = {}
        details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id

        super().__init__(
            code=ErrorCode.RESOURCE_NOT_FOUND,
            message=message,
            details=details,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ResourceAlreadyExistsError(BotException):
    """資源已存在異常"""

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        if message is None:
            message = f"{resource_type} 已存在: {resource_id}"

        if details is None:
            details = {}
        details["resource_type"] = resource_type
        details["resource_id"] = resource_id

        super().__init__(
            code=ErrorCode.RESOURCE_ALREADY_EXISTS,
            message=message,
            details=details,
            status_code=status.HTTP_409_CONFLICT,
        )


# ==================== 系統異常 ====================


class SystemInternalError(BotException):
    """系統內部錯誤異常"""

    def __init__(
        self,
        message: str = "系統內部錯誤",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            code=ErrorCode.SYSTEM_INTERNAL_ERROR,
            message=message,
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class ServiceUnavailableError(BotException):
    """服務不可用異常"""

    def __init__(
        self,
        service_name: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        if message is None:
            message = f"服務暫時不可用: {service_name}"

        if details is None:
            details = {}
        details["service_name"] = service_name

        super().__init__(
            code=ErrorCode.SYSTEM_SERVICE_UNAVAILABLE,
            message=message,
            details=details,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class ConfigurationError(BotException):
    """配置錯誤異常"""

    def __init__(
        self,
        config_key: str,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        if message is None:
            message = f"配置錯誤: {config_key} 未正確設定"

        if details is None:
            details = {}
        details["config_key"] = config_key

        super().__init__(
            code=ErrorCode.SYSTEM_CONFIGURATION_ERROR,
            message=message,
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
