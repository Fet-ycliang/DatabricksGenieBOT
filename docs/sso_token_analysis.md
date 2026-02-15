# Teams SSO Token 分析與最佳取得 Email 方法

**日期**：2026-02-16
**問題**：如何在 SSO 後取得真實的用戶 email？

## 🎯 您的問題很重要！

您完全正確質疑為什麼要透過 Graph API 取得 email。有更好的方法！

## 📊 三種取得 Email 的方法比較

### 方法 1: 直接從 JWT Token 解碼 ⚡（最佳）

**原理**：
- Azure AD 的 access token 是 JWT 格式
- Token 本身包含 claims（聲明），包括 email
- 不需要額外的 API 調用

**優點**：
- ✅ **最快**：無網路延遲
- ✅ **最省資源**：不消耗 API 配額
- ✅ **最可靠**：不依賴外部服務
- ✅ **離線可用**：不需要網路連接

**缺點**：
- ⚠️ 需要驗證 token 簽名（安全考量）
- ⚠️ Email 可能不在 token 中（取決於 scopes）

**實作**：

```python
import jwt
from typing import Optional

def get_email_from_token(access_token: str) -> Optional[str]:
    """
    從 Azure AD JWT Token 中解碼取得 email

    注意：這裡不驗證簽名，因為 token 已經由 Bot Framework 驗證過
    """
    try:
        # 解碼 JWT（不驗證簽名，因為已由 Bot Framework 驗證）
        decoded = jwt.decode(
            access_token,
            options={
                "verify_signature": False,  # Bot Framework 已驗證
                "verify_aud": False,
                "verify_exp": False
            }
        )

        # 嘗試多個可能的 email 欄位
        email = (
            decoded.get("email") or           # 標準 email claim
            decoded.get("preferred_username") or  # UPN (常是 email)
            decoded.get("upn") or             # User Principal Name
            decoded.get("unique_name")        # 舊版 AD
        )

        return email
    except Exception as e:
        logger.error(f"解碼 token 失敗: {e}")
        return None
```

**Token Claims 範例**：
```json
{
  "aud": "api://your-app-id",
  "iss": "https://login.microsoftonline.com/tenant-id/v2.0",
  "iat": 1708084800,
  "nbf": 1708084800,
  "exp": 1708088400,
  "email": "user@company.com",          // ← 目標！
  "preferred_username": "user@company.com",
  "name": "User Name",
  "oid": "user-object-id",
  "tid": "tenant-id",
  "scp": "User.Read email profile openid"
}
```

### 方法 2: 從 Activity Channel Data 取得 🔍（次佳）

**原理**：
- Teams 在 Activity 中可能包含用戶資訊
- Channel-specific data 可能已有 email

**優點**：
- ✅ 快速（無需解碼）
- ✅ Teams 原生支援

**缺點**：
- ⚠️ 不保證所有 channel 都有
- ⚠️ 格式可能不一致

**實作**：

```python
def get_email_from_activity(turn_context: TurnContext) -> Optional[str]:
    """從 Activity 的 channel data 取得 email"""
    activity = turn_context.activity

    # 方法 1: 檢查 from 屬性
    if hasattr(activity.from_property, "properties"):
        properties = activity.from_property.properties
        if "email" in properties:
            return properties["email"]

    # 方法 2: 檢查 channel data（Teams 特定）
    if activity.channel_data:
        # Teams 可能在 channel_data.tenant.id 或其他位置
        if isinstance(activity.channel_data, dict):
            # 嘗試從 Teams channel data 取得
            tenant_info = activity.channel_data.get("tenant", {})
            # Teams AAD 用戶資訊
            if "userPrincipalName" in activity.channel_data:
                return activity.channel_data["userPrincipalName"]

    # 方法 3: 檢查 AAD object ID（可用於後續查詢）
    if hasattr(activity.from_property, "aad_object_id"):
        aad_oid = activity.from_property.aad_object_id
        # 此時可以用 OID 查詢，但仍需 Graph API

    return None
```

### 方法 3: 調用 Graph API 🌐（最慢但最完整）

**原理**：
- 使用 token 調用 Microsoft Graph `/me` 端點
- 取得完整的用戶資料

**優點**：
- ✅ 最完整的用戶資訊
- ✅ 保證有資料（如果有權限）

**缺點**：
- ❌ 網路延遲（~200-500ms）
- ❌ 消耗 API 配額
- ❌ 需要 `User.Read` 權限
- ❌ 可能失敗（網路問題）

**實作**：

```python
async def get_email_from_graph(access_token: str) -> Optional[str]:
    """從 Microsoft Graph API 取得 email"""
    url = "https://graph.microsoft.com/v1.0/me"
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=5.0)
            if response.status_code == 200:
                profile = response.json()
                return profile.get("mail") or profile.get("userPrincipalName")
    except Exception as e:
        logger.error(f"Graph API 調用失敗: {e}")

    return None
```

## 🏆 推薦方案：混合策略（Waterfall）

