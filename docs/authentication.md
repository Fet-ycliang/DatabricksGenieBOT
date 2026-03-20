# API 認證指南

## 概述

本專案實作了統一的認證系統，保護所有敏感 API 端點。所有需要訪問受保護資源的請求必須包含有效的認證憑證。

## 認證類型

### 1. Azure AD Token 認證（M365 API）

用於保護 Microsoft 365 Agent Framework API 端點。

**支援的端點**：
- `GET /api/m365/profile` - 取得使用者個人資料
- `GET /api/m365/context` - 取得使用者完整上下文

**認證流程**：

1. 從 Azure AD 取得 access token
2. 在 HTTP 請求中包含 Bearer token
3. 伺服器驗證 token 並返回結果

**範例**：

```bash
# 取得個人資料
curl -H "Authorization: Bearer <your_azure_ad_token>" \
     https://your-bot-url.azurewebsites.net/api/m365/profile
```

**Token 要求**：
- Token 必須來自 Azure AD
- Audience 必須是應用程式的 APP_ID
- Token 不能過期
- Token 簽名必須有效

### 2. Bot Framework 簽名驗證

用於保護 Bot Framework 訊息端點。

**支援的端點**：
- `POST /api/messages` - 接收 Teams 訊息

**注意**：
- Bot Framework Adapter 自動處理簽名驗證
- 無需額外配置

## 實作細節

### 認證中介軟體

位置：`app/core/auth_middleware.py`

提供以下功能：

1. **verify_azure_ad_token(credentials)**
   - 驗證 Azure AD JWT Token
   - 檢查簽名、過期時間、audience
   - 返回解碼後的 token payload

2. **get_current_user(token_payload)**
   - 從 token 中提取用戶資訊
   - 返回 user_id, email, name, tenant_id

3. **verify_bot_framework_signature(authorization)**
   - 驗證 Bot Framework 請求簽名
   - 目前版本僅檢查格式（待完整實作）

### 在 API 端點中使用認證

```python
from fastapi import APIRouter, Depends
from app.core.auth_middleware import get_current_user

router = APIRouter()

@router.get("/protected-endpoint")
async def protected_endpoint(
    current_user: dict = Depends(get_current_user)
):
    """需要認證的端點"""
    return {
        "message": f"Hello, {current_user['email']}!",
        "user_id": current_user['user_id']
    }
```

## 錯誤處理

### 401 Unauthorized

**可能原因**：
- 未提供 Authorization header
- Token 格式無效（不是 Bearer token）
- Token 已過期
- Token 簽名無效
- Token audience 不符

**範例錯誤回應**：

```json
{
  "detail": "Token 已過期"
}
```

### 500 Internal Server Error

**可能原因**：
- 伺服器認證配置錯誤（APP_TENANTID 未設定）
- Azure AD JWKS 端點無法訪問

## 配置

### 必要環境變數

```bash
# Azure Bot Service 配置
APP_ID=<your-app-id>
APP_PASSWORD=<your-app-password>
APP_TENANTID=<your-tenant-id>
```

### Token Audience

Azure AD token 的 audience 必須設定為應用程式的 `APP_ID`。

在 Azure AD 應用註冊中：
1. 進入「API 權限」
2. 確保已授予必要的 Microsoft Graph 權限
3. Token 的 `aud` 欄位會是應用程式的 Client ID

## 開發和測試

### 測試端點

**使用 curl**：

```bash
# 取得 Azure AD token（需要 Azure CLI）
TOKEN=$(az account get-access-token --resource https://graph.microsoft.com --query accessToken -o tsv)

# 調用受保護的 API
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8000/api/m365/profile
```

### 單元測試

位置：`tests/unit/test_auth_middleware.py`

執行測試：

```bash
python tests/unit/test_auth_middleware.py
```

### 模擬認證（僅開發環境）

`auth_middleware.py` 提供 `optional_auth` 依賴用於開發環境：

```python
from app.core.auth_middleware import optional_auth

@router.get("/dev-endpoint")
async def dev_endpoint(user: dict = Depends(optional_auth)):
    """開發端點：可選認證"""
    if user:
        return {"message": f"Authenticated as {user['email']}"}
    else:
        return {"message": "Anonymous access"}
```

⚠️ **警告**：不要在生產環境使用 `optional_auth`！

## 安全性最佳實踐

1. **Token 儲存**
   - 不要將 token 儲存在前端 localStorage
   - 使用 httpOnly cookies 或記憶體儲存
   - 定期更新 token

2. **Token 驗證**
   - 總是驗證 token 簽名
   - 檢查 token 過期時間
   - 驗證 audience 和 issuer

3. **HTTPS**
   - 生產環境必須使用 HTTPS
   - 不要通過 HTTP 傳輸 token

4. **日誌安全**
   - 不要記錄完整的 token
   - 只記錄 token 的前幾個字元用於調試

5. **錯誤訊息**
   - 不要在錯誤訊息中洩漏敏感資訊
   - 使用通用錯誤訊息（如「認證失敗」）

## 故障排除

### Token 驗證失敗

1. **檢查 token 是否過期**：
   ```bash
   # 解碼 JWT token（使用 https://jwt.io/ 或 jwt CLI tool）
   echo $TOKEN | jwt decode -
   ```

2. **檢查 audience**：
   Token 的 `aud` 欄位必須匹配 `APP_ID`

3. **檢查 tenant ID**：
   確保 `APP_TENANTID` 環境變數正確設定

### JWKS 錯誤

如果看到「無法從 Azure AD 取得公鑰」錯誤：

1. 檢查網路連接
2. 確認 tenant ID 正確
3. 檢查 Azure AD 服務狀態

### Bot Framework 簽名驗證

目前 `verify_bot_framework_signature` 僅檢查格式。

完整實作需要：

```python
from botframework.connector.auth import JwtTokenValidation

async def verify_bot_framework_signature(authorization: str):
    claims = await JwtTokenValidation.validate_auth_header(
        authorization,
        credentials_factory,
        channel_service_or_channel_id
    )
    return claims
```

## 未來改進

- [ ] 完整實作 Bot Framework JWT 驗證
- [ ] 加入 API 限流（rate limiting）
- [ ] 實作 token 快取機制
- [ ] 支援 refresh token
- [ ] 加入 OAuth2 implicit flow
- [ ] 整合 Azure Key Vault 儲存密鑰

## 參考資料

- [Azure AD Token 驗證](https://docs.microsoft.com/en-us/azure/active-directory/develop/access-tokens)
- [Bot Framework 認證](https://docs.microsoft.com/en-us/azure/bot-service/bot-builder-authentication)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [PyJWT Documentation](https://pyjwt.readthedocs.io/)
