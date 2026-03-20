"""
Email 提取工具

從多個來源（JWT Token, Activity, Graph API）取得用戶 email。
使用混合策略（Waterfall）確保最佳性能和可靠性。
"""

import jwt
import logging
import httpx
from typing import Optional
from botbuilder.core import TurnContext
from botbuilder.schema import TokenResponse

logger = logging.getLogger(__name__)


class EmailExtractor:
    """
    從多個來源取得用戶 email 的工具類別

    優先級：
    1. JWT Token 解碼（最快，< 1ms）
    2. Activity Channel Data（次快，< 1ms）
    3. Graph API（備用，200-500ms）
    4. Placeholder（最後備案）
    """

    @staticmethod
    def from_token(access_token: str) -> Optional[str]:
        """
        從 JWT Token 解碼取得 email

        Args:
            access_token: Azure AD access token (JWT 格式)

        Returns:
            用戶 email，如果無法取得則返回 None

        Note:
            不驗證簽名，因為 token 已經由 Bot Framework 驗證過
        """
        try:
            # 解碼 JWT（不驗證簽名）
            decoded = jwt.decode(
                access_token,
                options={
                    "verify_signature": False,  # Bot Framework 已驗證
                    "verify_aud": False,
                    "verify_exp": False
                }
            )

            # 按優先級嘗試多個可能的 email claim
            email = (
                decoded.get("email") or              # 標準 email claim
                decoded.get("preferred_username") or # UPN (通常是 email 格式)
                decoded.get("upn") or                # User Principal Name
                decoded.get("unique_name")           # 舊版 Azure AD
            )

            if email and "@" in email:
                logger.debug(f"從 JWT token 取得 email: {email}")
                return email
            else:
                logger.debug(f"Token 中無有效 email，可用 claims: {list(decoded.keys())}")

        except jwt.DecodeError as e:
            logger.debug(f"JWT 解碼失敗（可能不是 JWT 格式）: {e}")
        except Exception as e:
            logger.warning(f"Token 解碼發生未預期錯誤: {e}", exc_info=True)

        return None

    @staticmethod
    def from_activity(turn_context: TurnContext) -> Optional[str]:
        """
        從 Activity 的 channel data 取得 email

        Args:
            turn_context: Bot Framework TurnContext

        Returns:
            用戶 email，如果無法取得則返回 None

        Note:
            Teams 可能在 channel_data 或 from_property.properties 中包含用戶資訊
        """
        try:
            activity = turn_context.activity

            # 方法 1: 檢查 from 屬性的 properties
            if hasattr(activity.from_property, "properties"):
                props = activity.from_property.properties
                if isinstance(props, dict) and "email" in props:
                    email = props["email"]
                    if email and "@" in email:
                        logger.debug(f"從 activity.from.properties 取得 email: {email}")
                        return email

            # 方法 2: 檢查 channel data（Teams 特定）
            if activity.channel_data:
                if isinstance(activity.channel_data, dict):
                    # Teams 可能包含 userPrincipalName
                    upn = activity.channel_data.get("userPrincipalName")
                    if upn and "@" in upn:
                        logger.debug(f"從 channel_data 取得 email: {upn}")
                        return upn

                    # 檢查是否有直接的 email 欄位
                    email = activity.channel_data.get("email")
                    if email and "@" in email:
                        logger.debug(f"從 channel_data.email 取得 email: {email}")
                        return email

        except Exception as e:
            logger.debug(f"從 activity 取得 email 失敗: {e}")

        return None

    @staticmethod
    async def from_graph_api(access_token: str, timeout: float = 5.0) -> Optional[str]:
        """
        從 Microsoft Graph API 取得 email

        Args:
            access_token: Azure AD access token
            timeout: API 超時時間（秒）

        Returns:
            用戶 email，如果調用失敗則返回 None

        Note:
            需要 token 包含 User.Read scope
            這是最慢的方法（200-500ms），應作為最後備用方案
        """
        try:
            url = "https://graph.microsoft.com/v1.0/me"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=headers,
                    timeout=timeout
                )

                if response.status_code == 200:
                    profile = response.json()
                    email = (
                        profile.get("mail") or
                        profile.get("userPrincipalName")
                    )

                    if email and "@" in email:
                        logger.debug(f"從 Graph API 取得 email: {email}")
                        return email
                    else:
                        logger.warning(f"Graph API 回應無 email: {list(profile.keys())}")
                else:
                    logger.warning(
                        f"Graph API 返回 {response.status_code}: "
                        f"{response.text[:200]}"
                    )

        except httpx.TimeoutException:
            logger.warning(f"Graph API 超時（{timeout}s）")
        except httpx.HTTPError as e:
            logger.warning(f"Graph API HTTP 錯誤: {e}")
        except Exception as e:
            logger.error(f"Graph API 調用失敗: {e}", exc_info=True)

        return None

    @staticmethod
    async def get_email(
        turn_context: TurnContext,
        token_response: TokenResponse,
        fallback_name: str = "User",
        use_graph_api: bool = True
    ) -> str:
        """
        使用混合策略取得用戶 email

        優先級：Token → Activity → Graph API → Placeholder

        Args:
            turn_context: Bot Framework TurnContext
            token_response: SSO 成功後的 TokenResponse
            fallback_name: Placeholder email 的名稱部分
            use_graph_api: 是否允許調用 Graph API（預設 True）

        Returns:
            用戶 email（保證返回非空字串）

        Example:
            ```python
            email = await EmailExtractor.get_email(
                turn_context,
                token_response,
                fallback_name="John"
            )
            # 可能結果：
            # - "john@company.com" (from token)
            # - "john@company.com" (from activity)
            # - "john@company.com" (from Graph API)
            # - "John@example.com" (placeholder)
            ```
        """
        # 方法 1: 從 JWT Token 解碼（最快，< 1ms）
        email = EmailExtractor.from_token(token_response.token)
        if email:
            logger.info(f"✅ Email 來源: JWT Token ({email})")
            return email

        # 方法 2: 從 Activity Channel Data（次快，< 1ms）
        email = EmailExtractor.from_activity(turn_context)
        if email:
            logger.info(f"✅ Email 來源: Activity Channel Data ({email})")
            return email

        # 方法 3: 從 Graph API（最慢，200-500ms，需要網路）
        if use_graph_api:
            email = await EmailExtractor.from_graph_api(token_response.token)
            if email:
                logger.info(f"✅ Email 來源: Microsoft Graph API ({email})")
                return email

        # 方法 4: Placeholder（最後備案）
        email = f"{fallback_name}@example.com"
        logger.warning(
            f"⚠️ 無法取得真實 email，使用 placeholder: {email}\n"
            f"   建議檢查：\n"
            f"   1. OAuth Connection Scopes 是否包含 'email'\n"
            f"   2. Azure AD App 權限是否已授予\n"
            f"   3. Token 是否包含 email claim（檢查日誌）"
        )
        return email

    @staticmethod
    def get_display_name_from_token(access_token: str) -> Optional[str]:
        """
        從 JWT Token 取得顯示名稱（可選功能）

        Args:
            access_token: Azure AD access token

        Returns:
            用戶顯示名稱，如果無法取得則返回 None
        """
        try:
            decoded = jwt.decode(
                access_token,
                options={"verify_signature": False}
            )

            name = (
                decoded.get("name") or
                decoded.get("given_name") or
                decoded.get("family_name")
            )

            if name:
                logger.debug(f"從 token 取得 display name: {name}")
                return name

        except Exception as e:
            logger.debug(f"從 token 取得 name 失敗: {e}")

        return None