**最佳實踐**：依序嘗試，快速 fallback

```python
async def get_user_email(
    turn_context: TurnContext,
    token_response: TokenResponse
) -> str:
    """
    混合策略取得用戶 email

    優先級：
    1. JWT Token 解碼（最快）
    2. Activity Channel Data（次快）
    3. Graph API（最完整）
    4. Placeholder（最後備案）
    """
    name = turn_context.activity.from_property.name or "User"

    # 方法 1: 從 JWT Token 解碼
    email = get_email_from_token(token_response.token)
    if email and "@" in email:
        logger.info(f"✅ 從 token 取得 email: {email}")
        return email

    # 方法 2: 從 Activity Channel Data
    email = get_email_from_activity(turn_context)
    if email and "@" in email:
        logger.info(f"✅ 從 channel data 取得 email: {email}")
        return email

    # 方法 3: 調用 Graph API（最後手段）
    try:
        email = await get_email_from_graph(token_response.token)
        if email and "@" in email:
            logger.info(f"✅ 從 Graph API 取得 email: {email}")
            return email
    except Exception as e:
        logger.warning(f"Graph API 失敗: {e}")

    # 方法 4: Placeholder
    email = f"{name}@example.com"
    logger.warning(f"⚠️ 使用 placeholder email: {email}")
    return email
```

## 🔐 關於 OBO (On-Behalf-Of) Flow

### 什麼時候需要 OBO？

**OBO 用於**：
- Backend service 需要**代表用戶**調用另一個 API
- 交換 token（從一個 API 的 token 換成另一個 API 的 token）

**在 Bot 的情況**：
```
用戶 → Teams → Bot Framework → Bot App
                     ↓
                 Bot 已有用戶的 token
                     ↓
         可以直接調用 Graph API（不需要 OBO）
```

**需要 OBO 的場景**：
```
用戶 → Teams → Bot App → Backend Service → 另一個 API
                              ↓
                    Backend Service 需要代表用戶
                    調用 API，但沒有用戶 token
                              ↓
                        使用 OBO 交換 token
```

### Bot Framework 中的 Token 流程

```
┌─────────────────────────────────────────────────────────┐
│ 1. 用戶在 Teams 中點擊「登入」                            │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Bot Framework 觸發 OAuth2 Flow                        │
│    → 重導向到 Azure AD 登入頁面                           │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│ 3. 用戶登入並授權                                         │
│    → Azure AD 返回 authorization code                    │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│ 4. Bot Framework 用 code 交換 access token              │
│    → 這就是**用戶的 token**（不是 Bot 的 token）          │
└─────────────────────┬───────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────┐
│ 5. Bot 收到 TokenResponse                                │
│    → token_response.token = 用戶的 Azure AD access token │
│    → 此 token 可以**直接**調用 Graph API                 │
│    → **不需要 OBO**，因為這已經是用戶的 token             │
└─────────────────────────────────────────────────────────┘
```

### 總結：Bot 不需要 OBO

**原因**：
1. Bot Framework 的 OAuth Prompt 已經取得**用戶的 access token**
2. 這個 token 可以直接用於調用 Microsoft Graph
3. OBO 是用於 service-to-service，但 Bot 直接持有用戶 token

**OBO 適用場景**：
```python
# 錯誤理解：Bot 需要 OBO
❌ User Token → Bot Token → Graph API (不需要)

# 正確流程：Bot 直接用用戶 token
✅ User Token → Graph API (直接使用)

# OBO 適用場景：Backend service 沒有用戶 token
✅ User Token (Frontend) → Bot Token (Bot) →
   Backend Service 用 Bot Token 透過 OBO 換用戶 Token → Graph API
```

## 📝 完整實作建議

### 步驟 1: 建立 Email 取得工具模組

