# .env 配置範本和說明

> 環境變數配置指南 - 部署前必讀

## 文件位置

```
DatabricksGenieBOT/
├── .env              ← 本地開發和部署用
├── .env.example      ← 安全範本（可上傳 Git）
└── docs/deployment/  ← 部署指南（包括環境變數配置）
```

---

## ⚠️ 安全注意事項

### 🔐 什麼應該放在 .env
```
✅ 可以存放在 .env：
  • APP_ID (Bot App ID)
  • DATABRICKS_SPACE_ID
  • DATABRICKS_HOST
  • 其他非敏感設定

❌ 敝不應該放在 .env：
  • APP_PASSWORD (Bot App Password)
  • DATABRICKS_TOKEN
  • 其他密鑰
```

### 🔒 建議做法
1. **本地開發**：.env 中存放所有內容 (不上傳 Git)
2. **生產環境**：使用 Azure Key Vault 或 App Service Configuration
3. **.env.example**：安全版本 (密值為空) → 可上傳 Git

---

## 完整配置範本

### 複製此範本到 .env 文件

```dotenv
# ═══════════════════════════════════════════════════════════════
# Microsoft Bot Framework 設定 - 必須配置
# ═══════════════════════════════════════════════════════════════

# Bot App ID - 從 Azure Bot Service 取得
# 位置：Azure Portal → Bot Channels Registration → Configuration
APP_ID=<從 Azure Bot Service 複製>

# Bot App Password - 從 Azure Bot Service 取得
# ⚠️ 密鑰只顯示一次，請立即複製！
# 位置：Azure Portal → Bot Service → Configuration → Manage App ID → Certificates & secrets
APP_PASSWORD=<從 Azure Bot Service 複製>

# 應用程式類型 - 通常為 SingleTenant
APP_TYPE=SingleTenant

# Azure AD 租戶 ID
# 如果不確定，通常是：bb5ad653-221f-4b94-9c26-f815e04eef40
APP_TENANTID=bb5ad653-221f-4b94-9c26-f815e04eef40


# ═══════════════════════════════════════════════════════════════
# Databricks Genie 設定 - 必須配置
# ═══════════════════════════════════════════════════════════════

# Databricks Genie Space ID
# 位置：Databricks 工作區 → Genie → 空間設定
DATABRICKS_SPACE_ID=<你的 Space ID>

# Databricks 實例 URL
# 格式：https://adb-<number>.azuredatabricks.net/
# 位置：Databricks 工作區 URL
DATABRICKS_HOST=https://adb-<number>.azuredatabricks.net/

# Databricks 個人存取令牌 (Personal Access Token)
# ⚠️ 敏感資訊 - 絕不要提交到 Git！
# 位置：Databricks 工作區 → User Settings → Access tokens
DATABRICKS_TOKEN=<你的 Databricks Personal Access Token>


# ═══════════════════════════════════════════════════════════════
# Microsoft Graph API OAuth 設定
# ═══════════════════════════════════════════════════════════════

# 啟用 Graph API 自動登入
# 設為 True 以啟用，False 以禁用
ENABLE_GRAPH_API_AUTO_LOGIN=True

# OAuth 連線名稱
# 必須與 Azure Bot Service 中的 OAuth Connection Settings 名稱相同
OAUTH_CONNECTION_NAME=GraphConnection


# ═══════════════════════════════════════════════════════════════
# 應用程式設定
# ═══════════════════════════════════════════════════════════════

# 應用程式運行埠號
# 本地開發：3978 或 5168
# Azure Web App：8000
PORT=8000

# 樣本問題 - 用戶首次登入時顯示
# 使用分號 (;) 分隔多個問題
SAMPLE_QUESTIONS="查詢上個月 Azure Databricks 的用量?;查詢上個月 VM 的用量?;查詢上個月 定價模型 的分配情況"

# 管理員聯絡郵箱 - 顯示在 info 指令中
ADMIN_CONTACT_EMAIL=ycliang@fareastone.com.tw

# 時區設定 - 用於時間戳記和排程
# 常見選項：Asia/Taipei, UTC, Asia/Shanghai, America/New_York
TIMEZONE=Asia/Taipei


# ═══════════════════════════════════════════════════════════════
# 功能開關
# ═══════════════════════════════════════════════════════════════

# 啟用回饋卡片 (讚/倒讚功能)
ENABLE_FEEDBACK_CARDS=True

# 啟用 Genie 回饋 API (將回饋發送到 Databricks)
ENABLE_GENIE_FEEDBACK_API=True


# ═══════════════════════════════════════════════════════════════
# 日誌記錄設定
# ═══════════════════════════════════════════════════════════════

# 詳細日誌記錄
# True：啟用 DEBUG 級別日誌（開發使用）
# False：標準 INFO 級別日誌（生產推薦）
VERBOSE_LOGGING=True

# 日誌檔案名稱（相對路徑）
LOG_FILE=bot_debug.log
```

