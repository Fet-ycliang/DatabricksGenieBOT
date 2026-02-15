# Teams SSO 功能狀態與修復指南

**日期**：2026-02-16
**狀態**：✅ 已修復 - 使用混合策略取得真實 email

## 🎉 最新更新（2026-02-16）

**已實施的解決方案**：

1. **建立 EmailExtractor 工具模組** (`app/utils/email_extractor.py`)
   - ✅ 混合策略：JWT Token → Activity → Graph API → Placeholder
   - ✅ 優先使用 JWT 解碼（< 1ms，最快）
   - ✅ Graph API 作為備用方案（200-500ms）
   - ✅ 完整錯誤處理和日誌記錄

2. **整合到 Bot Handler** (`bot/handlers/bot.py`)
   - ✅ SSO 完成後自動使用 EmailExtractor.get_email()
   - ✅ 不再使用 placeholder email
   - ✅ 支援透過參數控制是否調用 Graph API

3. **測試驗證**
   - ✅ 所有 41 個單元測試通過
   - ✅ 沒有破壞現有功能

**效能提升**：
- JWT Token 解碼：< 1ms（最快）
- 避免不必要的 Graph API 調用（節省 200-500ms）
- 優雅降級：各層級都有 fallback 機制

## 📋 當前狀態

### ✅ 可用的組件

1. **SSO Dialog**（`bot/dialogs/sso_dialog.py`）
   - ✅ 標準 Bot Framework OAuth 流程
   - ✅ Azure AD 認證
   - ✅ Token 管理

2. **GraphService**（`app/services/graph.py`）
   - ✅ Microsoft Graph API 客戶端
   - ✅ 用戶資料查詢功能
   - ✅ Profile Card 生成

3. **Bot 整合**（`bot/handlers/bot.py`）
   - ✅ 自動觸發 SSO（無 session 時）
   - ✅ Token Response 處理
   - ✅ 使用混合策略取得真實 email（EmailExtractor）

4. **EmailExtractor**（`app/utils/email_extractor.py`）
   - ✅ JWT Token 解碼（優先）
   - ✅ Activity Channel Data 提取
   - ✅ Graph API 備用調用
   - ✅ Placeholder 最後備案

### ✅ 已解決的問題

**問題**：~~SSO 成功後，使用 placeholder email 而非真實 email~~
- ✅ **已修復**：現在使用 EmailExtractor 混合策略
- ✅ 優先從 JWT Token 解碼取得 email（< 1ms）
- ✅ 備用方案：Activity → Graph API → Placeholder
- 實施位置：`bot/handlers/bot.py` 第 202-207 行
- 相關模組：`app/utils/email_extractor.py`

## 🔧 修復方法

### 選項 1：快速修復（推薦）⚡

**修改檔案**：`bot/handlers/bot.py`

**找到這段代碼**（第 194-208 行）：

```python
elif result.status == DialogTurnStatus.Complete:
    # SSO completed
    token_response = result.result
    if token_response and token_response.token:
        user_id = turn_context.activity.from_property.id

        # Create user session from token
        name = turn_context.activity.from_property.name or "User"
        # Use placeholder email (Graph API integration removed)
        email = f"{name}@example.com"

        # Create Session
        session = UserSession(user_id, email, name)
```

**替換為**：

```python
elif result.status == DialogTurnStatus.Complete:
    # SSO completed
    token_response = result.result
    if token_response and token_response.token:
        user_id = turn_context.activity.from_property.id

        # 取得使用者真實 email（使用 Graph API）
        name = turn_context.activity.from_property.name or "User"
        email = f"{name}@example.com"  # 預設值

        try:
            # 導入 GraphService
            from app.services.graph import GraphService
            graph_service = GraphService(self.config)

            # 使用 token 取得用戶資料
            profile = await graph_service.get_user_profile(token_response.token)

            # 優先使用 mail，備用 userPrincipalName
            if profile:
                email = profile.get("mail") or profile.get("userPrincipalName") or email
                # 可選：更新 displayName
                if profile.get("displayName"):
                    name = profile.get("displayName")

            logger.info(f"成功取得使用者資料: {email}")
        except Exception as ex:
            logger.warning(f"無法取得 Graph 資料，使用預設 email: {ex}")
            # 繼續使用 placeholder email

        # Create Session
        session = UserSession(user_id, email, name)
```

