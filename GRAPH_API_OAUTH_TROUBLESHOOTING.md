# Graph API OAuth 故障排查指南

## 🔴 常見錯誤：`'CloudAdapter' object has no attribute 'get_user_token'`

### 原因

當看到這個錯誤時，表示：
1. ❌ OAuth Connection 未在 Azure Portal 中正確配置
2. ❌ 或您正在使用 **Bot Emulator** (本地模擬器不支持 OAuth)

---

## ✅ 修復方案

### 情景 1: 在 Azure 生產環境中部署

**必須完成以下步驟：**

#### 第 1 步: 在 Azure Portal 中創建 OAuth Connection

1. 進入 **Bot Channels Registration** (您的 Bot Service)
2. 左側菜單 → **Configuration**
3. 向下滾動到 **OAuth Connection Settings**
4. 點擊 **+ New Connection Setting**

```
Connection Name:        GraphConnection  (與 config.py 中的 OAUTH_CONNECTION_NAME 相同)
Service Provider:       Azure Active Directory
Client ID:              <從 Azure AD 應用程式複製>
Client Secret:          <從 Azure AD 應用程式複製>
Token Exchange URL:     (留空)
Tenant:                 common
Scopes:                 openid email profile User.Read
```

#### 第 2 步: 獲取 Azure AD 應用程式 ID 和密鑰

1. 進入 **Azure Active Directory** → **App registrations**
2. 找到或創建您的應用程式
3. 進入應用程式設定
4. 複製 **Application (client) ID**
5. 進入 **Certificates & Secrets** → **Client Secrets**
6. 創建新密鑰並複製值

#### 第 3 步: 配置環境變數

在 Azure Web App 中添加：

```bash
ENABLE_GRAPH_API_AUTO_LOGIN=True
OAUTH_CONNECTION_NAME=GraphConnection
```

#### 第 4 步: 重啟機器人

```bash
# 在 Azure Portal 中重啟 Web App
az webapp restart --resource-group <resource-group> --name <app-name>
```

**結果**：OAuth 配置完成後，`get_user_token` 將正常工作 ✅

---

### 情景 2: 在 Bot Emulator 中開發測試

Bot Emulator 不支持 OAuth。機器人會自動回退到使用 Teams 提供的基本信息。

**預期行為**：
```
⚠️ CloudAdapter 不支援 get_user_token
   必須在 Azure Portal 中設定 OAuth Connection
   → 將使用 Teams 提供的基本資訊
```

**測試用戶信息**（來自 Emulator）：
```json
{
  "id": "test-user-id",
  "name": "User",
  "email": null,
  "aad_object_id": null
}
```

要完整測試 OAuth，**必須部署到 Azure** 並在 Teams 中測試。

---

### 情景 3: 在 Teams 本地測試中

如果在 Teams 中看到錯誤消息：

```
取得使用者 token 時發生錯誤: 'CloudAdapter' object has no attribute 'get_user_token'
```

**原因**：OAuth Connection 未正確配置

**解決方案**：
1. ✅ 完成上述 **第 1-4 步**
2. ✅ 確認環境變數 `ENABLE_GRAPH_API_AUTO_LOGIN=True`
3. ✅ 重啟機器人
4. ✅ 在 Teams 中重新測試

---

## 🔧 改進的錯誤處理 (已在代碼中更新)

### 之前 (會拋出異常):
```python
ERROR:graph_service:取得使用者 token 時發生錯誤: 'CloudAdapter' object has no attribute 'get_user_token'
WARNING:graph_service:無法透過 Graph API 取得完整使用者資訊，使用 Teams 提供的基本資訊
```

### 之後 (自動回退):
```python
📱 Teams 提供的基本信息:
   User ID: xxxxx
   Name: John Doe
   AAD ID: aaaaa (如果可用)
   Email: (如果可用)

⚠️ OAuth token 未取得。原因可能是：
   1. OAuth Connection 未在 Azure Portal 中配置
   2. 使用者未授權存取資訊
   3. 使用本地 Bot Emulator (不支持 OAuth)
   → 將使用 Teams 提供的基本資訊
```

**優點**：
- ✅ 機器人不會因 OAuth 缺失而崩潰
- ✅ 提供清晰的診斷信息
- ✅ 自動回退到基本功能

---

## 📋 診斷檢查清單

如果 Graph API 不工作，按以下步驟檢查：

