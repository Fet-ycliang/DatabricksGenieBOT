# 🚀 DatabricksGenieBOT 遷移步驟指南

## 📊 項目評估結果

- **複雜度分數**: 100/100 (高)
- **估計工作量**: 60+ 小時
- **Dialog 數量**: 1 (SSODialog)
- **Handler 數量**: 3 (Bot, Commands, Identity)
- **Activity 類型**: 2 (message, members_added)

## 🎯 遷移優先級

### 優先級 1: SSO 驗證
**目標**: 將 SSODialog 轉換為 AuthenticationSkill

#### 現況分析
- **文件**: `bot/dialogs/sso_dialog.py`
- **類型**: ComponentDialog with OAuthPrompt
- **功能**: 處理 OAuth 2.0 SSO 流程

#### 遷移方式
```
SSODialog (Bot Framework)
    ↓
AuthenticationSkill (M365 Agent Framework)
    - Inherit from BaseSkill
    - 使用 DefaultAzureCredential 替代 OAuthPrompt
    - 集成 Microsoft Graph 身份驗證
```

### 優先級 2: 主 Handler
**目標**: 將 MyBot Handler 轉換為 BotCoreSkill

#### 現況分析
- **文件**: `bot/handlers/bot.py`
- **類型**: ActivityHandler
- **功能**: 處理成員加入、消息接收
- **依賴**: GenieService, UserSession, SSODialog

#### 遷移方式
```
MyBot (Bot Framework)
    ↓
BotCoreSkill (M365 Agent Framework)
    - 提取對話邏輯
    - 保留 Genie 服務集成
    - 轉換 Dialog 管理為 Skill 管理
```

### 優先級 3: 命令和身份
**目標**: 將 CommandsHandler 和 IdentityHandler 轉換為相應 Skill

#### 現況分析
- **文件**: `bot/handlers/commands.py`, `bot/handlers/identity.py`
- **功能**: 特殊命令處理、身份管理

#### 遷移方式
```
CommandsHandler + IdentityHandler
    ↓
CommandSkill + IdentityManagementSkill
```

---

## 📋 遷移執行計劃

### 階段 1: 準備 (1-2 天)

#### 1.1 環境設置
```bash
# 確保所有依賴已安裝
pip install -r requirements.txt

# 驗證 M365 服務已配置
python -c "from app.core.m365_agent_framework import M365AgentFramework; print('✅ M365 框架已準備')"
```

#### 1.2 代碼審查
- [ ] 審查 `bot/dialogs/sso_dialog.py` 的完整邏輯
- [ ] 審查 `bot/handlers/bot.py` 的 Dialog 集成
- [ ] 檢查所有外部依賴和服務
- [ ] 文檔化現有的 API 約定

#### 1.3 測試基線建立
```bash
# 運行現有測試，建立基線
pytest tests/ -v

# 記錄覆蓋率
pytest tests/ --cov=app --cov=bot
```

---

### 階段 2: 核心遷移 - AuthenticationSkill (1-2 天)

#### 2.1 創建 AuthenticationSkill

**源文件**: `bot/dialogs/sso_dialog.py`
**目標文件**: `app/services/skills/authentication_skill.py`

創建新文件 `app/services/skills/authentication_skill.py`:

