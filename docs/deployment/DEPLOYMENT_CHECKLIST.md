# Databricks Genie Bot - 部署檢查清單

> **最後更新**：2026 年 2 月 9 日  
> **版本**：1.0.0

---

## 📋 部署前準備清單

### ✅ 第 1 階段：Azure Bot Service 設定

#### 1.1 建立 Azure Bot Service
- [ ] 登入 [Azure Portal](https://portal.azure.com)
- [ ] 搜尋並建立 "Bot Channels Registration" 資源
- [ ] 填寫基本資訊：
  - **Bot handle**：`databricks-genie-bot` (或自選名稱)
  - **Subscription**：選擇目標訂閱
  - **Resource group**：新建或選擇現有
  - **Location**：`East Asia` (建議)

#### 1.2 取得 Bot 認證
部署完成後，前往 **Configuration**：
- [ ] 複製 **Microsoft App ID** → 更新 `.env` 中的 `APP_ID`
- [ ] 建立新的 **Client Secret** → 複製值 → 更新 `.env` 中的 `APP_PASSWORD`
  > ⚠️ **重要**：Secret 只顯示一次，請立即複製並妥善保管

#### 1.3 驗證租戶配置
- [ ] 確認 `APP_TENANTID=bb5ad653-221f-4b94-9c26-f815e04eef40` 正確
- [ ] 確認 `APP_TYPE=SingleTenant` 設定正確

---

### ✅ 第 2 階段：OAuth 和 Microsoft Graph 設定

#### 2.1 建立 Azure AD App Registration
- [ ] Azure Portal → **Azure Active Directory** → **App registrations** → **New registration**
- [ ] **Name**：`DatabricksGenieBOT-OAuth`
- [ ] **Supported account types**：選擇 "Accounts in this organizational directory only"
- [ ] **Redirect URI**：暫時留空
- [ ] 按 **Register**

#### 2.2 配置重定向 URI
- [ ] 進入新建的 App Registration
- [ ] 前往 **Authentication**
- [ ] 在 **Redirect URIs** 中新增：
  ```
  https://token.botframework.com/.auth/web/redirect
  ```
- [ ] 儲存

#### 2.3 建立 Client Secret
- [ ] 前往 **Certificates & secrets**
- [ ] 點擊 **New client secret**
- [ ] **Description**：`DatabricksGenieBOT-Secret`
- [ ] **Expires**：建議 "12 months" 或 "24 months"
- [ ] 複製 **Value** (僅顯示一次)
- [ ] 妥善保管此密鑰

#### 2.4 配置 API 權限
- [ ] 前往 **API permissions**
- [ ] 點擊 **Add a permission**
- [ ] 選擇 **Microsoft Graph**
- [ ] 選擇 **Delegated permissions**
- [ ] 搜尋並勾選：
  - [ ] `User.Read`
  - [ ] `User.ReadBasic.All`
  - [ ] `email`
  - [ ] `profile`
  - [ ] `openid`
- [ ] 點擊 **Add permissions**
- [ ] **Grant admin consent** (如果有權限)

#### 2.5 在 Bot Service 中配置 OAuth Connection
- [ ] 前往 **Azure Bot Service** → **Configuration**
- [ ] 向下滾動到 **OAuth Connection Settings**
- [ ] 點擊 **Add OAuth Connection Settings**
- [ ] 填寫以下資訊：
  | 欄位 | 值 |
  |------|-----|
  | **Name** | `GraphConnection` |
  | **Service Provider** | `Azure Active Directory v2` |
  | **Client ID** | App Registration 的 Application ID |
  | **Client Secret** | App Registration 的 Client Secret |
  | **Tenant** | `common` 或 `bb5ad653-221f-4b94-9c26-f815e04eef40` |
  | **Scopes** | `User.Read User.ReadBasic.All email profile openid` |
  
- [ ] 點擊 **Save**
- [ ] 測試連接（應該看到 "Connection successful"）

---

### ✅ 第 3 階段：環境變數配置

#### 3.1 更新 .env 文件（本地開發）
```dotenv
# Bot Framework 設定 - 必須填寫
APP_ID=<從 Azure Bot Service 取得>
APP_PASSWORD=<從 Azure Bot Service 取得>
APP_TYPE=SingleTenant
APP_TENANTID=bb5ad653-221f-4b94-9c26-f815e04eef40

# Databricks 設定 - 必須填寫
DATABRICKS_SPACE_ID=<您的 Genie Space ID>
DATABRICKS_HOST=<您的 Databricks 實例 URL>
DATABRICKS_TOKEN=<您的 Databricks PAT>

# OAuth 設定
ENABLE_GRAPH_API_AUTO_LOGIN=True
OAUTH_CONNECTION_NAME=GraphConnection

# 應用程式設定
PORT=8000
SAMPLE_QUESTIONS="查詢上個月 Azure Databricks 的用量?;查詢上個月 VM 的用量?;查詢上個月 定價模型 的分配情況"
ADMIN_CONTACT_EMAIL=<支援郵箱>
TIMEZONE=Asia/Taipei

# 回饋功能設定
ENABLE_FEEDBACK_CARDS=True
ENABLE_GENIE_FEEDBACK_API=True

# 日誌記錄設定
VERBOSE_LOGGING=False    # 生產環境建議 False
LOG_FILE=bot_debug.log
```

#### 3.2 在 Azure Web App 中配置環境變數
- [ ] 進入 **Azure App Service**
- [ ] 前往 **Settings** → **Configuration**
- [ ] 點擊 **New application setting** 並新增所有上述環境變數
- [ ] 對於敏感資訊 (APP_PASSWORD, DATABRICKS_TOKEN)，建議使用 **Key Vault** 而不是直接輸入
- [ ] 儲存設定
- [ ] **重啟** App Service 使設定生效

---

### ✅ 第 4 階段：Teams 應用程式套件

#### 4.1 準備 manifest.json
- [ ] 開啟根目錄中的 `manifest.json`
- [ ] 找到所有 `"00000000-0000-0000-0000-000000000000"` 的佔位符
- [ ] 替換為實際的 **Bot App ID**：
  ```json
  "id": "YOUR-BOT-APP-ID-HERE",
  ...
  "botId": "YOUR-BOT-APP-ID-HERE",
  ```
- [ ] 驗證其他信息（組織名稱、URL 等）

#### 4.2 準備圖標文件
Teams 需要兩個 192x192 像素的 PNG 圖標：

- [ ] **outline.png** - 透明背景的黑色/深灰色圖標
- [ ] **color.png** - 彩色圖標

將這兩個檔案放在根目錄或 `/manifest` 文件夾中。

> 📝 **快速建議**：
> - 如果沒有設計工具，可以使用 Databricks 官方圖標或簡單的 Data 符號
> - 確保圖標在小尺寸下清晰可見

#### 4.3 建立 Teams 應用程式套件
- [ ] 建立新文件夾：`teams-app/`
- [ ] 複製以下檔案到 `teams-app/`：
  ```
  teams-app/
  ├── manifest.json
  ├── outline.png
  └── color.png
  ```
- [ ] 使用 7-Zip 或 Windows 內建壓縮功能建立 ZIP：
  ```bash
  # 在 teams-app 文件夾中右鍵 → 傳送至 → 壓縮的資料夾
  # 或使用命令行：
  Compress-Archive -Path teams-app/* -DestinationPath teams-app.zip
  ```
- [ ] 檢查 ZIP 內結構（manifest.json 應該在根層，不是子文件夾）

---

### ✅ 第 5 階段：Azure Web App 部署

#### 5.1 建立 Azure App Service
- [ ] Azure Portal → **Create a resource** → **App Service**
- [ ] 填寫基本資訊：
  - **Name**：`databricks-genie-bot-prod` (或自選)
  - **Publish**：`Code`
  - **Runtime stack**：`Python 3.11`
  - **Operating System**：`Windows` (與 web.config 相容)
  - **Region**：`East Asia`
  - **App Service Plan**：最少 **B1** (基本層)

#### 5.2 部署代碼

**選項 A：使用 Git（推薦快速部署）**
- [ ] App Service → **Deployment Center** → **GitHub**
- [ ] 連接 GitHub 帳戶和倉庫 `DatabricksGenieBOT`
- [ ] 選擇分支：`develop` 或 `main`
- [ ] 儲存 (自動開始部署)
- [ ] 監控 **Deployment logs** 檢查部署進度

**選項 B：使用 Docker**
- [ ] 構建 Docker 映像：
  ```bash
  docker build -t databricks-genie:latest .
  ```
- [ ] 推送到 Azure Container Registry
- [ ] 在 App Service 中配置 Container 映像

**選項 C：手動上傳 ZIP**
- [ ] 本地準備部署套件：
  ```bash
  # 建立虛擬環境並安裝依賴
  python -m venv venv
  .\venv\Scripts\activate
  uv sync
  ```
- [ ] 壓縮應用程式文件（排除 `.venv`, `.git`, `__pycache__` 等）
- [ ] App Service → **Deployment Center** → **Manual deployment** → 上傳 ZIP

#### 5.3 驗證部署
- [ ] 進入 App Service → **Overview**
- [ ] 記下 **Default domain**：`https://your-app-name.azurewebsites.net`
- [ ] 訪問 `https://your-app-name.azurewebsites.net/api/health`
  - 應返回：`{"status": "ok"}`
- [ ] 檢視 **Log stream** 確保沒有錯誤

#### 5.4 更新 Bot Service 設定
- [ ] 進入 **Azure Bot Service** → **Configuration**
- [ ] 在 **Messaging endpoint** 中輸入：
  ```
  https://your-app-name.azurewebsites.net/api/messages
  ```
- [ ] 儲存

---

### ✅ 第 6 階段：測試

#### 6.1 在 Web Chat 中測試
- [ ] Azure Bot Service → **Test in Web Chat**
- [ ] 輸入測試指令：
  - `help` - 應顯示可用指令
  - `info` - 應顯示機器人資訊
  - `whoami` - 應顯示使用者資訊
  - 自然語言查詢：`查詢上個月的用量`

#### 6.2 在 Teams 中測試
- [ ] 在 Teams 中新增應用程式：
  - **Apps** → **Manage your apps** → **Upload a custom app** → 選擇 `teams-app.zip`
- [ ] 應用程式應出現在側邊欄
- [ ] 開啟應用程式並在個人聊天中進行測試
- [ ] 測試在頻道和群組聊天中的使用

#### 6.3 功能測試清單
- [ ] [ ] 基本指令 (`help`, `info`, `whoami`)
- [ ] [ ] 自然語言查詢處理
- [ ] [ ] 圖表生成和顯示
- [ ] [ ] 建議問題的顯示和點擊
- [ ] [ ] 回饋卡片的運作
- [ ] [ ] 錯誤處理和消息提示

---

### ✅ 第 7 階段：監控和安全

#### 7.1 啟用 Application Insights
- [ ] App Service → **Settings** → **Application Insights**
- [ ] 點擊 **Enable Application Insights**
- [ ] 建立新的 Insights 資源或選擇現有
- [ ] 儲存並重啟 App Service

#### 7.2 查看日誌和監控
- [ ] **Log stream** - 實時查看日誌
- [ ] **Application Insights** → **Performance** - 監控應用性能
- [ ] **Alerts** - 設定告警規則

#### 7.3 安全性檢查
- [ ] [ ] HTTPS 已啟用（Azure Web App 預設）
- [ ] [ ] 敏感資訊已從代碼中移除（使用環境變數）
- [ ] [ ] 機器人 App Password 已安全保管
- [ ] [ ] Databricks Token 已安全保管（建議使用 Key Vault）
- [ ] [ ] OAuth Connection 已驗證
- [ ] [ ] 沒有在日誌中暴露敏感資訊

#### 7.4 備份和還原計畫
- [ ] 定期備份 Databricks 配置
- [ ] 文檔記錄 OAuth 連接設定
- [ ] 保存 manifest.json 和 teams-app.zip
- [ ] 建立災難恢復計畫

---

## 🚀 快速參考

### 環境變數映射
```
Azure Bot Service → APP_ID, APP_PASSWORD
Azure AD App Reg → OAUTH_CONNECTION_NAME (GraphConnection)
Databricks → DATABRICKS_SPACE_ID, DATABRICKS_HOST, DATABRICKS_TOKEN
Teams → manifest.json (Bot App ID)
```

### 部署網址
- **Local**：http://localhost:8000
- **Azure Web App**：https://your-app-name.azurewebsites.net
- **Health Check**：{base-url}/api/health
- **Bot Messages**：{base-url}/api/messages

### 聯絡方式
- **支援郵箱**：`ADMIN_CONTACT_EMAIL` (.env)
- **Azure Support**：Azure Portal → Help + support
- **Teams Admin**：Microsoft Teams admin center

---

## 📝 故障排查

### 部署後 Bot 無響應
1. 檢查 **App Service** 是否正在執行
2. 檢查 **Azure Bot Service** 的訊息端點是否正確
3. 查看 **Log stream** 中的錯誤信息
4. 確認所有環境變數都已設定

### OAuth 連接失敗
1. 驗證 **Azure AD App Registration** 的 Client ID 和 Secret
2. 驗證重定向 URI 是否正確
3. 確認 API 權限已授予
4. 在 Bot Service 中重新測試 OAuth Connection

### Teams 應用程式無法上傳
1. 檢查 `manifest.json` 的格式和語法
2. 確保 Bot App ID 已正確填入
3. 驗證 ZIP 文件結構（manifest.json 應在根層）
4. 檢查團隊或組織的上傳政策

---

## ✨ 完成！

所有步驟完成後，您的 Databricks Genie Bot 應該在 Teams 中正常運作。

有任何問題？請查看 [troubleshooting.md](../../troubleshooting.md) 或聯絡 `ADMIN_CONTACT_EMAIL`。
