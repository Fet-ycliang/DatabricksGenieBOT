# Microsoft Teams 整合指南

## 概述

本指南將協助您將 Databricks Genie 機器人部署到 Microsoft Teams。您的機器人已設定好 Bot Framework，但需要額外的 Teams 特定設定。

## 先決條件

- 已建立並設定 Azure Bot Service
- 機器人已部署到 Azure App Service
- Microsoft Teams 管理員權限（用於全組織部署）
- 有效的 Azure Bot Service 憑證

## 步驟 1：Azure Bot Service 設定

### 1.1 設定訊息端點

1. 前往 [Azure 入口網站](https://portal.azure.com)
2. 導航至您的 Bot Service 資源
3. 前往 **設定 (Configuration)** → **訊息 (Messaging)**
4. 將訊息端點設定為：`https://your-app-name.azurewebsites.net/api/messages`
5. 儲存設定

### 1.2 啟用 Teams 頻道

1. 在您的 Bot Service 中，前往 **頻道 (Channels)**
2. 點擊 **Microsoft Teams** 頻道
3. 點擊 **套用 (Apply)** 以啟用頻道
4. 記下 Teams App ID（應與您的機器人 App ID 相符）

## 步驟 2：建立 Teams 應用程式套件

### 2.1 建立資訊清單檔案 (Manifest File)

您需要為您的 Teams 應用程式建立一個 `manifest.json` 檔案。Microsoft 提供了範本和工具：

#### 選項 1：使用 Teams 開發人員入口網站（推薦）

1. 前往 [Teams 開發人員入口網站](https://dev.teams.microsoft.com/apps)
2. 點擊 **New app** 建立新應用程式
3. 填寫基本資訊
4. 前往 **Configure** → **App features** → **Bot**
5. 選擇您現有的機器人（使用您的 Azure Bot App ID）
6. 根據需要設定功能：Personal、Team、Group Chat
7. 完成後下載應用程式套件

#### 選項 2：手動建立資訊清單

使用 Microsoft 的資訊清單範本：[Teams 應用程式資訊清單結構描述](https://learn.microsoft.com/zh-tw/microsoftteams/platform/resources/schema/manifest-schema)

這是一個機器人的最小 `manifest.json` 範本：

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/teams/v1.16/MicrosoftTeams.schema.json",
  "manifestVersion": "1.16",
  "version": "1.0.0",
  "id": "YOUR-BOT-APP-ID-HERE",
  "packageName": "com.yourcompany.databricksgeniebot",
  "developer": {
    "name": "Your Company Name",
    "websiteUrl": "https://yourcompany.com",
    "privacyUrl": "https://yourcompany.com/privacy",
    "termsOfUseUrl": "https://yourcompany.com/terms"
  },
  "name": {
    "short": "Databricks Genie Bot",
    "full": "Databricks Genie Bot - Data Assistant"
  },
  "description": {
    "short": "AI assistant for Databricks data queries",
    "full": "A Teams bot that connects to Databricks Genie Space, allowing you to interact with your data through natural language queries."
  },
  "icons": {
    "outline": "outline.png",
    "color": "color.png"
  },
  "accentColor": "#FFFFFF",
  "bots": [
    {
      "botId": "YOUR-BOT-APP-ID-HERE",
      "scopes": ["personal", "team", "groupchat"],
      "supportsFiles": false,
      "isNotificationOnly": false,
      "commandLists": [
        {
          "scopes": ["personal", "team", "groupchat"],
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
              "title": "reset",
              "description": "開始新的對話"
            }
          ]
        }
      ]
    }
  ],
  "permissions": ["identity", "messageTeamMembers"],
  "validDomains": ["your-app-name.azurewebsites.net"]
}
```

**重要**：請替換範本中的以下內容：

- `YOUR-BOT-APP-ID-HERE` - 您的 Azure Bot Service App ID
- `com.yourcompany.databricksgeniebot` - 您的套件名稱
- `Your Company Name` - 您的組織名稱
- URLs - 您實際的公司網址
- `your-app-name.azurewebsites.net` - 您的 Azure App Service 網域

### 2.2 建立應用程式圖示

您的 Teams 應用程式需要兩個圖示檔案：

#### 圖示需求

- **color.png**：192x192 像素，全彩圖示，PNG 格式
- **outline.png**：32x32 像素，透明背景上的白色圖示，PNG 格式

#### 圖示資源

- **設計工具**：[Microsoft Teams 應用程式圖示指南](https://learn.microsoft.com/zh-tw/microsoftteams/platform/concepts/build-and-test/apps-package#app-icons)
- **圖示範本**：[Microsoft Teams 設計套件](https://learn.microsoft.com/zh-tw/microsoftteams/platform/concepts/design/design-teams-app-overview)
- **免費圖示**：[Flaticon](https://www.flaticon.com/) 或 [Icons8](https://icons8.com/) - 搜尋 "robot"、"chatbot" 或 "assistant"
- **線上編輯器**：[Canva](https://www.canva.com/) 或 [Figma](https://www.figma.com/) 進行自訂

#### 快速建立圖示

1. 尋找或建立一個機器人/聊天機器人圖示
2. 對於 `color.png`：建立 192x192px 版本，使用您的品牌顏色
3. 對於 `outline.png`：建立 32x32px 版本，透明背景上的白色圖示
4. 匯出為 PNG 檔案，並使用這些確切名稱

### 2.3 打包應用程式

1. 建立一個包含這三個檔案的資料夾：
   - `manifest.json`（來自步驟 2.1）
   - `color.png` (192x192 px)
   - `outline.png` (32x32 px)
2. 選取所有三個檔案並建立 ZIP 壓縮檔
3. 命名為 `DatabricksGenieBot.zip`
4. **重要**：檔案必須位於 ZIP 的根目錄，不能在子資料夾中

**驗證**：在上傳之前，使用 [Teams 應用程式驗證器](https://dev.teams.microsoft.com/appvalidation.html) 檢查您的套件

## 步驟 3：部署到 Teams

### 3.1 上傳到 Teams（管理員）

1. 前往 [Microsoft Teams 管理中心](https://admin.teams.microsoft.com)
2. 導航至 **Teams 應用程式** → **管理應用程式**
3. 點擊 **上傳** 並選擇您的 `DatabricksGenieBot.zip`
4. 審核並核准應用程式

### 3.2 為使用者安裝

1. 在 Teams 中，前往 **應用程式** → **為您的組織建置**
2. 找到 "Databricks Genie Bot"
3. 點擊 **新增** 進行安裝

## 步驟 4：測試整合

### 4.1 基本功能測試

1. 開啟與機器人的聊天
2. 發送訊息："help"
3. 確認您收到說明訊息
4. 測試使用者識別："whoami"

### 4.2 Databricks 整合測試

1. 詢問一個與資料相關的問題
2. 確認機器人處理請求
3. 檢查回應格式是否正確

## 步驟 5：疑難排解

### 常見問題

#### 機器人沒有回應

- 檢查 Azure App Service 記錄檔
- 驗證訊息端點 URL
- 確保機器人正在執行且狀態良好

#### 使用者識別問題

- 驗證 Teams 使用者已設定電子郵件
- 檢查機器人的使用者工作階段管理
- 審查驗證設定

#### Databricks API 錯誤

- 驗證 Databricks 憑證
- 檢查空間 ID 和權限
- 審查 API 權杖有效性

### 偵錯指令

- `/setuser email@company.com Name`（僅限模擬器）
- `whoami` - 檢查使用者工作階段
- `help` - 顯示可用指令

## 步驟 6：生產環境考量

### 安全性

- 使用 Azure Key Vault 儲存機密
- 實作適當的驗證
- 定期進行安全稽核

### 監控

- 設定 Application Insights
- 監控機器人效能
- 追蹤使用者參與度

### 擴展

- 設定自動擴展
- 監控資源使用量
- 規劃高可用性

## 支援

針對特定問題：

- **Bot Framework**：[Microsoft Bot Framework 文件](https://docs.microsoft.com/zh-tw/azure/bot-service/)
- **Teams 整合**：[Microsoft Teams 機器人開發](https://docs.microsoft.com/zh-tw/microsoftteams/platform/bots/what-are-bots)
- **Databricks API**：[Databricks Genie API 文件](https://docs.databricks.com/)

## 下一步

1. 完成 Azure Bot Service 設定
2. 建立適當的應用程式圖示
3. 打包並部署到 Teams
4. 在您的環境中進行徹底測試
5. 規劃使用者培訓和採用