```python
# app/utils/email_extractor.py
import jwt
import logging
from typing import Optional
from botbuilder.core import TurnContext
from botbuilder.schema import TokenResponse

logger = logging.getLogger(__name__)

class EmailExtractor:
    """從多個來源取得用戶 email 的工具類別"""

    @staticmethod
    def from_token(access_token: str) -> Optional[str]:
        """從 JWT Token 解碼取得 email"""
        try:
            decoded = jwt.decode(
                access_token,
                options={"verify_signature": False}
            )

            # 按優先級嘗試多個 claim
            email = (
                decoded.get("email") or
                decoded.get("preferred_username") or
                decoded.get("upn") or
                decoded.get("unique_name")
            )

            if email and "@" in email:
                logger.debug(f"從 token 取得 email: {email}")
                return email

        except Exception as e:
            logger.debug(f"Token 解碼失敗: {e}")

        return None

    @staticmethod
    def from_activity(turn_context: TurnContext) -> Optional[str]:
        """從 Activity 的 channel data 取得 email"""
        try:
            activity = turn_context.activity

            # 檢查 from 屬性
            if hasattr(activity.from_property, "properties"):
                props = activity.from_property.properties
                if "email" in props:
                    return props["email"]

            # 檢查 channel data
            if activity.channel_data:
                if isinstance(activity.channel_data, dict):
                    upn = activity.channel_data.get("userPrincipalName")
                    if upn and "@" in upn:
                        return upn

        except Exception as e:
            logger.debug(f"從 activity 取得 email 失敗: {e}")

        return None

    @staticmethod
    async def from_graph_api(access_token: str) -> Optional[str]:
        """從 Microsoft Graph API 取得 email"""
        import httpx

        try:
            url = "https://graph.microsoft.com/v1.0/me"
            headers = {"Authorization": f"Bearer {access_token}"}

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=headers,
                    timeout=5.0
                )

                if response.status_code == 200:
                    profile = response.json()
                    email = (
                        profile.get("mail") or
                        profile.get("userPrincipalName")
                    )
                    if email:
                        logger.debug(f"從 Graph API 取得 email: {email}")
                        return email
                else:
                    logger.warning(
                        f"Graph API 返回 {response.status_code}: "
                        f"{response.text[:100]}"
                    )

        except Exception as e:
            logger.warning(f"Graph API 調用失敗: {e}")

        return None

    @staticmethod
    async def get_email(
        turn_context: TurnContext,
        token_response: TokenResponse,
        fallback_name: str = "User"
    ) -> str:
        """
        混合策略取得用戶 email

        優先級：Token → Activity → Graph API → Placeholder
        """
        # 1. 從 Token 取得（最快）
        email = EmailExtractor.from_token(token_response.token)
        if email:
            logger.info(f"✅ Email 來源: JWT Token ({email})")
            return email

        # 2. 從 Activity 取得（次快）
        email = EmailExtractor.from_activity(turn_context)
        if email:
            logger.info(f"✅ Email 來源: Activity Channel Data ({email})")
            return email

        # 3. 從 Graph API 取得（最慢但最完整）
        email = await EmailExtractor.from_graph_api(token_response.token)
        if email:
            logger.info(f"✅ Email 來源: Graph API ({email})")
            return email

        # 4. Placeholder（最後備案）
        email = f"{fallback_name}@example.com"
        logger.warning(f"⚠️ 使用 placeholder email: {email}")
        return email
```

### 步驟 2: 在 Bot 中使用

```python
# bot/handlers/bot.py
from app.utils.email_extractor import EmailExtractor

class MyBot(ActivityHandler):
    async def _run_dialog(self, turn_context: TurnContext):
        # ... existing code ...

        elif result.status == DialogTurnStatus.Complete:
            # SSO completed
            token_response = result.result
            if token_response and token_response.token:
                user_id = turn_context.activity.from_property.id
                name = turn_context.activity.from_property.name or "User"

                # 使用 EmailExtractor（混合策略）
                email = await EmailExtractor.get_email(
                    turn_context,
                    token_response,
                    fallback_name=name
                )

                # Create Session
                session = UserSession(user_id, email, name)
                self.user_sessions[user_id] = session

                await turn_context.send_activity(f"登入成功！歡迎 {name} ({email})")
                # ...
```

## 🧪 測試與驗證

### 測試 Token Claims

```python
# 在開發環境中加入 debug 代碼
import jwt

token = token_response.token
decoded = jwt.decode(token, options={"verify_signature": False})

print("Token Claims:")
for key, value in decoded.items():
    print(f"  {key}: {value}")

# 檢查是否包含 email
if "email" in decoded:
    print(f"✅ Token 包含 email: {decoded['email']}")
else:
    print(f"⚠️ Token 不包含 email")
    print(f"   可用的 claims: {list(decoded.keys())}")
```

### 需要的 Scopes

確保 Azure AD OAuth Connection 包含正確的 scopes：

```
email profile openid User.Read
```

- `email` - 確保 token 包含 email claim
- `profile` - 包含 name, preferred_username 等
- `openid` - OpenID Connect 基本資訊
- `User.Read` - 允許調用 Graph API（備用方案）

## 📊 性能比較

| 方法 | 延遲 | API 配額 | 可靠性 | 推薦 |
|------|------|---------|--------|------|
| JWT 解碼 | < 1ms | 無消耗 | ⭐⭐⭐⭐⭐ | ✅ 優先 |
| Activity Data | < 1ms | 無消耗 | ⭐⭐⭐ | ✅ 次選 |
| Graph API | 200-500ms | 消耗配額 | ⭐⭐⭐⭐ | ⚠️ 備用 |
| Placeholder | < 1ms | 無消耗 | ⭐ | ❌ 最後 |

## 🎯 結論

1. **不需要 OBO**：Bot Framework 已提供用戶的 access token
2. **最佳方案**：從 JWT Token 解碼取得 email（最快、最可靠）
3. **備用方案**：Activity Data → Graph API → Placeholder
4. **混合策略**：使用 waterfall 方式，依序嘗試

---

**總結**：您的質疑完全正確！我之前的建議（直接用 Graph API）不是最優解。應該優先從 JWT Token 解碼取得 email，這樣最快、最省資源，也不需要 OBO flow。