```python
from typing import Dict, Any, Optional
from azure.identity import DefaultAzureCredential
from msgraph.core import GraphClient
from pydantic import BaseModel

from app.services.skills.base_skill import BaseSkill

class AuthTokenInfo(BaseModel):
    """認證令牌信息"""
    user_id: str
    access_token: str
    refresh_token: Optional[str]
    token_type: str
    expires_in: int
    scope: str


class AuthenticationSkill(BaseSkill):
    """
    認證技能 - 處理 SSO 和身份驗證
    
    遷移自: bot/dialogs/sso_dialog.py
    功能:
        - OAuth 2.0 SSO 流程
        - 令牌獲取和刷新
        - 用戶身份驗證
        - 會話管理
    """
    
    def __init__(self):
        super().__init__("authentication")
        self.credential = DefaultAzureCredential()
        self.graph_client: Optional[GraphClient] = None
        self.authenticated_users: Dict[str, AuthTokenInfo] = {}
    
    async def get_auth_prompt(self, connection_name: str = None) -> Dict[str, str]:
        """
        獲取認證提示信息
        
        遷移自: SSODialog.prompt_step()
        """
        return {
            "prompt": "請登入 (Please sign in)",
            "title": "登入 (Sign In)",
            "timeout": 300000,
            "connection_name": connection_name or "SSO"
        }
    
    async def authenticate_user(self, user_id: str, token: str) -> Dict[str, Any]:
        """
        認證用戶並存儲令牌
        
        遷移自: SSODialog.login_step()
        """
        try:
            self.authenticated_users[user_id] = AuthTokenInfo(
                user_id=user_id,
                access_token=token,
                refresh_token=None,
                token_type="Bearer",
                expires_in=3600,
                scope="default"
            )
            
            return {
                "status": "success",
                "message": f"用戶 {user_id} 已成功認證",
                "user_id": user_id
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"認證失敗: {str(e)}",
                "error": str(e)
            }
    
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """獲取認證用戶的個人資料"""
        if user_id not in self.authenticated_users:
            return {"status": "error", "message": "用戶未認證"}
        
        try:
            if not self.graph_client:
                self.graph_client = GraphClient(credential=self.credential)
            
            user = await self.graph_client.get("/me", content_type="application/json")
            return {
                "status": "success",
                "user_id": user_id,
                "profile": user
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"獲取個人資料失敗: {str(e)}"
            }
    
    async def refresh_token(self, user_id: str) -> Dict[str, Any]:
        """刷新用戶令牌"""
        if user_id not in self.authenticated_users:
            return {"status": "error", "message": "用戶未認證"}
        
        # 在實際應用中，應使用刷新令牌重新獲取訪問令牌
        return {
            "status": "success",
            "message": f"令牌已刷新",
            "user_id": user_id
        }
    
    async def logout_user(self, user_id: str) -> Dict[str, Any]:
        """登出用戶"""
        if user_id in self.authenticated_users:
            del self.authenticated_users[user_id]
            return {
                "status": "success",
                "message": f"用戶 {user_id} 已登出"
            }
        
        return {
            "status": "warning",
            "message": f"用戶 {user_id} 未登錄"
        }
    
    async def is_user_authenticated(self, user_id: str) -> bool:
        """檢查用戶是否已認證"""
        return user_id in self.authenticated_users
    
    def get_capability_description(self) -> Dict[str, Any]:
        """獲取技能的功能描述"""
        return {
            "name": "認證技能",
            "description": "處理用戶 SSO 身份驗證和令牌管理",
            "methods": {
                "get_auth_prompt": "獲取認證提示信息",
                "authenticate_user": "認證用戶並存儲令牌",
                "get_user_profile": "獲取認證用戶的個人資料",
                "refresh_token": "刷新用戶令牌",
                "logout_user": "登出用戶",
                "is_user_authenticated": "檢查用戶認證狀態"
            },
            "migration_notes": "遷移自 bot/dialogs/sso_dialog.py"
        }
```

#### 2.2 更新 M365AgentFramework 集成

修改 `app/core/m365_agent_framework.py`:

```python
from app.services.skills.authentication_skill import AuthenticationSkill

class M365AgentFramework:
    def __init__(self, config):
        # ... 現有代碼 ...
        self.authentication_skill = AuthenticationSkill()
        
        # 在 _initialize_framework 中添加
        self.skills["authentication"] = self.authentication_skill
```

---

### 階段 3: 主 Bot Logic 遷移 - BotCoreSkill (2-3 天)

#### 3.1 分析 MyBot 依賴

```
MyBot Handler 依賴:
  ├─ GenieService (保留)
  ├─ UserSession (保留)
  ├─ SSODialog (遷移為 AuthenticationSkill)
  ├─ DialogSet/DialogTurnStatus (轉換為 Skill 管理)
  └─ Conversation/UserState (遷移為會話管理)
```

#### 3.2 創建 BotCoreSkill

**源文件**: `bot/handlers/bot.py`
**目標文件**: `app/services/skills/bot_core_skill.py`

```python
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from app.services.skills.base_skill import BaseSkill
from app.services.genie import GenieService
from app.models.user_session import UserSession

class ConversationContext(BaseModel):
    """對話上下文"""
    user_id: str
    conversation_id: str
    channel_name: str
    authenticated: bool
    session: Optional[UserSession] = None


class BotCoreSkill(BaseSkill):
    """
    機器人核心技能
    
    遷移自: bot/handlers/bot.py
    功能:
        - 消息處理
        - 對話管理
        - Genie 服務集成
        - 用戶會話管理
    """
    
    def __init__(self, genie_service: GenieService):
        super().__init__("bot_core")
        self.genie_service = genie_service
        self.user_sessions: Dict[str, UserSession] = {}
        self.active_dialogs: Dict[str, Any] = {}
    
    async def on_message_activity(self, context: ConversationContext) -> Dict[str, Any]:
        """
        處理消息活動
        
        遷移自: MyBot.on_message_activity()
        """
        try:
            user_id = context.user_id
            message = context.session.last_message if context.session else ""
            
            # 調用 Genie 服務
            response = await self.genie_service.query(message)
            
            return {
                "status": "success",
                "response": response,
                "conversation_id": context.conversation_id
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"消息處理失敗: {str(e)}"
            }
    
    async def on_members_added_activity(self, context: ConversationContext) -> Dict[str, Any]:
        """
        處理成員加入活動
        
        遷移自: MyBot.on_members_added_activity()
        """
        try:
            return {
                "status": "success",
                "message": "新成員已加入對話",
                "user_id": context.user_id,
                "requires_authentication": not context.authenticated
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"成員加入處理失敗: {str(e)}"
            }
    
    async def start_conversation(self, user_id: str) -> Dict[str, Any]:
        """啟動新對話"""
        try:
            session = UserSession(user_id=user_id)
            self.user_sessions[user_id] = session
            return {
                "status": "success",
                "conversation_id": str(session.session_id),
                "user_id": user_id
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"啟動對話失敗: {str(e)}"
            }
    
    async def end_conversation(self, user_id: str) -> Dict[str, Any]:
        """結束對話"""
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
            return {
                "status": "success",
                "message": f"對話已結束"
            }
        
        return {
            "status": "warning",
            "message": f"用戶 {user_id} 沒有活躍對話"
        }
    
    def get_capability_description(self) -> Dict[str, Any]:
        return {
            "name": "機器人核心技能",
            "description": "處理消息、對話和 Genie 服務集成",
            "methods": {
                "on_message_activity": "處理消息",
                "on_members_added_activity": "處理成員加入",
                "start_conversation": "啟動對話",
                "end_conversation": "結束對話"
            },
            "migration_notes": "遷移自 bot/handlers/bot.py"
        }
```

