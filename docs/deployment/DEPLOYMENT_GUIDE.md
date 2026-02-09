# 部署指南 - Databricks Genie Bot 到 Azure Web App

## 目錄
1. [前置需求](#前置需求)
2. [Azure 資源準備](#azure-資源準備)
3. [代碼部署](#代碼部署)
4. [配置驗證](#配置驗證)
5. [Teams 整合](#teams-整合)
6. [測試驗證](#測試驗證)
7. [生產環境設定](#生產環境設定)

---

## 前置需求

### 帳戶和權限
- ✅ Azure 訂閱（有效的信用卡或企業協議）
- ✅ Azure AD 租戶管理員權限
- ✅ GitHub 帳戶（擁有 DatabricksGenieBOT 倉庫的存取權）
- ✅ Teams 管理員權限（用於應用程式發佈）

### 本地工具
```bash
# 必需的工具
- Python 3.11+
- Git
- Azure CLI (可選但推薦)
- Visual Studio Code (推薦)

# 安裝 Azure CLI
# Windows
choco install azure-cli

# 或從網站下載：https://aka.ms/installazurecliwindows
```

### 憑證準備
在開始部署前，請準備好：
- [ ] Databricks Host URL
- [ ] Databricks Space ID
- [ ] Databricks Personal Access Token (PAT)

---

## Azure 資源準備

### 步驟 1：建立 Bot Channels Registration

```bash
# 使用 Azure CLI (可選)
az bot create \
  --name databricks-genie-bot \
  --resource-group your-resource-group \
  --app-type SingleTenant \
  --kind registration \
  --display-name "Databricks Genie Bot"
```

**或使用 Azure Portal：**

1. 登入 [Azure Portal](https://portal.azure.com)
2. **+ Create a resource** → 搜尋 **Bot Channels Registration**
3. 填寫表單：
   - **Bot name**: `databricks-genie-bot-prod`
   - **Subscription**: 選擇目標訂閱
   - **Resource Group**: 建立新的或選擇現有
   - **Location**: `East Asia` (推薦)
   - **Pricing Tier**: `F0` (免費) 或 `S1` (標準)
4. **Create**

### 步驟 2：取得 Bot 認證

部署完成後：

1. 進入新建的 **Bot Channels Registration** 資源
2. 左側菜單 → **Configuration**
3. 複製以下信息：
   ```
   Microsoft App ID: <複製此項>
   Tenant ID: <通常是 bb5ad653-221f-4b94-9c26-f815e04eef40>
   ```
4. 點擊 **Manage Microsoft App ID**
   - 新標籤頁打開 Azure AD
   - 左側 → **Certificates & secrets**
   - **New client secret**
   - Description: `DatabricksGenieBOT-Production`
   - **Add**
   - 立即複製 **Value**（只顯示一次）

> ⚠️ **重要**: 妥善保管 App ID 和 Secret

### 步驟 3：配置 OAuth Connection

1. 回到 **Bot Channels Registration**
2. 左側 → **Configuration**
3. 向下滾動到 **OAuth Connection Settings**
4. **Add OAuth Connection Settings**

填寫以下信息：

| 欄位 | 值 |
|------|-----|
| Name | `GraphConnection` |
| Service Provider | `Azure Active Directory v2` |
| Client ID | [Azure AD App ID] |
| Client Secret | [Azure AD Client Secret] |
| Tenant | `common` |
| Scopes | `User.Read User.ReadBasic.All email profile` |

5. **Save**
6. 測試連接 (應該看到綠色的 ✓)

---

## 代碼部署

### 選項 A：使用 Git (推薦 - 最快)

#### 在 Azure 中配置

1. 進入 **App Service**（如果還沒有，先建立一個）
   - **Create** → **App Service**
   - Runtime: `Python 3.11`
   - OS: `Windows`
   - Plan: 最少 `B1 Basic`

2. **Deployment Center**
   ```
   Source: GitHub
   Organization: carrossoni
   Repository: DatabricksGenieBOT
   Branch: develop
   ```

3. Azure 會自動建立 GitHub Actions workflow 並開始部署

4. 在 **Deployments** 中監控進度

#### 本地準備

```bash
# 確保代碼已推送到 GitHub
cd d:\azure_code\DatabricksGenieBOT
git add .
git commit -m "Prepare for production deployment"
git push origin develop
```

### 選項 B：使用 Docker

```bash
# 本地構建
docker build -t databricks-genie:1.0 .

# 推送到 Azure Container Registry
docker tag databricks-genie:1.0 yourregistry.azurecr.io/databricks-genie:1.0
docker push yourregistry.azurecr.io/databricks-genie:1.0

# 在 App Service 中配置容器映像
# App Service → Settings → Container settings
# Image source: Azure Container Registry
# Registry: yourregistry
# Image: databricks-genie
# Tag: 1.0
```

### 選項 C：手動 ZIP 部署

```bash
# 1. 準備部署文件
cd d:\azure_code\DatabricksGenieBOT

# 2. 安裝依賴到本地
uv sync --frozen

# 3. 建立部署包 (排除不需要的文件)
$exclude = @('.git', '.venv', 'env', '__pycache__', '.pytest_cache', '*.log', 'node_modules')
Get-ChildItem -Path . -Recurse | 
  Where-Object { $_.FullName -notmatch ($exclude -join '|') } |
  Compress-Archive -DestinationPath deploy.zip

# 4. 上傳到 Azure
# App Service → Deployment Center → Manual deployment → 上傳 deploy.zip
```

---

## 配置驗證

### 步驟 1：更新環境變數

在 **App Service → Configuration → Application settings** 中新增：

```
APP_ID                          = [從 Bot Service 取得]
APP_PASSWORD                    = [從 Bot Service 取得]
APP_TYPE                        = SingleTenant
APP_TENANTID                    = bb5ad653-221f-4b94-9c26-f815e04eef40
DATABRICKS_SPACE_ID             = [您的 Space ID]
DATABRICKS_HOST                 = [您的 Databricks URL]
DATABRICKS_TOKEN                = [您的 PAT Token]
OAUTH_CONNECTION_NAME           = GraphConnection
ENABLE_GRAPH_API_AUTO_LOGIN     = True
PORT                            = 8000
SAMPLE_QUESTIONS                = "查詢上個月的用量?;查詢本月費用?"
ADMIN_CONTACT_EMAIL             = support@company.com
TIMEZONE                        = Asia/Taipei
ENABLE_FEEDBACK_CARDS           = True
ENABLE_GENIE_FEEDBACK_API       = True
VERBOSE_LOGGING                 = False
LOG_FILE                        = bot_debug.log
```

**儲存並重啟 App Service**

### 步驟 2：驗證健康檢查

```bash
# 訪問健康檢查端點
curl https://your-app-name.azurewebsites.net/api/health

# 應返回
{"status": "ok"}
```

### 步驟 3：檢查日誌

```bash
# 在 Azure Portal 中查看實時日誌
# App Service → Log stream

# 或下載日誌文件
# App Service → SSH 或 Kudu Console (https://your-app-name.scm.azurewebsites.net)
```

---

## Teams 整合

### 步驟 1：準備應用程式套件

編輯 `manifest.json`：

```json
{
  "id": "YOUR-BOT-APP-ID",      // ← 替換為你的 Bot App ID
  "botId": "YOUR-BOT-APP-ID",   // ← 同上
  ...
}
```

### 步驟 2：準備圖標

準備兩個 192x192 PNG 圖標：
- `outline.png` - 黑色/灰色版本
- `color.png` - 彩色版本

### 步驟 3：建立 Teams App 包

```bash
# 建立目錄
mkdir teams-app

# 複製文件
copy manifest.json teams-app/
copy outline.png teams-app/
copy color.png teams-app/

# 建立 ZIP (manifest.json 必須在根層)
cd teams-app
Compress-Archive -Path * -DestinationPath ../teams-app.zip
cd ..
```

### 步驟 4：在 Teams 中上傳應用

**方法 A：個人測試**
1. Teams → **Apps**
2. **Upload a custom app** → 選擇 `teams-app.zip`
3. 應用程式出現在側邊欄

**方法 B：組織範圍部署**
1. [Teams Admin Center](https://admin.teams.microsoft.com)
2. **Manage apps** → **Upload new app**
3. 選擇 `teams-app.zip`
4. **Publish** 或分配給特定團隊

---

## 測試驗證

### 基本功能測試

```
測試項目                   預期結果
────────────────────────────────────────
1. 健康檢查               200 OK, {"status": "ok"}
2. help 指令              顯示可用命令列表
3. info 指令              顯示機器人信息
4. whoami 指令            顯示登入使用者資訊
5. 自然語言查詢           回傳 Genie 結果
6. 圖表生成               顯示圖表圖片
7. 建議問題               顯示並可點擊問題
8. 回饋卡片               顯示讚/倒讚按鈕
```

### 詳細測試步驟

#### 在 Web Chat 中測試
1. Azure Bot Service → **Test in Web Chat**
2. 輸入 `help` → 應顯示指令列表

#### 在 Teams 中測試
1. 打開應用程式
2. 輸入 `whoami` → 應顯示您的資訊
3. 輸入 Genie 查詢 (例如："查詢上個月的用量")
4. 驗證圖表是否正確顯示

---

## 生產環境設定

### 性能優化

#### 應用服務計畫升級
- 開發：`B1 Basic` (1 個核心，1.75 GB RAM)
- 生產：`B2 Standard` (2 個核心，3.5 GB RAM) 或以上

#### 啟用自動縮放
1. **App Service Plan** → **Settings** → **Scale out**
2. 配置自動縮放規則：
   - 最小實例：1
   - 最大實例：3
   - 觸發器：CPU % > 70

### 監控和告警

#### 啟用 Application Insights
1. **App Service** → **Settings** → **Application Insights**
2. **Enable Application Insights**
3. 建立新資源或選擇現有
4. 儲存

#### 設定告警
1. **Application Insights** → **Alerts**
2. **New alert rule**
3. 條件：
   - Failed requests > 5 in 5 minutes
   - Server response time > 5s

#### 查看監控數據
- 性能：**Performance** 標籤
- 故障：**Failures** 標籤
- 日誌：**Logs** (KQL 查詢)

### 安全最佳實踐

#### 1. 使用 Azure Key Vault 管理敏感資訊

```bash
# 建立 Key Vault
az keyvault create --name databricks-genie-kv --resource-group your-rg

# 新增密鑰
az keyvault secret set --vault-name databricks-genie-kv \
  --name app-password --value YOUR-PASSWORD

# 在 App Service 中參考
# Configuration → New application setting
# Name: APP_PASSWORD
# Value: @Microsoft.KeyVault(SecretUri=https://databricks-genie-kv.vault.azure.net/secrets/app-password/)
```

#### 2. 配置 IP 限制 (可選)
- **App Service** → **Networking** → **Access Restrictions**
- 只允許 Teams 和 Bot Framework 的 IP 範圍

#### 3. 啟用 CORS
- `web.config` 已配置完畢
- 驗證 `validDomains` 包含您的網域

#### 4. 定期安全審計
- [ ] 檢查依賴包更新
- [ ] 運行 SAST (如 SonarQube)
- [ ] 定期輪換密鑰

### 備份和恢復

#### 啟用備份
1. **App Service** → **Settings** → **Backups**
2. **Configure backup**
3. 存儲帳戶：選擇或建立
4. 頻率：每日或每週
5. **Save**

#### 恢復步驟
1. **Backups** → 選擇備份
2. **Restore**
3. 監控恢復進度

---

## 快速故障排查

| 問題 | 解決方案 |
|------|--------|
| Bot 無響應 | 1. 檢查 App Service 狀態 2. 查看 log stream 3. 驗證訊息端點 |
| OAuth 失敗 | 1. 驗證 App ID/Secret 2. 檢查 API 權限 3. 重新測試連接 |
| 圖表不顯示 | 1. 檢查 matplotlib/seaborn 依賴 2. 查看日誌中的圖表錯誤 |
| Teams 應用無法上傳 | 1. 驗證 manifest.json 格式 2. 檢查 ZIP 結構 3. 確認 Bot App ID |

---

## 成功指標

部署成功的標誌：

✅ 健康檢查返回 200 OK  
✅ Bot 在 Teams 中有響應  
✅ 查詢返回 Genie 結果  
✅ 圖表正確生成和顯示  
✅ Application Insights 顯示無錯誤  
✅ 所有指令 (help, info, whoami) 正常運作  

---

## 下一步

- 🎯 [部署檢查清單](./DEPLOYMENT_CHECKLIST.md) - 詳細的部署步驟
- 📖 [Teams 整合指南](./teams_deployment.md) - Teams 特定設定
- 🔍 [故障排查](../troubleshooting.md) - 常見問題
- 📊 [性能優化](../architecture/optimization.md) - 優化建議

---

**最後更新**：2026 年 2 月 9 日  
**維護者**：Databricks Genie Bot 團隊
