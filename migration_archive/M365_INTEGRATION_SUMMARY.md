# Microsoft 365 Agent Framework 整合完成

## 概述

已成功將 Microsoft 365 Agent Framework SDK 導入到 DatabricksGenieBOT 項目中，並添加了完整的 skills 支持。

## 新增的功能

### 1. Core Services
- **M365AgentService** (`app/services/m365_agent.py`)
  - Microsoft Graph API 整合
  - Azure AD 驗證
  - 基礎服務操作

- **M365AgentFramework** (`app/core/m365_agent_framework.py`)
  - Skills 管理和編排
  - 統一的 API 接口
  - 使用者上下文管理

### 2. Skills 模組

#### Mail Skill (`app/services/skills/mail_skill.py`)
- 取得最近的電子郵件
- 搜尋郵件
- 發送郵件

#### Calendar Skill (`app/services/skills/calendar_skill.py`)
- 取得即將的事件
- 建立日曆事件
- 查找共同的空閒時間

#### OneDrive Skill (`app/services/skills/onedrive_skill.py`)
- 列出驅動項目
- 搜尋檔案
- 建立資料夾
- 取得檔案中繼資料
- 管理檔案共享權限

#### Teams Skill (`app/services/skills/teams_skill.py`)
- 列出使用者所屬的 Teams
- 列出頻道
- 取得和發送頻道訊息
- 搜尋 Teams 訊息
- 建立聊天

### 3. API 端點
所有功能通過 FastAPI 路由暴露：

```
GET /api/m365/skills                      - 獲取可用的 skills
GET /api/m365/profile                     - 獲取使用者個人資料
GET /api/m365/context                     - 獲取完整使用者上下文
GET /api/m365/mail/recent                 - 獲取最近的郵件
GET /api/m365/calendar/upcoming           - 獲取即將的事件
GET /api/m365/onedrive/items              - 列出 OneDrive 項目
GET /api/m365/teams                       - 列出 Teams
POST /api/m365/skill/execute              - 執行特定的 skill 方法
```

### 4. 更新的文件

- `pyproject.toml` - 添加了新的依賴項
- `app/main.py` - 新增 m365_agent 路由
- `app/bot_instance.py` - 整合 M365AgentFramework

## 依賴項

新增的 Python 包：

```
microsoft-365-agent-framework>=0.1.0
msgraph-core>=0.2.0
msgraph-sdk>=1.0.0
azure-eventhubs>=5.11.0
pydantic>=2.0.0
```

## 文檔

創建了完整的使用文檔：

1. **docs/m365_agent_framework.md** - 完整的使用指南
   - 架構介紹
   - API 使用示例
   - Python 代碼集成
   - 錯誤處理
   - 安全考慮

2. **docs/M365_SETUP.md** - 環境配置指南
   - .env 文件示例
   - Azure AD 應用註冊步驟
   - 權限配置
   - 本地開發設置
   - 生產部署指南

## 使用方式

### 快速開始

1. **安裝依賴項**
   ```bash
   pip install -e .
   ```

2. **配置環境變數**
   ```env
   AZURE_TENANT_ID=your_tenant_id
   AZURE_CLIENT_ID=your_client_id
   AZURE_CLIENT_SECRET=your_client_secret
   GRAPH_SCOPES=https://graph.microsoft.com/.default
   ```

3. **啟動應用**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

4. **測試 API**
   ```bash
   # 獲取可用的 skills
   curl http://localhost:8000/api/m365/skills
   
   # 獲取使用者郵件
   curl "http://localhost:8000/api/m365/mail/recent?count=5"
   ```

### 在 Bot 中集成

```python
from app.bot_instance import M365_AGENT_FRAMEWORK

async def handle_user_request(message):
    # 執行特定的 skill
    result = await M365_AGENT_FRAMEWORK.execute_skill(
        "mail",
        "get_recent_emails",
        user_id="me",
        count=5
    )
    return result
```

## 架構設計

```
app/
├── core/
│   ├── m365_agent_framework.py    # 主要 Framework 管理器
│   └── ...
├── services/
│   ├── m365_agent.py              # Microsoft Graph 服務
│   ├── skills/
│   │   ├── mail_skill.py          # 郵件 skill
│   │   ├── calendar_skill.py      # 日曆 skill
│   │   ├── onedrive_skill.py      # OneDrive skill
│   │   ├── teams_skill.py         # Teams skill
│   │   └── __init__.py
│   └── ...
├── api/
│   ├── m365_agent.py              # API 端點
│   └── ...
└── ...

docs/
├── m365_agent_framework.md        # 使用指南
├── M365_SETUP.md                  # 設置指南
└── ...
```

## 下一步

1. **Azure AD 配置**
   - 在 Azure Portal 中建立應用註冊
   - 配置 API 權限
   - 建立客戶端密碼

2. **環境變數配置**
   - 設置 .env 文件中的必要變數
   - 配置應用 ID 和客戶端密碼

3. **測試集成**
   - 使用 API 端點測試各項功能
   - 驗證權限配置

4. **生產部署**
   - 更新重定向 URI
   - 配置 Azure App Service
   - 設置生產環境變數

## 注意事項

1. **安全性**
   - 確保 Azure AD 客戶端密碼妥善保管
   - 遵循最小權限原則
   - 定期輪換密鑰

2. **速率限制**
   - Microsoft Graph API 有速率限制
   - 實施適當的重試邏輯
   - 監控 API 調用

3. **錯誤處理**
   - 所有 API 端點都提供統一的錯誤響應
   - 檢查日誌以進行故障排除
   - 驗證環境配置

## 技術支持

參考以下資源獲取幫助：

- [Microsoft Graph API 文檔](https://docs.microsoft.com/graph/overview)
- [Azure AD 開發指南](https://docs.microsoft.com/azure/active-directory/develop/)
- [Bot Framework 文檔](https://docs.microsoft.com/bot-framework/)
- [本地文檔](./docs/m365_agent_framework.md)
