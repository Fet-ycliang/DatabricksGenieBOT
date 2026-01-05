# Graph API 快速參考

## 三種取得使用者資訊的方法

### 方法 1: OAuth + Graph API（推薦，最完整）

**適用情境**：需要完整使用者資訊，包括 email、OpenID、UPN 等

```python
from graph_service import GraphService

graph_service = GraphService("GraphConnection")

# 取得完整使用者資訊
user_info = await graph_service.get_user_email_and_id(turn_context)

# 回傳資料
{
    'email': 'user@company.com',
    'id': '12345678-1234-1234-1234-123456789abc',  # AAD Object ID (OpenID)
    'name': 'John Doe',
    'upn': 'user@company.com',
    'given_name': 'John',
    'surname': 'Doe'
}
```

**需要**：
- Azure Portal 中設定 OAuth Connection
- 環境變數：`ENABLE_GRAPH_API_AUTO_LOGIN=True`, `OAUTH_CONNECTION_NAME=GraphConnection`
- API 權限：`openid`, `email`, `profile`, `User.Read`

---

### 方法 2: Teams Channel Data（無需 OAuth）

**適用情境**：只需要基本資訊，不想設定 OAuth

```python
from graph_service import get_teams_user_info

# 直接從 Teams 提供的資料取得
user_info = await get_teams_user_info(turn_context)

# 回傳資料
{
    'id': '29:1234567890abcdef',  # Teams User ID
    'name': 'John Doe',
    'aad_object_id': '12345678-1234-1234-1234-123456789abc',  # OpenID
    'email': 'user@company.com'  # 可能為 None
}
```

**需要**：無特殊設定，直接可用

**限制**：
- 不是所有情境都會提供完整資訊
- email 可能為 None
- 依賴 Teams 提供的資料

---

### 方法 3: 手動輸入（Fallback）

**適用情境**：當前兩種方法都失敗時

```python
# Bot 會提示使用者輸入 email
await turn_context.send_activity("請輸入您的 email...")

# 使用者輸入後
session = await _create_session_with_manual_email(turn_context, email)
```

**需要**：無，這是最後的 fallback

---

## 實際使用流程

在 [app.py](app.py#L143) 中的 `get_or_create_user_session()` 方法會按以下順序嘗試：

```
1. 檢查是否已有 session → 直接使用
   ↓ 沒有 session
   
2. 嘗試 Graph API (如果啟用) → 成功則建立 session
   ↓ 失敗或未啟用
   
3. 嘗試 Teams Channel Data → 成功則建立 session
   ↓ 失敗
   
4. 要求使用者手動輸入 email → 建立 session
```

---

## 如何取得 OpenID？

OpenID 就是 **Azure AD Object ID (AAD Object ID)**

### 從 Graph API 取得：

```python
user_info = await graph_service.get_user_email_and_id(turn_context)
open_id = user_info['id']  # 這就是 OpenID
```

### 從 Teams Channel Data 取得：

```python
user_info = await get_teams_user_info(turn_context)
open_id = user_info['aad_object_id']  # 這就是 OpenID
```

### 從 UserSession 取得：

```python
session = await get_or_create_user_session(turn_context)
open_id = session.aad_object_id  # 儲存在 session 中
```

---

## 常見 API 呼叫

### 取得使用者個人資料

```python
graph_service = GraphService()

# 1. 取得 token
token_response = await graph_service.get_user_token(turn_context)

# 2. 使用 token 呼叫 Graph API
user_profile = await graph_service.get_user_profile(token_response.token)

# 回傳完整個人資料
{
    'id': '...',                    # AAD Object ID
    'displayName': 'John Doe',
    'mail': 'john@company.com',
    'userPrincipalName': 'john@company.com',
    'givenName': 'John',
    'surname': 'Doe',
    'jobTitle': 'Software Engineer',
    'officeLocation': 'Building 42',
    'mobilePhone': '+1234567890',
    # ... 更多欄位
}
```

### 登出使用者

```python
graph_service = GraphService()
success = await graph_service.sign_out_user(turn_context)
```

### 提示登入

```python
graph_service = GraphService()
await graph_service.prompt_for_sign_in(turn_context)
```

---

## UserSession 資料結構

```python
class UserSession:
    user_id: str              # Teams 使用者 ID
    email: str                # 使用者 email
    name: str                 # 使用者名稱
    conversation_id: str      # Genie 對話 ID
    aad_object_id: str        # AAD Object ID (OpenID) ← 新增
    upn: str                  # User Principal Name ← 新增
    created_at: datetime
    last_activity: datetime
    is_authenticated: bool
    user_context: dict
```

---

## 測試

執行測試腳本：

```bash
python test_graph_api.py
```

這會檢查：
- ✅ 環境變數設定
- ✅ Teams 資料提取功能
- ✅ 設定建議

---

## 除錯

### 檢查 Log

在應用程式日誌中搜尋：

```
"成功取得使用者 token"                    → OAuth 正常
"成功取得使用者資料"                       → Graph API 正常
"透過 Graph API 自動建立使用者工作階段"   → 自動登入成功
"從 Teams channel data 建立使用者工作階段" → 使用 fallback
"無法透過 Graph API 取得使用者資訊"       → Graph API 失敗
```

### 常見問題

❌ **"無法取得使用者 token"**
- 檢查 OAuth Connection 是否正確設定
- 檢查 `OAUTH_CONNECTION_NAME` 是否正確
- 檢查 API 權限是否已授予

❌ **"Graph API 錯誤: 401"**
- Token 可能過期或無效
- 檢查 Bot 的 Client ID 和 Secret

❌ **"AAD Object ID 為 None"**
- Teams 未提供此資訊
- 需要使用 Graph API OAuth 方法

---

## 進階：自訂 Graph API 呼叫

### 取得使用者照片

```python
async def get_user_photo(token: str) -> bytes:
    headers = {'Authorization': f'Bearer {token}'}
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://graph.microsoft.com/v1.0/me/photo/$value",
            headers=headers
        ) as response:
            if response.status == 200:
                return await response.read()
```

### 取得使用者的管理者

```python
async def get_user_manager(token: str) -> dict:
    headers = {'Authorization': f'Bearer {token}'}
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://graph.microsoft.com/v1.0/me/manager",
            headers=headers
        ) as response:
            if response.status == 200:
                return await response.json()
```

---

## 相關檔案

- [graph_service.py](graph_service.py) - Graph API 整合程式碼
- [app.py](app.py) - 主要 Bot 邏輯，包含自動登入流程
- [config.py](config.py) - 環境變數設定
- [user_session.py](user_session.py) - UserSession 類別定義
- [GRAPH_API_SETUP.md](GRAPH_API_SETUP.md) - 完整設定指南
- [test_graph_api.py](test_graph_api.py) - 測試腳本