---

### 階段 4: 測試 (2-3 天)

#### 4.1 單元測試

創建 `tests/unit/test_authentication_skill.py`:

```python
import pytest
from app.services.skills.authentication_skill import AuthenticationSkill


@pytest.fixture
def auth_skill():
    return AuthenticationSkill()


@pytest.mark.asyncio
async def test_authenticate_user(auth_skill):
    result = await auth_skill.authenticate_user("user123", "mock_token")
    assert result["status"] == "success"
    assert result["user_id"] == "user123"


@pytest.mark.asyncio
async def test_is_user_authenticated(auth_skill):
    await auth_skill.authenticate_user("user123", "mock_token")
    is_auth = await auth_skill.is_user_authenticated("user123")
    assert is_auth is True


@pytest.mark.asyncio
async def test_logout_user(auth_skill):
    await auth_skill.authenticate_user("user123", "mock_token")
    result = await auth_skill.logout_user("user123")
    assert result["status"] == "success"
    is_auth = await auth_skill.is_user_authenticated("user123")
    assert is_auth is False
```

#### 4.2 集成測試

```bash
# 測試 API 端點
pytest tests/integration/ -v

# 測試 Genie 服務集成
pytest tests/integration/test_bot_core_skill.py -v
```

---

### 階段 5: 部署 (1 天)

#### 5.1 更新依賴

```bash
# 確保所有新依賴已添加到 pyproject.toml
pip install -e .

# 驗證安裝
pip list | grep azure
```

#### 5.2 環境配置

`.env` 配置:

```env
# 現有配置保持不變
MICROSOFT_APP_ID=...
MICROSOFT_APP_PASSWORD=...

# 新增 M365 配置
AZURE_TENANT_ID=...
AZURE_CLIENT_ID=...
AZURE_CLIENT_SECRET=...
```

#### 5.3 逐步遷移

```bash
# 第 1 步: 在開發環境測試
pytest tests/ -v

# 第 2 步: 部署到測試環境
# ... 構建和部署步驟 ...

# 第 3 步: 驗證功能
curl http://localhost:8000/api/m365/skills
curl http://localhost:8000/api/m365/migration/report

# 第 4 步: 監控和回滾計劃
# ... 部署完成後監控日誌 ...
```

---

## 📝 檢查清單

### 準備階段
- [ ] 環境設置完成
- [ ] 現有測試通過
- [ ] 代碼審查完成
- [ ] 文檔記錄完成

### AuthenticationSkill 遷移
- [ ] 創建 AuthenticationSkill 類
- [ ] 實現所有必需的方法
- [ ] 更新 M365AgentFramework
- [ ] 創建單元測試
- [ ] 通過集成測試

### BotCoreSkill 遷移
- [ ] 創建 BotCoreSkill 類
- [ ] 遷移消息處理邏輯
- [ ] 遷移成員加入邏輯
- [ ] 集成 GenieService
- [ ] 更新 M365AgentFramework
- [ ] 創建單元測試
- [ ] 通過集成測試

### CommandSkill 和 IdentitySkill
- [ ] 分析命令處理邏輯
- [ ] 創建 CommandSkill
- [ ] 創建 IdentityManagementSkill
- [ ] 集成測試

### 測試和驗證
- [ ] 單元測試覆蓋 > 80%
- [ ] 集成測試通過
- [ ] 性能測試正常
- [ ] 安全測試通過

### 部署
- [ ] 更新 Docker 鏡像
- [ ] 部署到測試環境
- [ ] 部署到生產環境
- [ ] 監控和日誌記錄

---

## 🔗 相關資源

- [M365 Agent Framework 文檔](../MIGRATION_SKILL_GUIDE.md)
- [Bot Framework 遷移指南](../docs/bot_framework_migration.md)
- [Skill 基類參考](../app/services/skills/base_skill.py)
- [測試範本](../tests/)

---

**遷移開始日期**: 2026-02-08
**預計完成日期**: 2026-02-22
**狀態**: ⏳ 準備階段
