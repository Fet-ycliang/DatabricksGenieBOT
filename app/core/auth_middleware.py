"""
認證中介軟體

提供統一的認證機制，保護 API 端點。
"""

import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWKClient
from app.core.config import DefaultConfig

logger = logging.getLogger(__name__)

security = HTTPBearer()
CONFIG = DefaultConfig()

# 模組級快取：避免每次請求都重新建立 PyJWKClient（含 JWKS 下載）
_jwks_client_cache: dict[str, PyJWKClient] = {}


def _get_jwks_client(tenant_id: str) -> PyJWKClient:
    """取得或建立快取的 PyJWKClient"""
    if tenant_id not in _jwks_client_cache:
        jwks_url = f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
        _jwks_client_cache[tenant_id] = PyJWKClient(jwks_url)
    return _jwks_client_cache[tenant_id]


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
    """
    token = credentials.credentials

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供認證 token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        if not CONFIG.APP_TENANTID:
            logger.error("APP_TENANTID 未配置，無法驗證 Azure AD token")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="伺服器認證配置錯誤"
            )

        # 取得快取的 JWKS client
        jwks_client = _get_jwks_client(CONFIG.APP_TENANTID)
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        # 解碼並驗證 token
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=CONFIG.APP_ID,
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

    except HTTPException:
        raise
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
