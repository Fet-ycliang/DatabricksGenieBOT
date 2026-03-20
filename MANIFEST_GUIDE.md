# manifest.json 詳細說明

> Microsoft Teams 應用程式的定義文件

## 文件位置

```
DatabricksGenieBOT/
├── manifest.json              ← 此檔案 (根目錄)
└── docs/deployment/
    └── teams_deployment.md    ← Teams 整合指南
```

---

## 什麼是 manifest.json？

`manifest.json` 是 Teams 應用程式的配置檔案，定義：
- 應用程式的基本信息（名稱、描述、圖標）
- 機器人功能和作用域
- API 權限和功能
- 支援的命令列表

---

## 文件結構詳解

### 1. 基本信息部分

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/teams/v1.16/MicrosoftTeams.schema.json",
  "manifestVersion": "1.16",
  "version": "1.0.0",
```

| 欄位 | 說明 | 範例 |
|------|-----|------|
| `$schema` | Teams manifest 格式版本 | 保持不變 (v1.16) |
| `manifestVersion` | Manifest 版本號 | `1.16` |
| `version` | 應用程式版本 | `1.0.0` → `1.0.1` (更新時遞增) |

### 2. 應用程式標識

```json
  "id": "00000000-0000-0000-0000-000000000000",
  "packageName": "com.fareastone.databricksgeniebot",
```

| 欄位 | 說明 | 如何設定 |
|------|-----|--------|
| `id` | **⭐ 必須替換** 為 Bot App ID | Azure Bot Service → Configuration → Microsoft App ID |
| `packageName` | 應用程式包名稱 (反向網域命名) | 通常不變，格式：`com.company.appname` |

> ⚠️ **重要**：`id` 必須與 Azure Bot Service 的 App ID 相同

### 3. 開發者信息

```json
  "developer": {
    "name": "Fareastone",
    "websiteUrl": "https://www.fareastone.com.tw",
    "privacyUrl": "https://www.fareastone.com.tw/privacy",
    "termsOfUseUrl": "https://www.fareastone.com.tw/terms"
  },
```

| 欄位 | 說明 | 編輯提示 |
|------|-----|--------|
| `name` | 開發者/公司名稱 | 更改為你的組織名稱 |
| `websiteUrl` | 官方網站 | 更改為你的網站 |
| `privacyUrl` | 隱私政策連結 | 更改為你的隱私政策 URL |
| `termsOfUseUrl` | 服務條款連結 | 更改為你的服務條款 URL |

### 4. 應用程式名稱和描述

```json
  "name": {
    "short": "Databricks Genie",
    "full": "Databricks Genie Bot - 資料查詢助手"
  },
  "description": {
    "short": "Databricks 資料查詢 AI 助手",
    "full": "透過自然語言與 Databricks Genie 互動，快速查詢資料、生成圖表、進行數據分析"
  },
```

| 欄位 | 字數限制 | 說明 |
|------|--------|------|
| `name.short` | 30 字以內 | 應用程式列表中顯示的名稱 |
| `name.full` | 100 字以內 | 應用程式詳情頁顯示的完整名稱 |
| `description.short` | 80 字以內 | 應用程式摘要 |
| `description.full` | 4000 字以內 | 完整說明 |

### 5. 應用程式圖標

```json
  "icons": {
    "outline": "outline.png",
    "color": "color.png"
  },
```

| 圖標 | 規格 | 使用場景 |
|------|------|--------|
| `outline` | 192×192 px, 透明背景 | Teams 側邊欄、深色主題 |
| `color` | 192×192 px, 彩色 | 應用程式詳情、淺色主題 |

> 📁 **位置**：與 `manifest.json` 在同一文件夾（或在 ZIP 中同級）

### 6. 主題顏色

```json
  "accentColor": "#FFFFFF",
```

使用應用程式的主色調（十六進制顏色代碼）。建議選擇：
- `#FFFFFF` - 白色 (default)
- `#0078D4` - Teams 藍色
- `#6B69D6` - Databricks 紫色