**優點**：
- ✅ 5 分鐘即可完成
- ✅ 取得真實 email
- ✅ 有錯誤處理（fallback 到 placeholder）
- ✅ 不需要額外配置

### 選項 2：完整重構（較複雜）🔨

如果您想要更完整的實作，可以：

1. **建立專用的 SSO 處理器**

```python
# bot/handlers/sso_handler.py
from app.services.graph import GraphService

class SSOHandler:
    def __init__(self, config, graph_service: GraphService):
        self.config = config
        self.graph_service = graph_service

    async def process_token_response(
        self,
        turn_context: TurnContext,
        token_response: TokenResponse
    ) -> UserSession:
        """處理 SSO token 並建立 user session"""
        user_id = turn_context.activity.from_property.id
        name = turn_context.activity.from_property.name or "User"

        # 取得真實 email
        email = await self._get_user_email(token_response.token, name)

        return UserSession(user_id, email, name)

    async def _get_user_email(self, access_token: str, default_name: str) -> str:
        """從 Graph API 取得用戶 email"""
        try:
            profile = await self.graph_service.get_user_profile(access_token)
            return profile.get("mail") or profile.get("userPrincipalName") or f"{default_name}@example.com"
        except Exception as ex:
            logger.error(f"Graph API 調用失敗: {ex}")
            return f"{default_name}@example.com"
```

2. **在 Bot 中使用**

```python
# bot/handlers/bot.py
from bot.handlers.sso_handler import SSOHandler

class MyBot(ActivityHandler):
    def __init__(self, ...):
        # ...
        self.sso_handler = SSOHandler(config, GraphService(config))

    async def _run_dialog(self, turn_context: TurnContext):
        # ...
        elif result.status == DialogTurnStatus.Complete:
            token_response = result.result
            if token_response and token_response.token:
                # 使用 SSO Handler
                session = await self.sso_handler.process_token_response(
                    turn_context,
                    token_response
                )
                self.user_sessions[session.user_id] = session
                # ...
```

## 🔐 必要的 Azure 配置

### 1. Bot Service OAuth Connection

在 Azure Portal：
1. 前往 **Azure Bot Service** → **Configuration**
2. 找到 **OAuth Connection Settings**
3. 確認已設定：
   - **Name**: `GraphConnection`（或您的 `OAUTH_CONNECTION_NAME`）
   - **Service Provider**: `Azure Active Directory v2`
   - **Client ID**: 您的 App ID
   - **Client Secret**: 您的 App Secret
   - **Scopes**: `User.Read User.ReadBasic.All email profile openid`

### 2. 環境變數

確認 `.env` 包含：

```bash
# Bot Framework
APP_ID=your-app-id
APP_PASSWORD=your-app-password
APP_TENANTID=your-tenant-id

# OAuth Connection（必須與 Bot Service 中的名稱一致）
OAUTH_CONNECTION_NAME=GraphConnection
```

### 3. Azure AD 權限

在 **Azure AD App Registration** → **API Permissions**：
- ✅ `User.Read`
- ✅ `User.ReadBasic.All`
- ✅ `email`
- ✅ `profile`
- ✅ `openid`

**重要**：點擊 **Grant admin consent** 授予權限！

## ✅ 測試 SSO 功能

### 1. 本地測試（Bot Emulator）

```bash
# 設定環境變數
export APP_ID=""
export APP_PASSWORD=""

# 啟動 Bot
uv run uvicorn app.main:app --port 8000
```

**預期行為**：
- 無 APP_ID/PASSWORD → 跳過 SSO，顯示未認證歡迎訊息
- 可以直接使用 `/setuser` 命令設定 email

### 2. Teams 測試

1. 部署到 Azure Web App
2. 在 Teams 中開啟 Bot
3. 首次訊息觸發 SSO 登入
4. 登入後檢查回應中的 email

