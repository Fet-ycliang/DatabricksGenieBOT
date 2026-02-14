# Microsoft 365 Agent Framework 使用指南

## 概述

本應用已集成 Microsoft 365 Agent Framework SDK，提供與 Microsoft 365 services 互動的能力，包括郵件、日曆、OneDrive 和 Teams。

## 架構

### 核心組件

1. **M365AgentService** (`app/services/m365_agent.py`)
   - 與 Microsoft Graph API 互動的基礎服務
   - 處理驗證和授權

2. **Skills** (`app/services/skills/`)
   - `MailSkill`: 電子郵件操作
   - `CalendarSkill`: 日曆事件管理
   - `OneDriveSkill`: 檔案和資料夾操作
   - `TeamsSkill`: Teams 和聊天功能

3. **M365AgentFramework** (`app/core/m365_agent_framework.py`)
   - 統合所有 skills 的管理器
   - 提供統一的執行接口

4. **API 端點** (`app/api/m365_agent.py`)
   - HTTP 路由來訪問 Agent Framework 功能

## 環境配置

### 必需的環境變數

在 `.env` 文件中設置以下變數：

```env
# Azure AD 配置
AZURE_TENANT_ID=your_tenant_id
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret

# Microsoft Graph 權限
GRAPH_SCOPES=https://graph.microsoft.com/.default
```

### 必需的 Azure 權限

應用需要以下 Microsoft Graph 權限（委派權限）：

#### 郵件
- `Mail.Read` - 讀取使用者郵件
- `Mail.Send` - 發送郵件

#### 日曆
- `Calendars.Read` - 讀取日曆
- `Calendars.ReadWrite` - 建立和修改事件

#### OneDrive
- `Files.Read.All` - 讀取所有檔案
- `Files.ReadWrite.All` - 建立和修改檔案

#### Teams
- `Team.ReadBasic.All` - 讀取 Teams 基本信息
- `Chat.ReadWrite` - 讀取和寫入聊天訊息
- `ChannelMessage.Read.All` - 讀取頻道訊息

## 使用示例

### 1. 獲取可用的 Skills

```bash
GET /api/m365/skills
```

響應:
```json
{
  "status": "success",
  "skills": {
    "mail": ["get_recent_emails", "search_emails", "send_email"],
    "calendar": ["get_upcoming_events", "create_event", "find_free_time"],
    "onedrive": ["list_drive_items", "search_files", "create_folder", ...],
    "teams": ["list_teams", "list_channels", "get_channel_messages", ...]
  }
}
```

### 2. 獲取使用者上下文

```bash
GET /api/m365/context?user_id=me
```

返回包含使用者的個人資料、最近郵件、即將事件等的完整上下文。

### 3. 郵件操作

```bash
# 獲取最近的郵件
GET /api/m365/mail/recent?count=10

# 發送郵件
POST /api/m365/skill/execute
{
  "skill_name": "mail",
  "method_name": "send_email",
  "params": {
    "to_addresses": ["recipient@example.com"],
    "subject": "Hello",
    "body": "This is a test email"
  }
}
```

### 4. 日曆操作

```bash
# 獲取即將的事件
GET /api/m365/calendar/upcoming?count=10

# 建立事件
POST /api/m365/skill/execute
{
  "skill_name": "calendar",
  "method_name": "create_event",
  "params": {
    "subject": "Team Meeting",
    "start_time": "2024-02-08T14:00:00Z",
    "end_time": "2024-02-08T15:00:00Z",
    "attendees": ["colleague@example.com"]
  }
}
```

### 5. OneDrive 操作

```bash
# 列出驅動項目
GET /api/m365/onedrive/items?count=10

# 搜尋檔案
POST /api/m365/skill/execute
{
  "skill_name": "onedrive",
  "method_name": "search_files",
  "params": {
    "search_query": "report",
    "count": 5
  }
}

# 建立資料夾
POST /api/m365/skill/execute
{
  "skill_name": "onedrive",
  "method_name": "create_folder",
  "params": {
    "folder_name": "Projects"
  }
}
```