### 7. 機器人配置 ⭐

```json
  "bots": [
    {
      "botId": "00000000-0000-0000-0000-000000000000",
      "scopes": [
        "personal",
        "team",
        "groupchat"
      ],
      "supportsFiles": false,
      "isNotificationOnly": false,
      "commandLists": [
        {
          "scopes": [
            "personal",
            "team",
            "groupchat"
          ],
          "commands": [
            {
              "title": "help",
              "description": "顯示所有可用指令和功能"
            },
            {
              "title": "info",
              "description": "顯示機器人資訊和使用說明"
            },
            {
              "title": "whoami",
              "description": "顯示您的使用者資訊和權限"
            }
          ]
        }
      ]
    }
  ],
```

#### 機器人配置詳解

| 欄位 | 說明 | 範例 |
|------|-----|------|
| `botId` | **⭐ 必須替換** Bot App ID | 同 `id` 欄位 |
| `scopes` | 機器人可以使用的範圍 | `personal` (1:1)、`team` (頻道)、`groupchat` (群組) |
| `supportsFiles` | 機器人是否支援文件上傳 | `false` (此應用不支援) |
| `isNotificationOnly` | 機器人是否為通知專用 | `false` (支援互動) |

#### 命令列表說明

使用者在 Teams 中輸入 `/` 時會看到這些命令：

```
/help      → 顯示所有可用指令和功能
/info      → 顯示機器人資訊和使用說明
/whoami    → 顯示您的使用者資訊和權限
```

你可以新增更多命令，例如：

```json
{
  "title": "query",
  "description": "查詢 Databricks 資料"
},
{
  "title": "chart",
  "description": "生成數據圖表"
}
```

### 8. 應用程式權限

```json
  "permissions": [
    "identity",
    "messageTeamMembers"
  ],
```

| 權限 | 說明 |
|------|-----|
| `identity` | 允許存取使用者身份 (用於 OAuth) |
| `messageTeamMembers` | 允許機器人傳送主動消息給使用者 |

常見權限：
- `identity` - 身份驗證
- `messageTeamMembers` - 主動傳送消息
- `validDomains` - 驗證域名

### 9. 有效域名

```json
  "validDomains": [
    "*.azurewebsites.net",
    "token.botframework.com"
  ]
```

指定機器人可以連接的域名。如果有自訂域名，添加：

```json
  "validDomains": [
    "*.azurewebsites.net",
    "token.botframework.com",
    "yourdomain.com"           ← 如果有自訂域名
  ]
```

---

## 編輯檢查清單

部署前確保修改以下內容：

- [ ] **`id`** - 替換為你的 Bot App ID
  ```json
  "id": "12345678-1234-1234-1234-123456789abc"
  ```

- [ ] **`botId`** (在 bots 陣列中) - 同上
  ```json
  "botId": "12345678-1234-1234-1234-123456789abc"
  ```

- [ ] **`developer.name`** - 改為你的組織名稱
  ```json
  "name": "Your Company Name"
  ```

- [ ] **`developer.websiteUrl`** - 改為你的網站
  ```json
  "websiteUrl": "https://yourcompany.com"
  ```

- [ ] **`developer.privacyUrl`** - 改為你的隱私政策
  ```json
  "privacyUrl": "https://yourcompany.com/privacy"
  ```

- [ ] **`developer.termsOfUseUrl`** - 改為你的服務條款
  ```json
  "termsOfUseUrl": "https://yourcompany.com/terms"
  ```

- [ ] **`name.short`** - 確認應用程式名稱
  ```json
  "short": "Databricks Genie"
  ```

- [ ] **`description`** - 確認應用程式描述

- [ ] **圖標準備** - 確保有 `outline.png` 和 `color.png`
  - 位置：與 manifest.json 同級目錄
  - 規格：192×192 pixels, PNG format

