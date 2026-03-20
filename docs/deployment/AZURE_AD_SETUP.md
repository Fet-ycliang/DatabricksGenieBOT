# Azure AD OAuth 設定指南

> 此指南用於配置 Microsoft Graph API OAuth，以便 Teams Bot 可以存取使用者信息。

## 概述

此過程包括以下步驟：

1. 建立 Azure AD App Registration
2. 配置 API 權限
3. 建立 Client Secret
4. 在 Bot Service 中配置 OAuth Connection

---

## 詳細步驟

### 步驟 1：建立 Azure AD App Registration

1. 登入 [Azure Portal](https://portal.azure.com)
2. 搜尋 **Azure Active Directory** (或從左側菜單)
3. 左側 → **App registrations**
4. **+ New registration**

填寫表單：
```
Name:                          DatabricksGenieBOT-OAuth
Supported account types:       Accounts in this organizational directory only
Redirect URI:                  暫時留空
```

5. **Register**

### 步驟 2：複製應用程式 ID

在新建的應用程式中：

- 複製 **Application (client) ID**，稍後會用到
- 複製 **Directory (tenant) ID** (通常是 `bb5ad653-221f-4b94-9c26-f815e04eef40`)

### 步驟 3：配置重定向 URI

1. 左側 → **Authentication**
2. **Add a platform** → **Web**
3. 在 **Redirect URIs** 中輸入：
   ```
   https://token.botframework.com/.auth/web/redirect
   ```
4. 勾選 **Access tokens** 和 **ID tokens**
5. **Configure**

### 步驟 4：設定 API 權限

1. 左側 → **API permissions**
2. **+ Add a permission**
3. 選擇 **Microsoft Graph**
4. 選擇 **Delegated permissions**
5. 搜尋並勾選以下權限：

**建議的權限：**
```
☑ User.Read
☑ User.ReadBasic.All
☑ email
☑ profile
☑ openid
```

**完整清單（如需更多功能）：**
```
☑ User.Read                    // 讀取登入使用者信息
☑ User.ReadBasic.All           // 讀取所有使用者的基本信息
☑ Directory.Read.All           // 讀取目錄結構
☑ email                        // 存取電子郵件
☑ profile                      // 存取使用者設檔
☑ openid                       // OpenID 連接
```

6. **Add permissions**

### 步驟 5：授予管理員同意（可選但推薦）

如果有權限：

1. 仍在 **API permissions**
2. 點擊 **Grant admin consent for [Tenant Name]**
3. **Yes**

### 步驟 6：建立 Client Secret

1. 左側 → **Certificates & secrets**
2. **+ New client secret**

填寫：
```
Description:                   DatabricksGenieBOT-Production-Secret
Expires:                        24 months (或 12 months)
```

3. **Add**
4. **立即複製 Value** (秘密值只顯示一次)

> ⚠️ **重要**：妥善保管此密鑰，不要在代碼中硬編碼

### 步驟 7：在 Bot Service 中配置 OAuth Connection

1. 前往 **Azure Bot Service** → **Configuration**
2. 向下滾動到 **OAuth Connection Settings**
3. **Add OAuth Connection Settings**

填寫以下信息：

| 欄位 | 值 | 備註 |
|------|-----|------|
| **Name** | `GraphConnection` | 必須與 `.env` 中的 `OAUTH_CONNECTION_NAME` 相符 |
| **Service Provider** | `Azure Active Directory v2` | 必須選擇 v2 版本 |
| **Client ID** | [App Registration 的 Application ID] | 從步驟 2 複製 |
| **Client Secret** | [從步驟 6 複製的密鑰值] | 機密資訊，妥善保管 |
| **Tenant** | `common` 或 `bb5ad653-221f-4b94-9c26-f815e04eef40` | 建議使用特定租戶 ID |
| **Scopes** | `User.Read User.ReadBasic.All email profile openid` | 使用空格分隔 |

4. **Save**

### 步驟 8：測試 OAuth Connection

保存後，在同一頁面：

1. 尋找 **Test Connection** (在剛建立的 OAuth Connection 下)
2. 點擊 **Test**
3. 應該看到綠色的 ✓ 和 "Connection successful" 消息

如果失敗，檢查：
- [ ] Client ID 是否正確
- [ ] Client Secret 是否正確
- [ ] Tenant 是否正確
- [ ] API 權限是否已授予
- [ ] Redirect URI 是否正確

---

## 在代碼中使用 OAuth

### .env 配置

```dotenv
# OAuth 設定
OAUTH_CONNECTION_NAME=GraphConnection
ENABLE_GRAPH_API_AUTO_LOGIN=True
```

### 使用範例 (在 Bot Handler 中)

當使用者登入時，Bot 會自動呼叫 OAuth：

```python
# app/core/m365_agent_framework.py

async def ensure_token(self, context: TurnContext) -> Optional[str]:
    """
    確保使用者有有效的 OAuth token
    
    Returns:
        token 如果成功，None 如果失敗
    """
    # 先檢查是否已有 token
    token = context.turn_state.get("token")
    if token:
        return token
    
    # 嘗試取得新 token
    result = await context.adapter.get_token_status(
        context, 
        context.activity.from_property.id
    )
    
    if result and result[0].token:
        return result[0].token
    
    # 如果沒有 token，返回 None (Bot 會提示使用者登入)
    return None
```

---

## 常見問題

### Q: 如何更新 Client Secret?

1. 左側 → **Certificates & secrets**
2. 在舊 Secret 的旁邊點擊刪除 (垃圾桶圖標)
3. **+ New client secret**
4. 新增新的密鑰
5. **立即複製新值**
6. 更新 Bot Service 中的 OAuth Connection
7. 重啟 App Service

### Q: 如何撤銷使用者的 OAuth 授權?

1. 使用者在 Teams 中 → **Settings** → **Connected Accounts**
2. 尋找 "Databricks Genie Bot"
3. **Disconnect**

### Q: OAuth 過期後怎麼辦?

Bot 會自動處理 Token 刷新，使用者無需重新登入。

### Q: 如何限制哪些使用者可以使用此應用?

在 **App Registration** → **Enterprise applications** 中：
1. 選擇此應用
2. **Properties** → **User assignment required** 為 **Yes**
3. **Users and groups** → 新增允許的使用者/組

---

## 權限參考

| 權限 | 說明 | 必須 |
|------|-----|-----|
| `User.Read` | 讀取登入使用者的設檔信息 | ✅ |
| `User.ReadBasic.All` | 讀取所有使用者的基本信息 | ✅ |
| `email` | 存取使用者的電子郵件 | ✅ |
| `profile` | 存取使用者設檔數據 | ✅ |
| `openid` | 支援 OpenID Connect 登入 | ✅ |
| `Directory.Read.All` | 讀取整個目錄 | ⚠️ (可選，用於組織查詢) |
| `Mail.Read` | 讀取電子郵件 | ⚠️ (未來功能) |

---

## 安全最佳實踐

1. **永不在代碼中硬編碼 Client Secret**
   - 使用環境變數
   - 或使用 Azure Key Vault

2. **定期輪換 Client Secret**
   - 建議每 12-24 個月輪換一次
   - 建立新密鑰後再刪除舊的

3. **最小化權限**
   - 只授予所需的權限
   - 定期審計已授予的權限

4. **監控 OAuth 使用**
   - 在 Azure AD 中查看登入日誌
   - 設定告警規則

---

## 驗證清單

部署前確保完成以下事項：

- [ ] App Registration 已建立
- [ ] 重定向 URI 已配置
- [ ] API 權限已授予
- [ ] Client Secret 已建立
- [ ] OAuth Connection 在 Bot Service 中已配置
- [ ] OAuth Connection 測試成功
- [ ] `.env` 已更新正確的連線名稱
- [ ] 機密資訊已安全保管

---

**相關文件**：
- [部署指南](./DEPLOYMENT_GUIDE.md)
- [部署檢查清單](./DEPLOYMENT_CHECKLIST.md)
- [Teams 整合指南](./teams_deployment.md)

**最後更新**：2026 年 2 月 9 日