### 環境檢查
- [ ] `ENABLE_GRAPH_API_AUTO_LOGIN=True` 已設定
- [ ] `OAUTH_CONNECTION_NAME=GraphConnection` 已設定
- [ ] 機器人已重啟

### Azure Portal 檢查
- [ ] Bot Channels Registration 存在
- [ ] OAuth Connection 已配置
- [ ] 連線名稱與 `OAUTH_CONNECTION_NAME` 相同
- [ ] Client ID 和 Secret 正確

### Azure AD 應用程式檢查
- [ ] 應用程式已註冊
- [ ] 應用程式 ID 與 Azure Portal 中的相同
- [ ] Client Secret 未過期
- [ ] API 權限已授予：`User.Read`, `email`, `openid`, `profile`

### 測試檢查
- [ ] 在 **Teams** 中測試（不是 Emulator）
- [ ] 使用 **真實的 Azure AD 帳戶** 登入
- [ ] 檢查機器人日誌

```bash
# 查看 Azure Web App 日誌
az webapp log tail --resource-group <rg> --name <app-name>
```

---

## 🎯 兩種運行模式對比

| 功能 | Bot Emulator | Azure Teams |
|------|-------------|------------|
| OAuth Support | ❌ 不支持 | ✅ 支持 |
| 取得 Email | ❌ | ✅ (需配置) |
| 取得 AAD ID | ❌ | ✅ (需配置) |
| 取得完整個人資料 | ❌ | ✅ (需配置) |
| 機器人是否運行 | ✅ 是 | ✅ 是 |
| 機器人功能 | ✅ 基本功能可用 | ✅ 完全功能 |

**結論**: 開發時用 Emulator，生產部署到 Azure + Teams

---

## 📝 代碼修復摘要

已更新 `graph_service.py` 中的以下方法：

### 1. `get_user_token()` - 改進的 OAuth token 獲取
```python
# 更好的錯誤檢查
# 詳細的診斷日誌
# 自動捕獲 AttributeError (CloudAdapter 不支持)
```

### 2. `get_user_email_and_id()` - 優先級級聯
```python
# 優先級 1: 從 Teams 提供的信息 (始終可用)
# 優先級 2: OAuth token (如果配置正確)
# 優先級 3: 回退到最小化資訊 (確保不會失敗)
```

---

## ✅ 驗證修復

在機器人日誌中應該看到：

### ✅ 成功情景 (OAuth 已配置):
```
📱 Teams 提供的基本信息:
   User ID: xxxxx
   Name: John Doe
   AAD ID: aaaaa
   Email: john@company.com

🔐 OAuth token 已取得，正在呼叫 Graph API...
✅ Graph API 成功返回完整使用者資訊
```

### ⚠️ 回退情景 (OAuth 未配置，正常):
```
📱 Teams 提供的基本信息:
   User ID: xxxxx
   Name: John Doe
   AAD ID: (未提供)
   Email: (未提供)

⚠️ OAuth token 未取得。原因可能是：
   1. OAuth Connection 未在 Azure Portal 中配置
   2. 使用者未授權存取資訊
   3. 使用本地 Bot Emulator (不支持 OAuth)
   → 將使用 Teams 提供的基本資訊
```

**機器人仍能正常運行，只是功能受限** ✅

---

## 🆘 進一步幫助

### 參考資源
- [GRAPH_API_SETUP.md](GRAPH_API_SETUP.md) - 完整設定指南
- [GRAPH_API_QUICK_REFERENCE.md](GRAPH_API_QUICK_REFERENCE.md) - API 快速參考
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - 通用故障排查

### 常用命令

```bash
# 查看機器人實時日誌
az webapp log tail --resource-group <rg> --name <app>

# 重啟機器人
az webapp restart --resource-group <rg> --name <app>

# 檢查環境變數
az webapp config appsettings list --resource-group <rg> --name <app>

# 設定環境變數
az webapp config appsettings set --resource-group <rg> --name <app> \
    --settings ENABLE_GRAPH_API_AUTO_LOGIN=True
```

---

## 🎉 結論

修復後：
- ✅ 機器人在任何環境中都能運行 (無論 OAuth 是否配置)
- ✅ 提供清晰的診斷信息
- ✅ OAuth 有效時自動提升功能
- ✅ OAuth 無效時自動回退到基本功能

**現在你可以安心在任何環境中部署機器人了！** 🚀
