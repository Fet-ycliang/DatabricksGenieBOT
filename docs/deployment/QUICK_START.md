# 🚀 部署快速開始指南

> 5 分鐘快速版本 - 針對已有 Azure 經驗的開發人員

## 🎯 5 步部署流程

### 1️⃣ 建立 Azure 資源 (5 分鐘)
```bash
# Bot Service
az bot create --name databricks-genie-bot \
  --resource-group your-rg --app-type SingleTenant

# App Service (Python 3.11, B1+)
az appservice plan create -g your-rg -n app-plan --sku B1 --is-linux
az webapp create -g your-rg -n databricks-genie-webapp \
  -p app-plan --runtime "PYTHON:3.11"
```

### 2️⃣ 建立 OAuth 連接 (3 分鐘)
```
Azure Portal → Azure AD → App registrations → New
Name: DatabricksGenieBOT-OAuth

Redirect URI:
  https://token.botframework.com/.auth/web/redirect

API Permissions:
  ☑ User.Read
  ☑ User.ReadBasic.All
  ☑ email, profile, openid

Certificates & secrets → New client secret → Copy value

Bot Service → Configuration → OAuth Connection Settings → Add
  Name: GraphConnection
  Service Provider: Azure Active Directory v2
  Client ID: [From App Reg]
  Client Secret: [From App Reg]
  Tenant: bb5ad653-221f-4b94-9c26-f815e04eef40
  Scopes: User.Read User.ReadBasic.All email profile openid
```

### 3️⃣ 部署代碼 (2 分鐘)
```bash
# Git 部署
cd d:\azure_code\DatabricksGenieBOT
git push origin develop

# App Service → Deployment Center → GitHub
# 選擇倉庫和分支 → 自動部署開始
```

### 4️⃣ 配置環境變數 (1 分鐘)
```
App Service → Configuration → Application settings → Add

APP_ID                       = [Bot Service App ID]
APP_PASSWORD                 = [Bot Service App Password]
DATABRICKS_SPACE_ID          = [Your Space ID]
DATABRICKS_HOST              = [Your DB Host]
DATABRICKS_TOKEN             = [Your PAT Token]
OAUTH_CONNECTION_NAME        = GraphConnection
PORT                         = 8000
```

**保存 → 重啟 App Service**

### 5️⃣ 驗證和上傳 Teams (2 分鐘)
```bash
# 驗證健康檢查
curl https://your-app-name.azurewebsites.net/api/health
# 應返回: {"status": "ok"}

# 編輯 manifest.json
# 替換: "id": "YOUR-BOT-APP-ID-HERE"
# 替換: "botId": "YOUR-BOT-APP-ID-HERE"

# 上傳到 Teams
Teams → Apps → Upload custom app → teams-app.zip
```

---

## 📦 manifest.json 準備

```json
{
  "id": "YOUR-BOT-APP-ID-HERE",        // ← 替換你的 Bot App ID
  "botId": "YOUR-BOT-APP-ID-HERE",     // ← 同上
  ...其他欄位保持默認...
}
```

建立 ZIP：
```bash
mkdir teams-app
copy manifest.json teams-app/
copy outline.png teams-app/         # 需要準備此圖標
copy color.png teams-app/           # 需要準備此圖標
cd teams-app && Compress-Archive -Path * -DestinationPath ../teams-app.zip
```

---

## 🔑 重要變數對應

| 來源 | 變數 | 位置 |
|------|-----|------|
| Bot Service | APP_ID | Configuration → Microsoft App ID |
| Bot Service | APP_PASSWORD | Configuration → Manage App ID → Certificates & secrets |
| Azure AD | Client ID | App registrations → Application ID |
| Azure AD | Client Secret | App registrations → Certificates & secrets |
| Databricks | DATABRICKS_TOKEN | Workspace → User Settings → Access tokens |

---

## ✅ 測試清單

```bash
# 1. 健康檢查
curl https://your-app-name.azurewebsites.net/api/health

# 2. Teams 中測試
help              # 顯示指令列表
info              # 顯示機器人資訊
whoami            # 顯示使用者資訊
查詢上個月的用量   # 測試 Genie 查詢
```

---

## ⚡ 常見問題

### Bot 無響應
→ 檢查 `App Service → Log stream` 中的錯誤

### OAuth 連接失敗
→ 驗證 Azure AD 中的 Client Secret 是否正確

### 圖表不顯示
→ 檢查日誌中是否有 matplotlib 相關錯誤

### Teams 應用無法上傳
→ 驗證 manifest.json 格式，確保 Bot App ID 正確

---

## 📚 詳細指南

- 🔍 [完整部署檢查清單](./DEPLOYMENT_CHECKLIST.md)
- 📖 [完整部署指南](./DEPLOYMENT_GUIDE.md)
- 🔐 [Azure AD OAuth 詳細設定](./AZURE_AD_SETUP.md)
- 🎨 [Teams 應用整合](./teams_deployment.md)

---

**預計總時間**：15-20 分鐘  
**預計成本**：$10-20/月 (B1 App Service + Bot Service)

🎉 **完成後，你的 Bot 應該可以在 Teams 中正常使用！**