---

## 如何使用此文件

### 本地測試
1. 編輯 `manifest.json`
2. 準備圖標：`outline.png` 和 `color.png`
3. 建立 ZIP 檔案：
   ```bash
   mkdir teams-app
   copy manifest.json teams-app/
   copy outline.png teams-app/
   copy color.png teams-app/
   cd teams-app && Compress-Archive -Path * -DestinationPath ../teams-app.zip
   ```
4. Teams → **Apps** → **Upload custom app** → 選擇 `teams-app.zip`

### 生產發佈
1. 上傳到 Teams Admin Center
2. 分配給組織內的團隊
3. 或發佈到 Microsoft Teams App Store (需要審核)

---

## 常見修改

### 新增更多命令

```json
"commands": [
  {
    "title": "help",
    "description": "顯示所有可用指令"
  },
  {
    "title": "info",
    "description": "顯示機器人資訊"
  },
  {
    "title": "whoami",
    "description": "顯示您的使用者資訊"
  },
  {
    "title": "query",           // ← 新增命令
    "description": "查詢 Databricks 資料"
  },
  {
    "title": "report",         // ← 新增命令
    "description": "生成報表"
  }
]
```

### 添加自訂域名

```json
"validDomains": [
  "*.azurewebsites.net",
  "token.botframework.com",
  "yourdomain.com"            // ← 新增你的域名
]
```

### 變更應用程式版本

更新應用程式時遞增版本號：

```json
"version": "1.0.0"    // 首次發佈
"version": "1.0.1"    // 小的修復
"version": "1.1.0"    // 新功能
"version": "2.0.0"    // 重大變更
```

---

## 驗證 manifest.json

使用 Microsoft 提供的驗證工具：

1. 訪問 [Teams App Validator](https://dev.teams.microsoft.com/validation)
2. 上傳你的 manifest.json
3. 檢查是否有警告或錯誤

或使用命令行工具：
```bash
# 安裝 Teams 驗證工具
npm install @microsoft/teams-manifest-validator -g

# 驗證
teams-manifest-validator manifest.json
```

---

## 故障排查

### ❌ 上傳時出現 "Invalid manifest"
- [ ] 檢查 JSON 格式（使用 [JSON 驗證器](https://jsonlint.com/)）
- [ ] 確保 `id` 和 `botId` 已替換
- [ ] 檢查文件編碼是否為 UTF-8

### ❌ Bot 在 Teams 中無響應
- [ ] 驗證 `botId` 是否與 Azure Bot Service App ID 相同
- [ ] 檢查機器人訊息端點是否正確配置
- [ ] 查看 Application Insights 日誌

### ❌ 命令列表不顯示
- [ ] 檢查 `commandLists` 語法
- [ ] 確保至少有一個命令配置
- [ ] Teams 可能需要 5-10 分鐘才能更新

### ❌ 圖標不顯示
- [ ] 檢查圖標文件是否存在（與 manifest.json 同級）
- [ ] 驗證文件名稱完全匹配：`outline.png` 和 `color.png`
- [ ] 確認圖標規格：192×192 pixels, PNG format

---

## 參考資源

- 📖 [Microsoft Teams Manifest Schema](https://learn.microsoft.com/en-us/microsoftteams/platform/resources/schema/manifest-schema)
- 🔧 [Teams Developer Portal](https://dev.teams.microsoft.com)
- 💬 [Teams Bot Best Practices](https://learn.microsoft.com/en-us/microsoftteams/platform/bots/bot-basics)

---

## 下一步

1. ✅ 編輯此 manifest.json 文件
2. ✅ 準備圖標文件
3. ✅ 創建 Teams 應用包 (ZIP)
4. ✅ 上傳到 Teams
5. ✅ 測試機器人功能

詳見 [DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md) 或 [teams_deployment.md](./teams_deployment.md)

---

**最後更新**：2026 年 2 月 9 日
