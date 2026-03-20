# Microsoft 365 Agent Framework 配置示例

## .env 文件示例

```env
# ==========================================
# Microsoft 365 Agent Framework 配置
# ==========================================

# Azure AD 租戶信息
AZURE_TENANT_ID=12345678-1234-1234-1234-123456789012

# 應用註冊信息
AZURE_CLIENT_ID=87654321-4321-4321-4321-210987654321
AZURE_CLIENT_SECRET=your_client_secret_here

# Microsoft Graph 設置
GRAPH_SCOPES=https://graph.microsoft.com/.default

# ==========================================
# 現有配置（保持不變）
# ==========================================

# Bot Framework
APP_ID=your_bot_app_id
APP_PASSWORD=your_bot_app_password
APP_TYPE=SingleTenant

# Databricks
DATABRICKS_SPACE_ID=your_space_id
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=your_databricks_token

# Teams
CONNECTION_NAME=Your-OAuth-Connection-Name

# 其他配置
PORT=3978
```

## Azure AD 應用註冊步驟

### 1. 在 Azure Portal 中建立應用註冊

1. 前往 [Azure Portal](https://portal.azure.com)
2. 選擇 Azure Active Directory
3. 選擇 "應用註冊"
4. 點擊 "新建註冊"
5. 填入應用信息：
   - 名稱: `Databricks Genie Bot M365 Agent`
   - 支持的帳戶類型: 根據需要選擇
   - 重定向 URI: `http://localhost:3978/auth/callback` （用於本地測試）

### 2. 配置應用權限

1. 在應用中，選擇 "API 權限"
2. 點擊 "添加權限"
3. 選擇 "Microsoft Graph"
4. 選擇 "委派權限"
5. 添加以下權限：

#### 郵件權限
- `Mail.Read`
- `Mail.Send`

#### 日曆權限
- `Calendars.Read`
- `Calendars.ReadWrite`

#### 檔案權限
- `Files.Read.All`
- `Files.ReadWrite.All`

#### Teams 權限
- `Team.ReadBasic.All`
- `Chat.ReadWrite`
- `ChannelMessage.Read.All`

#### 用戶信息
- `User.Read`
- `User.ReadBasic.All`

6. 點擊 "授予管理員同意"

### 3. 建立客戶端密碼

1. 在應用中，選擇 "證書和密碼"
2. 點擊 "新建客戶端密碼"
3. 輸入描述和過期時間
4. 複製密碼值到 `.env` 文件中的 `AZURE_CLIENT_SECRET`

### 4. 獲取應用 ID 和租戶 ID

1. 在應用的 "概述" 頁面上找到：
   - 應用（客戶端）ID -> 複製到 `AZURE_CLIENT_ID`
   - 目錄（租戶）ID -> 複製到 `AZURE_TENANT_ID`

## 本地開發設置

### 安裝依賴項

```bash
# 激活虛擬環境
source env/Scripts/activate  # 在 Windows 上

# 安裝依賴項
pip install -e .
```

### 啟動應用

```bash
# 使用 FastAPI 開發服務器
uv run uvicorn app.main:app --reload --port 8000
```

### 測試 Agent Framework

```bash
# 獲取可用的 skills
curl http://localhost:8000/api/m365/skills

# 獲取使用者上下文
curl "http://localhost:8000/api/m365/context?user_id=me"

# 獲取最近的郵件
curl "http://localhost:8000/api/m365/mail/recent?count=5"
```

## 生產部署配置

### Azure App Service 部署

1. 在 Azure Portal 中建立 App Service
2. 在 Application Settings 中添加環境變數
3. 設置部署憑據並部署應用

### 環境變數配置

在 Azure App Service 中設置：

```
AZURE_TENANT_ID = <your_tenant_id>
AZURE_CLIENT_ID = <your_client_id>
AZURE_CLIENT_SECRET = <your_client_secret>
GRAPH_SCOPES = https://graph.microsoft.com/.default
```

### 更新重定向 URI

在 Azure AD 應用中，更新重定向 URI 為生產應用 URL：

```
https://your-app.azurewebsites.net/auth/callback
```

## 驗證配置

執行以下步驟驗證配置是否正確：

1. **檢查環境變數**
   ```python
   from app.core.config import DefaultConfig
   config = DefaultConfig()
   print(f"Tenant: {config.AZURE_TENANT_ID}")
   ```

2. **測試 Graph 連接**
   ```python
   from app.services.m365_agent import M365AgentService
   from app.core.config import DefaultConfig
   
   config = DefaultConfig()
   service = M365AgentService(config)
   profile = await service.get_user_profile()
   print(profile)
   ```

3. **檢查 API 端點**
   - 訪問 http://localhost:8000/docs（Swagger UI）
   - 測試各個端點

## 常見問題

### 權限問題

如果遇到 "Insufficient privileges" 錯誤：
1. 檢查應用中的 API 權限配置
2. 確保已點擊 "授予管理員同意"
3. 等待數分鐘讓權限生效

### 驗證失敗

如果無法連接到 Microsoft Graph：
1. 檢查 Azure AD 應用 ID 和客戶端密碼
2. 確保應用還未過期
3. 檢查租戶 ID 是否正確

### 超時問題

對於大量數據的操作：
1. 增加請求超時時間
2. 使用分頁返回結果
3. 考慮使用後台任務處理

## 進一步學習

- [Microsoft Graph Python SDK](https://github.com/microsoftgraph/msgraph-sdk-python)
- [Azure AD 開發者指南](https://docs.microsoft.com/azure/active-directory/develop/)
- [Bot Framework 文檔](https://docs.microsoft.com/bot-framework/)