---

## 配置說明

### 🔴 必須配置的變數 (6 個)

1. **APP_ID**
   - 從哪取：Azure Portal → Bot Service → Configuration → Microsoft App ID
   - 格式：`12345678-1234-1234-1234-123456789abc` (UUID)
   - 用途：Bot Framework 身份驗證

2. **APP_PASSWORD**
   - 從哪取：Azure Portal → Bot Service → Configuration → Manage App ID → Certificates & secrets
   - 格式：`SD-8Q~imC~yYprU3tBhmvhjKu3Irr...`
   - ⚠️ 只顯示一次！必須立即複製
   - 用途：Bot Framework 身份驗證

3. **DATABRICKS_SPACE_ID**
   - 從哪取：Databricks 工作區 → Genie → 空間設定
   - 格式：`01f0e08cf60e10a1a35bb8615b234b19` (24 字符)
   - 用途：指定要查詢的 Genie 空間

4. **DATABRICKS_HOST**
   - 從哪取：Databricks 工作區 URL
   - 格式：`https://adb-2654999172504234.14.azuredatabricks.net/`
   - 用途：Databricks API 端點

5. **DATABRICKS_TOKEN**
   - 從哪取：Databricks → User Settings → Access tokens → Generate new token
   - 格式：`dapi<your-token-here>`
   - ⚠️ 敏感！絕不要提交到 Git
   - 用途：Databricks API 身份驗證

6. **APP_TENANTID**
   - 從哪取：通常是 `bb5ad653-221f-4b94-9c26-f815e04eef40`
   - 格式：UUID
   - 用途：Azure AD 租戶識別

### 🟡 建議配置的變數 (4 個)

7. **OAUTH_CONNECTION_NAME**
   - 默認：`GraphConnection`
   - 用途：與 Azure Bot Service 中的 OAuth Connection Settings 關聯
   - 變更：通常不需要

8. **SAMPLE_QUESTIONS**
   - 默認：`"查詢上個月 Azure Databricks 的用量?;..."`
   - 用途：使用者登入時顯示的建議問題
   - 分隔符：分號 (`;`)

9. **ADMIN_CONTACT_EMAIL**
   - 默認：`admin@company.com`
   - 用途：使用者聯絡支援時顯示
   - 建議：使用團隊的支援郵箱

10. **TIMEZONE**
    - 默認：`Asia/Taipei`
    - 常見選項：
      - `Asia/Taipei` - 臺北/台灣
      - `UTC` - 格林威治
      - `Asia/Shanghai` - 上海/中國
      - `America/New_York` - 紐約/美東
    - 用途：時間戳記和排程

### 🟢 可選配置的變數 (6 個)

11. **ENABLE_GRAPH_API_AUTO_LOGIN**
    - 默認：`True`
    - 選項：`True` 或 `False`
    - 用途：自動從 Microsoft Graph 取得使用者資訊

12. **ENABLE_FEEDBACK_CARDS**
    - 默認：`True`
    - 選項：`True` 或 `False`
    - 用途：顯示回饋卡片 (讚/倒讚)

