# 透過 Graph API 取得使用者 Email 和 OpenID 設定指南

本文件說明如何設定 Microsoft Graph API，以便在 Teams Bot 中自動取得使用者的 email 和 OpenID (Azure AD Object ID)。

## 功能說明

啟用 Graph API 整合後，Bot 可以：
- ✅ 自動取得使用者的 email（無需手動輸入）
- ✅ 取得使用者的 Azure AD Object ID (OpenID)
- ✅ 取得使用者的 Display Name 和 User Principal Name (UPN)
- ✅ 提供更好的使用者體驗（無需額外登入步驟）

## Azure Portal 設定步驟

### 步驟 1: 在 Azure Portal 設定 OAuth 連線

1. 登入 [Azure Portal](https://portal.azure.com)

2. 導航至你的 **Bot Channels Registration** 或 **Azure Bot**

3. 在左側選單中，選擇 **Configuration** → **Add OAuth Connection Settings**

4. 填寫以下資訊：
   - **Name**: `GraphConnection` (或自訂名稱，需與環境變數一致)
   - **Service Provider**: 選擇 `Azure Active Directory v2`
   - **Client ID**: 你的 Bot 的 Application ID (從 App Registration 取得)
   - **Client Secret**: 你的 Bot 的 Client Secret (從 App Registration 取得)
   - **Token Exchange URL**: 留空
   - **Tenant ID**: 你的 Azure AD Tenant ID
   - **Scopes**: 輸入以下範圍（用空格分隔）：
     ```
     openid email profile User.Read
     ```

5. 按下 **Save** 儲存設定

### 步驟 2: 設定 API 權限

1. 導航至 **Azure Active Directory** → **App registrations**

2. 找到你的 Bot 應用程式並點擊進入

3. 選擇左側的 **API permissions**

4. 確認已新增以下 **Delegated permissions**：
   - ✅ `openid`
   - ✅ `email`  
   - ✅ `profile`
   - ✅ `User.Read`

5. 如果缺少任何權限，點擊 **Add a permission** → **Microsoft Graph** → **Delegated permissions** 新增

6. 新增完權限後，點擊 **Grant admin consent for [Your Organization]** 授予管理員同意

### 步驟 3: 設定環境變數

在你的部署環境（Azure App Service、本地 `.env` 檔案等）中，新增以下環境變數：

```env
# 啟用 Graph API 自動登入
ENABLE_GRAPH_API_AUTO_LOGIN=True

# OAuth 連線名稱（必須與 Azure Portal 中設定的名稱一致）
OAUTH_CONNECTION_NAME=GraphConnection
```

### 步驟 4: 更新 requirements.txt

確認 `requirements.txt` 包含以下套件：

```txt
aiohttp>=3.8.0
```

（此套件應該已經在專案中）

## 如何測試

### 測試 1: 在 Teams 中測試

1. 重新部署你的 Bot 應用程式

2. 在 Teams 中開啟 Bot 對話

3. 第一次使用時，Bot 可能會顯示 **Sign In** 按鈕要求你登入

4. 點擊 **Sign In** 並完成 OAuth 登入流程

5. 登入成功後，Bot 會自動取得你的 email 和其他資訊，無需手動輸入

### 測試 2: 檢查 Logs

在應用程式日誌中，你應該會看到類似以下的訊息：

```
INFO: 成功取得使用者 token
INFO: 成功取得使用者資料: user@company.com
INFO: 透過 Graph API 自動建立使用者工作階段: John Doe (user@company.com), AAD ID: 12345678-1234-1234-1234-123456789abc
```

## 程式碼說明

### graph_service.py

這個新檔案包含以下主要函式：

- **`get_user_token()`**: 取得 OAuth access token
- **`get_user_profile()`**: 使用 token 呼叫 Graph API 取得使用者資料
- **`get_user_email_and_id()`**: 整合函式，取得 email 和 OpenID
- **`get_teams_user_info()`**: 從 Teams channel data 取得基本資訊（不需要 OAuth）

### 資料結構

取得的使用者資訊包含：

```python
{
    'email': 'user@company.com',          # 使用者 email
    'id': '12345...',                     # Azure AD Object ID (OpenID)
    'name': 'John Doe',                   # 顯示名稱
    'upn': 'user@company.com',            # User Principal Name
    'given_name': 'John',                 # 名字
    'surname': 'Doe'                      # 姓氏
}
```

### UserSession 更新

`UserSession` 類別新增了以下屬性：

```python
session.aad_object_id  # Azure AD Object ID (OpenID)
session.upn            # User Principal Name
```

## Fallback 機制

如果 Graph API 呼叫失敗，Bot 會：

1. **第一層**: 嘗試從 Teams channel data 取得基本資訊
2. **第二層**: 要求使用者手動輸入 email（現有流程）

這確保了即使 OAuth 設定有問題，Bot 仍然可以正常運作。

## 停用 Graph API 自動登入

如果你想回到手動輸入 email 的模式，只需設定：

```env
ENABLE_GRAPH_API_AUTO_LOGIN=False
```

或直接移除該環境變數。

## 常見問題

### Q: 為什麼需要 OAuth 連線？

A: Microsoft Graph API 需要使用者授權才能存取個人資訊。OAuth 連線提供了安全的授權機制。

### Q: 使用者每次都需要登入嗎？

A: 不需要。Token 會被快取，通常只需要在第一次使用時登入一次。

### Q: 如何取得 AAD Object ID？

A: AAD Object ID 會儲存在 `session.aad_object_id` 中，這就是使用者的 OpenID。

### Q: 如果不想使用 OAuth 怎麼辦？

A: 可以使用 `get_teams_user_info()` 函式，它不需要 OAuth token，直接從 Teams 提供的資訊中提取。但這種方式可能無法在所有情況下取得完整資訊。

## 安全性考量

- ✅ OAuth token 不會被儲存在資料庫或日誌中
- ✅ 使用 HTTPS 加密所有 API 呼叫
- ✅ 只請求必要的最小權限（openid、email、User.Read）
- ✅ Token 由 Bot Framework 自動管理和更新

## 相關文件

- [Bot Framework Authentication](https://learn.microsoft.com/en-us/azure/bot-service/bot-builder-authentication)
- [Microsoft Graph API - User](https://learn.microsoft.com/en-us/graph/api/user-get)
- [OAuth 2.0 in Azure Bot Service](https://learn.microsoft.com/en-us/azure/bot-service/bot-builder-concept-authentication)