### 6. Teams 操作

```bash
# 列出所屬的 Teams
GET /api/m365/teams

# 發送訊息到頻道
POST /api/m365/skill/execute
{
  "skill_name": "teams",
  "method_name": "send_message_to_channel",
  "params": {
    "team_id": "team_id",
    "channel_id": "channel_id",
    "message_content": "Hello team!"
  }
}

# 搜尋 Teams 訊息
POST /api/m365/skill/execute
{
  "skill_name": "teams",
  "method_name": "search_teams_messages",
  "params": {
    "search_query": "important",
    "count": 10
  }
}
```

## Python 代碼中使用

### 在 Bot 處理器中使用

```python
from app.bot_instance import M365_AGENT_FRAMEWORK

async def handle_user_query(message_text, user_token=None):
    if not M365_AGENT_FRAMEWORK:
        return "Agent Framework not available"
    
    # 執行特定的 skill (傳入 user_token 以存取使用者資料)
    result = await M365_AGENT_FRAMEWORK.execute_skill(
        "mail",
        "get_recent_emails",
        user_id="me",
        count=5,
        token=user_token  # 關鍵：傳入 OAuth Token
    )
    return result
```

### 獲取使用者上下文

```python
from app.bot_instance import M365_AGENT_FRAMEWORK

async def get_user_info(user_id):
    if not M365_AGENT_FRAMEWORK:
        return None
    
    context = await M365_AGENT_FRAMEWORK.get_user_context(user_id)
    return context
```

### 創建自定義 Skill

要添加新的 skill，遵循以下步驟：

1. 在 `app/services/skills/` 中建立新文件，例如 `custom_skill.py`

```python
class CustomSkill:
    def __init__(self, graph_service):
        self.graph_service = graph_service
    
    async def my_custom_method(self, param1, param2):
        # 實現自定義邏輯
        pass
```

2. 在 `app/services/skills/__init__.py` 中導入

3. 在 `M365AgentFramework` 中初始化該 skill

```python
from app.services.skills.custom_skill import CustomSkill

# 在 __init__ 中
self.custom_skill = CustomSkill(self.m365_service)
```

## 錯誤處理

所有 API 端點都遵循統一的錯誤格式：

```json
{
  "status": "error",
  "error": "Error message"
}
```

常見錯誤：

- `Agent Framework 未初始化` - M365 服務啟動失敗
- `Skill not found` - 無效的 skill 名稱
- `Method not found` - 該 skill 不支持該方法
- `401 Unauthorized` - 驗證失敗或無效的權限

## 安全考慮

1. **驗證**: 使用 Azure AD 進行安全驗證
2. **權限**: 遵循最小權限原則，只請求必要的權限
3. **敏感信息**: 不要在日誌中存儲個人數據
4. **速率限制**: 遵守 Microsoft Graph API 的速率限制

## 故障排除

### 連接失敗

確保環境變數已正確設置，並且應用有正確的 Azure AD 權限。

### 權限不足

檢查應用在 Azure AD 中的權限配置，確保已授予所有必要的 Graph API 權限。

### 超時

某些操作可能需要較長時間。增加超時設置或使用異步操作。

## 進一步集成

本 Agent Framework 可與以下組件進行集成：

1. **Databricks Genie** - 使用 M365 services 來增強 Genie 查詢
2. **Bot Framework** - 在 Teams Bot 中提供 M365 功能
3. **自定義邏輯** - 根據特定業務需求擴展 skills

## 相關資源

- [Microsoft Graph API 文檔](https://docs.microsoft.com/graph/overview)
- [Azure AD 驗證](https://docs.microsoft.com/azure/active-directory/develop/)
- [Bot Framework 文檔](https://docs.microsoft.com/bot-framework/)