13. **ENABLE_GENIE_FEEDBACK_API**
    - 默認：`True`
    - 選項：`True` 或 `False`
    - 用途：將回饋發送到 Databricks Genie API

14. **VERBOSE_LOGGING**
    - 默認開發：`True`（啟用 DEBUG 日誌）
    - 默認生產：`False`（INFO 級別）
    - 用途：控制日誌詳細程度

15. **LOG_FILE**
    - 默認：`bot_debug.log`
    - 用途：日誌檔案名稱

16. **PORT**
    - 默認本地：`5168` 或 `3978`
    - 默認 Azure：`8000`
    - 用途：應用程式監聽的埠號

---

## 本地開發 vs 生產配置

### 🖥️ 本地開發 (.env)

```dotenv
# 本地使用 App Service 認證 (若要測試完整流程)
# 或留空用於 Bot Emulator 測試
APP_ID=<如果使用 Bot Emulator，留空>
APP_PASSWORD=<如果使用 Bot Emulator，留空>

# Databricks - 使用測試環境
DATABRICKS_SPACE_ID=<測試 Space ID>
DATABRICKS_HOST=<測試 Databricks 實例>
DATABRICKS_TOKEN=<測試 Token>

# 日誌 - 詳細模式用於開發
VERBOSE_LOGGING=True
LOG_FILE=bot_debug.log

# 埠 - 本地開發
PORT=5168
```

### ☁️ 生產環境 (Azure App Service Configuration)

```
應用程式設定：

APP_ID                       = <生產 Bot App ID>
APP_PASSWORD                 = @Microsoft.KeyVault(SecretUri=...)
DATABRICKS_SPACE_ID          = <生產 Space ID>
DATABRICKS_HOST              = <生產 Databricks 實例>
DATABRICKS_TOKEN             = @Microsoft.KeyVault(SecretUri=...)
VERBOSE_LOGGING              = False
LOG_FILE                     = /home/LogFiles/bot_debug.log
PORT                         = 8000
```

---

## 驗證和測試

### ✅ 驗證 .env 配置

```bash
# 1. 檢查 .env 文件語法
python -c "from dotenv import load_dotenv; load_dotenv(); print('✓ .env loaded successfully')"

# 2. 列出已載入的環境變數
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('\n'.join([f'{k}={v[:20]}...' if len(v)>20 else f'{k}={v}' for k,v in os.environ.items() if k.startswith(('APP_', 'DATABRICKS_'))]))"

# 3. 檢查必須的變數
python -c "
import os
from dotenv import load_dotenv

load_dotenv()

required = ['APP_ID', 'APP_PASSWORD', 'DATABRICKS_SPACE_ID', 
            'DATABRICKS_HOST', 'DATABRICKS_TOKEN', 'APP_TENANTID']

missing = [var for var in required if not os.getenv(var)]

if missing:
    print(f'❌ 缺少必要變數：{missing}')
else:
    print('✅ 所有必要變數都已配置')
"
```

### 🧪 測試應用程式啟動

```bash
# 1. 啟動應用程式
cd d:\azure_code\DatabricksGenieBOT
uv run python -m uvicorn app.main:app --port 8000

# 2. 測試健康檢查
curl http://localhost:8000/api/health
# 預期：{"status": "ok"}

# 3. 檢查日誌
# 應該看到：
# 🔍 日誌級別設置為: DEBUG (如果 VERBOSE_LOGGING=True)
# 📄 日誌文件: bot_debug.log
```

---

## 常見錯誤和解決

### ❌ 錯誤：`DATABRICKS_TOKEN 環境變數是必需的`

```
原因：DATABRICKS_TOKEN 未設定
解決：
1. 檢查 .env 中是否有 DATABRICKS_TOKEN=...
2. 確認 Token 不是空值
3. 重新啟動應用程式
```

### ❌ 錯誤：`無法連接到 Databricks`

