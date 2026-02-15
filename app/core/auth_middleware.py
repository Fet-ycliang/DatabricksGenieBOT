"""
認證中介軟體

提供統一的認證機制，保護 API 端點。
"""

import logging
from typing import Optional
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWKClient
from app.core.config import DefaultConfig

logger = logging.getLogger(__name__)

security = HTTPBearer()
CONFIG = DefaultConfig()


class AuthenticationError(Exception):
    """認證失敗異常"""
    pass


async def verify_bot_framework_signature(
    authorization: Optional[str] = Header(None)
) -> dict:
    """
    驗證 Bot Framework 請求簽名

    Bot Framework 使用 JWT Bearer Token 驗證請求。
    Token 包含在 Authorization header 中。

    Args:
        authorization: Authorization header 值

    Returns:
        解碼後的 token payload

    Raises:
        HTTPException: 認證失敗時

    Note:
        此函數驗證 Bot Framework 發送的請求。
        生產環境應使用 Bot Framework SDK 的 JwtTokenValidation。
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供認證憑證",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 檢查 Bearer 前綴
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無效的認證格式，需要 Bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization[7:]  # 移除 "Bearer " 前綴

    try:
        # 在生產環境中，應該使用 Bot Framework 的 JwtTokenValidation
        # 這裡提供簡化版本用於示範
        #
        # from botframework.connector.auth import JwtTokenValidation
        # claims = await JwtTokenValidation.validate_auth_header(authorization)

        # 暫時跳過驗證（僅檢查格式）
        # TODO: 實作完整的 Bot Framework JWT 驗證
        logger.warning("Bot Framework 簽名驗證未完全實作，僅檢查格式")

        return {"validated": True, "token": token}

    except Exception as e:
        logger.error(f"Bot Framework 簽名驗證失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="簽名驗證失敗",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def verify_azure_ad_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    驗證 Azure AD JWT Token

    驗證用戶提供的 Azure AD access token。
    Token 必須包含在 Authorization header 中，格式：Bearer <token>

    Args:
        credentials: HTTP Bearer 認證憑證

    Returns:
        解碼後的 token payload，包含用戶資訊

    Raises:
        HTTPException: Token 無效或過期時

    Example:
        ```
        curl -H "Authorization: Bearer <token>" https://api.example.com/m365/profile
        ```
    """
    token = credentials.credentials

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供認證 token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # 驗證 Azure AD JWT Token
        # 需要從 Azure AD 取得公鑰來驗證簽名

        if not CONFIG.APP_TENANTID:
            logger.error("APP_TENANTID 未配置，無法驗證 Azure AD token")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="伺服器認證配置錯誤"
            )

        # Azure AD OpenID Connect metadata endpoint
        jwks_url = f"https://login.microsoftonline.com/{CONFIG.APP_TENANTID}/discovery/v2.0/keys"

        # 取得 JWT 公鑰並驗證
        jwks_client = PyJWKClient(jwks_url)
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        # 解碼並驗證 token
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=CONFIG.APP_ID,  # Token audience 應該是我們的 App ID
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_aud": True,
            }
        )

        logger.info(f"Token 驗證成功: user={payload.get('preferred_username', 'unknown')}")

        return payload

    except jwt.ExpiredSignatureError:
        logger.warning("Token 已過期")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 已過期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidAudienceError:
        logger.warning("Token audience 不符")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 無效（audience 不符）",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Token 無效: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 無效",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Token 驗證失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認證失敗",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    token_payload: dict = Depends(verify_azure_ad_token)
) -> dict:
    """
    從 token 中提取當前用戶資訊

    Args:
        token_payload: 已驗證的 token payload

    Returns:
        用戶資訊字典

    Example:
        ```python
        @router.get("/protected")
        async def protected_endpoint(user: dict = Depends(get_current_user)):
            return {"user_id": user["user_id"], "email": user["email"]}
        ```
    """
    try:
        user_info = {
            "user_id": token_payload.get("oid"),  # Object ID
            "email": token_payload.get("preferred_username") or token_payload.get("email"),
            "name": token_payload.get("name"),
            "tenant_id": token_payload.get("tid"),
        }

        if not user_info["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="無法從 token 中提取用戶資訊"
            )

        return user_info

    except Exception as e:
        logger.error(f"提取用戶資訊失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無效的用戶資訊"
        )


# 開發環境：允許繞過認證的可選依賴
async def optional_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """
    可選認證依賴（僅用於開發環境）

    如果提供了 token 則驗證，否則返回 None。

    Warning:
        僅用於開發和測試環境，生產環境應使用強制認證。
    """
    if not credentials:
        logger.warning("未提供認證憑證，使用匿名訪問（僅開發環境）")
        return None

    try:
        return await verify_azure_ad_token(credentials)
    except HTTPException:
        # 在可選認證模式下，驗證失敗不拋出異常
        logger.warning("Token 驗證失敗，使用匿名訪問")
        return None