**驗證方法**：
```bash
# 查看日誌
az webapp log tail --name your-app-name --resource-group your-rg

# 應該看到
# 成功取得使用者資料: user@company.com
```

### 3. 檢查 Token

在 Bot 中加入調試：

```python
logger.info(f"Token length: {len(token_response.token)}")
logger.info(f"Token prefix: {token_response.token[:20]}...")
```

有效的 Azure AD token 應該：
- 長度 > 500 字元
- 以 `eyJ` 開頭（JWT 格式）

## 📊 常見問題

### Q1: SSO 登入彈窗不出現

**檢查**：
- ✅ `OAUTH_CONNECTION_NAME` 是否正確
- ✅ Bot Service 中的 OAuth Connection 是否測試成功
- ✅ Azure AD Redirect URI 是否包含 `https://token.botframework.com/.auth/web/redirect`

### Q2: Token 取得成功但 Graph API 失敗

**檢查**：
- ✅ API 權限是否已授予（admin consent）
- ✅ Scopes 是否包含 `User.Read`
- ✅ Token 是否已過期（SSO Dialog 有 5 分鐘超時）

**調試**：
```python
# 解碼 JWT token 檢查 scopes
import jwt
decoded = jwt.decode(token_response.token, options={"verify_signature": False})
print(decoded.get("scp"))  # 應該包含 User.Read
```

### Q3: Email 仍然是 placeholder

**可能原因**：
1. Graph API 調用失敗（檢查日誌）
2. 用戶沒有 `mail` 屬性（使用 `userPrincipalName`）
3. Token 缺少必要的 scopes

**解決方法**：
```python
# 更詳細的錯誤處理
try:
    profile = await graph_service.get_user_profile(token_response.token)
    logger.info(f"Graph API 回應: {profile}")

    if not profile:
        logger.error("Graph API 返回空結果")
    elif "mail" not in profile and "userPrincipalName" not in profile:
        logger.error(f"用戶資料缺少 email: {list(profile.keys())}")
except httpx.HTTPError as ex:
    logger.error(f"Graph API HTTP 錯誤: {ex.response.status_code} - {ex.response.text}")
```

## 📈 效能考量

### Graph API 調用優化

**問題**：每次 SSO 都調用 Graph API

**建議**：
1. **快取用戶資料**（TTL: 1 小時）
   ```python
   # app/utils/user_cache.py
   from datetime import datetime, timedelta

   class UserCache:
       def __init__(self, ttl_hours: int = 1):
           self.cache = {}
           self.ttl = timedelta(hours=ttl_hours)

       def get(self, user_id: str):
           if user_id in self.cache:
               data, timestamp = self.cache[user_id]
               if datetime.now() - timestamp < self.ttl:
                   return data
           return None

       def set(self, user_id: str, data: dict):
           self.cache[user_id] = (data, datetime.now())
   ```

2. **批次查詢**（如果需要多個用戶）
   ```python
   # 使用 Microsoft Graph batch API
   # https://graph.microsoft.com/v1.0/$batch
   ```

## 🎯 建議實作順序

1. **立即修復**（5 分鐘）⭐⭐⭐⭐⭐
   - 使用「選項 1：快速修復」
   - 恢復 Graph API 調用
   - 測試取得真實 email

2. **短期改善**（1-2 天）⭐⭐⭐⭐
   - 加入錯誤處理和日誌
   - 建立單元測試
   - 文檔化 SSO 流程

3. **中期優化**（1 週）⭐⭐⭐
   - 實作用戶資料快取
   - 重構為 SSOHandler
   - 加入 Token 刷新機制

## 📚 相關文檔

- [Azure AD 設定指南](deployment/AZURE_AD_SETUP.md)
- [GraphService API](../app/services/graph.py)
- [SSODialog 實作](../bot/dialogs/sso_dialog.py)
- [部署檢查清單](deployment/DEPLOYMENT_CHECKLIST.md)

---

**總結**：SSO 功能在代碼層面是完整且可用的，只需要 5 分鐘的代碼修改即可恢復 Graph API 調用，取得真實的用戶 email。