```
原因：DATABRICKS_HOST 或 DATABRICKS_TOKEN 不正確
解決：
1. 驗證 DATABRICKS_HOST 格式：https://adb-<number>.azuredatabricks.net/
2. 驗證 Token 未過期（Databricks 中檢查）
3. 測試連接：curl -H "Authorization: Bearer <TOKEN>" <HOST>/api/2.0/workspace/get-status
```

### ❌ 錯誤：`auth: Invalid bearer token`

```
原因：DATABRICKS_TOKEN 格式不正確或已過期
解決：
1. 在 Databricks 中重新生成 Token
2. 確認 Token 開頭為 "dapi" 或 "dapit"
3. 更新 .env 並重啟
```

### ❌ 錯誤：`OAuth connection failed`

```
原因：OAUTH_CONNECTION_NAME 未在 Azure Bot Service 中配置
解決：
1. Azure Portal → Bot Service → Configuration
2. 檢查 OAuth Connection Settings 中是否有 "GraphConnection"
3. 驗證 Client ID 和 Client Secret 正確
4. 測試連接（應顯示綠色 ✓）
```

---

## 遷移到 Azure Key Vault

### 💾 什麼時候需要 Key Vault

- ✅ 生產環境
- ✅ 多個部署環境
- ✅ 敏感密鑰管理
- ✅ 審計和合規需求

### 📋 遷移步驟

1. **建立 Key Vault**
   ```bash
   az keyvault create --name databricks-genie-kv \
     --resource-group your-rg \
     --location eastasia
   ```

2. **新增密鑰**
   ```bash
   az keyvault secret set --vault-name databricks-genie-kv \
     --name app-password --value $APP_PASSWORD
   
   az keyvault secret set --vault-name databricks-genie-kv \
     --name databricks-token --value $DATABRICKS_TOKEN
   ```

3. **配置 App Service 存取**
   ```bash
   # 為 App Service 分配 Managed Identity
   az webapp identity assign --name your-app-name \
     --resource-group your-rg
   
   # 授予 Key Vault 存取權限
   az keyvault set-policy --name databricks-genie-kv \
     --object-id <managed-identity-object-id> \
     --secret-permissions get list
   ```

4. **在 App Service 中參考密鑰**
   ```
   Configuration → New application setting
   
   Name:  APP_PASSWORD
   Value: @Microsoft.KeyVault(SecretUri=https://databricks-genie-kv.vault.azure.net/secrets/app-password/)
   ```

---

## 檢查清單

部署前確保：

- [ ] 所有 6 個必須變數都已配置
- [ ] `APP_PASSWORD` 已安全保管
- [ ] `DATABRICKS_TOKEN` 已安全保管
- [ ] Databricks 認證已驗證可用
- [ ] `DATABRICKS_HOST` 以 `/` 結尾
- [ ] 時區設定正確
- [ ] 樣本問題已自訂（可選）
- [ ] `.env` 文件未提交到 Git
- [ ] `.env.example` 已更新為安全版本
- [ ] 本地測試成功（健康檢查、日誌）

---

## 參考資源

### 相關文檔
- 📖 [DEPLOYMENT_GUIDE.md](../deployment/DEPLOYMENT_GUIDE.md) - 部署步驟
- ✅ [DEPLOYMENT_CHECKLIST.md](../deployment/DEPLOYMENT_CHECKLIST.md) - 完整檢查清單
- 🔐 [AZURE_AD_SETUP.md](../deployment/AZURE_AD_SETUP.md) - OAuth 配置

### 外部資源
- [Databricks API 文檔](https://docs.databricks.com/api/)
- [Azure Bot Service 配置](https://learn.microsoft.com/en-us/azure/bot-service/bot-service-resources-app-service-settings)
- [Azure Key Vault 指南](https://learn.microsoft.com/en-us/azure/key-vault/)

---

**最後更新**：2026 年 2 月 9 日  
**版本**：1.0.0  
**狀態**：✅ 完成
