# Bot Framework 到 M365 Agent Framework 遷移指南

## 📋 目錄

1. [概述](#概述)
2. [遷移階段](#遷移階段)
3. [逐步指南](#逐步指南)
4. [代碼轉換示例](#代碼轉換示例)
5. [常見問題](#常見問題)
6. [工具和資源](#工具和資源)

---

## 概述

### 為什麼要遷移？

**Bot Framework 的局限**:
- 侷限於聊天界面
- 狀態管理複雜
- 對 Microsoft 365 集成有限

**M365 Agent Framework 的優勢**:
- 完整的 Microsoft 365 集成
- 更靈活的架構
- 更好的異步支持
- 更強大的 API 訪問

### 遷移時間表

根據複雜度：
- **簡單** (複雜度 < 30): 1 天
- **中等** (複雜度 30-60): 3 天
- **複雜** (複雜度 60-80): 1 周
- **非常複雜** (複雜度 > 80): 1.5 周以上

---

## 遷移階段

### 階段 1: 評估 (Assessment)

使用遷移 Skill 分析現有代碼：

```bash
GET /api/m365/migration/analyze?project_path=/path/to/project
```

分析結果包括：
- 總文件數
- Dialog 和 Handler 數量
- 複雜度評分（0-100）
- 估算工作量
- 關鍵問題和建議

### 階段 2: 規劃 (Planning)

基於分析結果創建遷移計劃：

```bash
GET /api/m365/migration/plan
```

計劃包括：
- 6 個主要步驟
- 每個步驟的工作量
- 優先級和可交付成果

### 階段 3: 重構 (Refactoring)

逐個轉換 Dialog 為 Skill：

```bash
POST /api/m365/migration/generate-skill
{
  "dialog_name": "SSODialog",
  "dialog_type": "component"
}
```

### 階段 4: 測試 (Testing)

執行完整的測試覆蓋：
- 單元測試
- 集成測試
- 性能測試

### 階段 5: 部署 (Deployment)

分階段部署到生產環境。

---

## 逐步指南

### 步驟 1: 環境準備

```bash
# 1. 確保已安裝所有依賴項
pip install -e .

# 2. 驗證安裝
python -c "from app.core.m365_agent_framework import M365AgentFramework; print('OK')"
```

### 步驟 2: 分析現有項目

```bash
# 發送分析請求
curl -X GET "http://localhost:8000/api/m365/migration/analyze?project_path=."

# 檢查輸出，記下複雜度評分和建議
```

### 步驟 3: 創建遷移計劃

```bash
# 獲取詳細的遷移計劃
curl -X GET "http://localhost:8000/api/m365/migration/plan"

# 查看估算的工作量和每個步驟的詳細信息
```

### 步驟 4: 建立 Skill 映射

```bash
# 為每個 Dialog 創建映射
curl -X POST "http://localhost:8000/api/m365/migration/create-mapping" \
  -H "Content-Type: application/json" \
  -d '{
    "source_name": "SSODialog",
    "source_type": "dialog",
    "target_skill_name": "SSOSkill",
    "description": "SSO 驗證邏輯",
    "complexity": "high"
  }'
```

### 步驟 5: 生成 Skill 代碼

```bash
# 生成 Skill 模板
curl -X POST "http://localhost:8000/api/m365/migration/generate-skill" \
  -H "Content-Type: application/json" \
  -d '{
    "dialog_name": "SSODialog",
    "dialog_type": "component"
  }'

# 複製生成的代碼，進行定制
```

### 步驟 6: 實現 Skill

參考生成的模板，實現具體的業務邏輯。

### 步驟 7: 編寫測試

```python
# tests/unit/test_sso_skill.py
import pytest
from app.services.skills.sso_skill import SSOSkill

@pytest.mark.asyncio
async def test_sso_skill_execute():
    skill = SSOSkill(mock_graph_service)
    result = await skill.execute()
    assert result["status"] == "success"
```

### 步驟 8: 更新映射狀態

```bash
# 標記為進行中
curl -X PATCH "http://localhost:8000/api/m365/migration/mapping/SSODialog" \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'

# 完成時標記為已完成
curl -X PATCH "http://localhost:8000/api/m365/migration/mapping/SSODialog" \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'
```

### 步驟 9: 查看進度

```bash
# 檢查遷移進度
curl -X GET "http://localhost:8000/api/m365/migration/mapping-status"

# 查看完整報告
curl -X GET "http://localhost:8000/api/m365/migration/report"
```

---

## 代碼轉換示例

### 示例 1: SSO Dialog 遷移

#### 原始 Bot Framework 代碼

```python
# bot/dialogs/sso_dialog.py
from botbuilder.dialogs import ComponentDialog, OAuthPrompt

class SSODialog(ComponentDialog):
    def __init__(self, connection_name: str):
        super().__init__("SSODialog")
        
        self.add_dialog(
            OAuthPrompt(
                OAuthPrompt.__name__,
                OAuthPromptSettings(
                    connection_name=connection_name,
                    text="請登入",
                    title="登入",
                    timeout=300000,
                ),
            )
        )
        
        self.add_dialog(
            WaterfallDialog("MyWaterfall", [
                self.prompt_for_token,
                self.process_token,
            ])
        )
    
    async def prompt_for_token(self, step_context):
        return await step_context.begin_dialog(OAuthPrompt.__name__)
    
    async def process_token(self, step_context):
        token_response = step_context.result
        # 處理 token
```

#### 遷移到 M365 Skill

```python
# app/services/skills/sso_skill.py
from app.services.m365_agent import M365AgentService

class SSOSkill:
    def __init__(self, graph_service: M365AgentService):
        self.graph_service = graph_service
    
    async def execute(self, user_id: str = "me") -> Dict[str, Any]:
        """執行 SSO 驗證流程"""
        try:
            # 第一步：獲取用戶個人資料
            profile = await self.graph_service.get_user_profile(user_id)
            
            # 第二步：驗證用戶身份
            if "error" not in profile:
                return {
                    "status": "authenticated",
                    "profile": profile
                }
            else:
                return {
                    "status": "error",
                    "message": "驗證失敗"
                }
        except Exception as e:
            logger.error(f"SSO 驗證失敗: {str(e)}")
            return {"status": "error", "error": str(e)}
```

### 示例 2: 命令處理轉換

#### 原始 Bot Framework

```python
# bot/handlers/commands.py
async def handle_special_commands(user_input, turn_context):
    if user_input.lower() == "help":
        await turn_context.send_activity("幫助信息...")
    elif user_input.lower() == "status":
        status = await check_status()
        await turn_context.send_activity(f"狀態: {status}")
```

#### 遷移到 M365 Skill

```python
# app/services/skills/commands_skill.py
class CommandsSkill:
    async def handle_help_command(self) -> Dict[str, Any]:
        """處理幫助命令"""
        return {
            "status": "success",
            "message": "幫助信息...",
            "commands": ["help", "status", "list"]
        }
    
    async def handle_status_command(self) -> Dict[str, Any]:
        """處理狀態命令"""
        status = await self.check_system_status()
        return {
            "status": "success",
            "system_status": status
        }
```

---

## 常見問題

### Q: 遷移期間可以同時運行兩個框架嗎？

**A**: 可以。建議建立一個路由層來決定使用哪個框架，逐漸過渡。

### Q: 如何處理複雜的 Dialog 邏輯？

**A**: 
1. 將複雜 Dialog 分解為多個簡單的 Skill
2. 使用 M365AgentFramework 的 execute_skill 方法協調
3. 實施適當的錯誤處理和重試邏輯

### Q: OAuth 配置如何遷移？

**A**: 
1. 使用 Azure AD 應用註冊
2. 配置 Microsoft Graph API 權限
3. 在 M365AgentService 中使用 DefaultAzureCredential

### Q: 如何測試遷移的代碼？

**A**:
1. 編寫單元測試（使用 Mock Graph Service）
2. 編寫集成測試（使用真實 Graph API）
3. 使用 Swagger UI 進行端點測試

### Q: 性能會有變化嗎？

**A**: M365 Agent Framework 通常性能更好：
- 更好的異步支持
- 減少了層級結構
- 更高效的 API 調用

---

## 工具和資源

### 可用的遷移工具

#### 1. 分析工具

```bash
GET /api/m365/migration/analyze
```

評估現有代碼的複雜度。

#### 2. 計劃生成器

```bash
GET /api/m365/migration/plan
```

基於分析結果生成詳細計劃。

#### 3. 代碼生成器

```bash
POST /api/m365/migration/generate-skill
```

為 Dialog 生成 Skill 模板。

#### 4. 映射管理

```bash
POST /api/m365/migration/create-mapping
PATCH /api/m365/migration/mapping/{source_name}
GET /api/m365/migration/mapping-status
```

管理 Dialog 到 Skill 的映射。

#### 5. 指南和檢查清單

```bash
GET /api/m365/migration/guide
GET /api/m365/migration/checklist
```

獲取遷移指南和檢查清單。

#### 6. 報告生成

```bash
GET /api/m365/migration/report
```

生成完整的遷移報告。

### 文檔資源

- [M365 Agent Framework 完整指南](./m365_agent_framework.md)
- [M365 設置指南](./M365_SETUP.md)
- [Microsoft Graph API 文檔](https://docs.microsoft.com/graph/)
- [Azure AD 開發指南](https://docs.microsoft.com/azure/active-directory/develop/)

### 測試工具

- **Postman**: 導入 API 集合進行測試
- **Swagger UI**: 訪問 http://localhost:8000/docs
- **Python unittest**: 編寫測試用例
- **pytest**: 異步測試支持

---

## 遷移檢查清單

使用以下檢查清單跟踪遷移進度：

```
基礎設施準備
□ 安裝所有依賴項
□ 配置環境變數
□ 設置 Azure AD 應用

分析和規劃
□ 運行項目分析
□ 生成遷移計劃
□ 識別關鍵問題

開發
□ 建立 Skill 映射
□ 生成 Skill 模板
□ 實現 Skill 邏輯
□ 編寫單元測試
□ 編寫集成測試

驗證
□ 執行測試套件
□ 性能基準測試
□ 安全審查
□ 文檔審查

部署
□ 部署到開發環境
□ 部署到測試環境
□ 用戶驗收測試
□ 部署到生產環境
□ 監控和維護
```

---

## 支持

如需幫助，請參考：

1. [M365 Agent Framework 文檔](./m365_agent_framework.md)
2. [遷移指南](../docs/bot_framework_migration.md) （本文件）
3. [實現檢查清單](../IMPLEMENTATION_CHECKLIST.md)

---

**版本**: 1.0  
**最後更新**: 2026-02-08  
**狀態**: ✅ 完整
