# Bot Framework 到 M365 Agent Framework 遷移 Skill

## 📋 概述

已實現完整的 Migration Skill，協助您從 Bot Framework 無縫遷移到 M365 Agent Framework。

## ✨ 主要功能

### 1. 項目分析
- 自動掃描代碼庫
- 評估複雜度（0-100 分）
- 估算遷移工作量
- 識別關鍵問題

### 2. 遷移規劃
- 生成詳細的遷移計劃
- 6 個結構化步驟
- 為每個步驟估算工作量
- 優先級設置

### 3. 代碼轉換
- 自動生成 Skill 模板
- 保留原始邏輯結構
- 包含遷移提示和檢查清單

### 4. 映射管理
- 追踪 Dialog → Skill 映射
- 監控遷移進度
- 生成進度報告

### 5. 學習資源
- 對比指南（Bot Framework vs M365）
- 代碼轉換示例
- 遷移檢查清單
- 最佳實踐

## 🚀 快速開始

### 方法 1: 使用 API

```bash
# 1. 分析項目
curl -X GET "http://localhost:8000/api/m365/migration/analyze?project_path=."

# 2. 查看遷移計劃
curl -X GET "http://localhost:8000/api/m365/migration/plan"

# 3. 生成 Skill 模板
curl -X POST "http://localhost:8000/api/m365/migration/generate-skill" \
  -H "Content-Type: application/json" \
  -d '{"dialog_name": "SSODialog", "dialog_type": "component"}'

# 4. 查看進度
curl -X GET "http://localhost:8000/api/m365/migration/report"
```

### 方法 2: 使用命令行工具

```bash
# 分析項目
python migration_utils.py analyze .

# 生成計劃
python migration_utils.py plan

# 生成 Skill 模板
python migration_utils.py generate SSODialog component

# 創建映射
python migration_utils.py map SSODialog dialog SSOSkill "SSO 驗證"

# 更新進度
python migration_utils.py update SSODialog in_progress

# 查看報告
python migration_utils.py report

# 顯示指南
python migration_utils.py guide

# 顯示檢查清單
python migration_utils.py checklist
```

### 方法 3: 在 Python 中使用

```python
from app.bot_instance import M365_AGENT_FRAMEWORK

# 分析項目
analysis = await M365_AGENT_FRAMEWORK.migration_skill.analyze_bot_framework_project(".")

# 創建計劃
plan = await M365_AGENT_FRAMEWORK.migration_skill.create_migration_plan(analysis)

# 生成 Skill
template = await M365_AGENT_FRAMEWORK.migration_skill.generate_skill_template("SSODialog")

# 創建映射
mapping = M365_AGENT_FRAMEWORK.migration_skill.create_mapping(
    "SSODialog", "dialog", "SSOSkill", "SSO 認證"
)
```

## 📊 API 端點列表

### 分析和規劃

```
GET /api/m365/migration/analyze          - 分析項目複雜度
GET /api/m365/migration/plan             - 獲取遷移計劃
```

### 代碼生成

```
POST /api/m365/migration/generate-skill  - 生成 Skill 模板
```

### 映射管理

```
POST /api/m365/migration/create-mapping  - 創建映射
PATCH /api/m365/migration/mapping/{name} - 更新映射狀態
GET /api/m365/migration/mapping-status   - 查看映射狀態
```

### 學習資源

```
GET /api/m365/migration/guide            - 遷移指南
GET /api/m365/migration/checklist        - 檢查清單
GET /api/m365/migration/report           - 遷移報告
```

## 📈 遷移複雜度評分

### 簡單 (< 30)
- 1-2 個 Dialog
- 1-3 個 Handler
- 工作量：1 天

### 中等 (30-60)
- 3-5 個 Dialog
- 4-6 個 Handler
- 工作量：3 天

### 複雜 (60-80)
- 6-10 個 Dialog
- 7+ 個 Handler
- 工作量：1 周

### 非常複雜 (> 80)
- 10+ 個 Dialog
- 複雜的狀態管理
- 工作量：1.5+ 周

## 🔍 分析結果示例

```json
{
  "analysis": {
    "total_files": 15,
    "dialog_count": 5,
    "handler_count": 8,
    "activity_handler_count": 1,
    "complexity_score": 65.5,
    "complexity_level": "複雜",
    "estimated_effort_hours": 40.0,
    "critical_issues": [
      "複雜的多步驟 Dialog",
      "OAuth 和 SSO 集成",
      "自定義狀態管理"
    ],
    "warnings": [
      "需要重新評估異步流程",
      "舊版依賴項可能需要更新",
      "部分 API 無直接對應"
    ],
    "recommendations": [
      "將 Dialog 轉換為 Skill",
      "重構事件處理流程",
      "整合 Microsoft Graph API",
      "實施完整的單元測試"
    ]
  }
}
```

## 📝 遷移計劃示例

```
步驟 1: 依賴項更新
  工作量: 2 小時
  優先級: 高
  可交付物: 更新的 pyproject.toml, 安裝測試報告

步驟 2: 創建 Skill 結構
  工作量: 12 小時
  優先級: 高
  可交付物: BaseSkill 模板, Skills 目錄結構

步驟 3: 遷移身份驗證
  工作量: 8 小時
  優先級: 高
  可交付物: 認證 Skill, 測試案例

步驟 4: 重構事件處理
  工作量: 12 小時
  優先級: 高
  可交付物: 功能 Skills, 單元測試

步驟 5: 集成測試
  工作量: 6 小時
  優先級: 高
  可交付物: 測試報告, 缺陷清單

步驟 6: 部署
  工作量: 2 小時
  優先級: 高
  可交付物: 部署檢查清單, 上線報告

總工作量: 40 小時 (~5 天)
```

## 📚 文檔資源

| 文件 | 描述 |
|------|------|
| [bot_framework_migration.md](./docs/bot_framework_migration.md) | 完整的遷移指南 |
| [m365_agent_framework.md](./docs/m365_agent_framework.md) | M365 Agent Framework 使用指南 |
| [M365_SETUP.md](./docs/M365_SETUP.md) | 環境設置和配置 |

## 🛠️ 遷移工具

### migration_utils.py

命令行工具，簡化遷移過程：

```bash
# 分析項目
python migration_utils.py analyze <project_path>

# 生成計劃
python migration_utils.py plan

# 生成 Skill
python migration_utils.py generate <dialog_name> [type]

# 管理映射
python migration_utils.py map <source> <type> <target> <desc>
python migration_utils.py update <source> <status>

# 查看資源
python migration_utils.py guide      # 顯示遷移指南
python migration_utils.py checklist  # 顯示檢查清單
python migration_utils.py report     # 顯示進度報告
```

## ✅ 遷移檢查清單

```
□ 運行項目分析
□ 查看遷移計劃
□ 識別所有 Dialog 和 Handler
□ 為每個 Dialog 創建映射
□ 生成 Skill 模板
□ 實現 Skill 邏輯
□ 編寫單元測試
□ 編寫集成測試
□ 更新映射狀態
□ 性能優化
□ 文檔更新
□ 用戶驗收測試
□ 部署到生產
□ 監控和維護
```

## 🔗 集成示例

### 在 Bot Handler 中使用

```python
from app.bot_instance import M365_AGENT_FRAMEWORK

class MyBot(ActivityHandler):
    async def on_message_activity(self, turn_context: TurnContext):
        # 使用遷移 Skill 幫助用戶理解遷移
        if "migration" in turn_context.activity.text:
            guide = M365_AGENT_FRAMEWORK.migration_skill.generate_comparison_guide()
            await turn_context.send_activity(guide)
```

### 在 FastAPI 中使用

```python
from app.api.migration import router as migration_router

app.include_router(migration_router, prefix="/api")

# 現在可以訪問所有遷移 API 端點
# GET /api/m365/migration/analyze
# POST /api/m365/migration/generate-skill
# 等等...
```

## 🎯 後續步驟

1. **運行分析** - 評估當前代碼庫
2. **查看計劃** - 了解遷移步驟
3. **學習指南** - 參考代碼轉換示例
4. **生成模板** - 為每個 Dialog 生成 Skill
5. **實現邏輯** - 填充具體的業務邏輯
6. **測試** - 編寫完整的測試覆蓋
7. **部署** - 分階段部署到生產
8. **監控** - 監控性能和錯誤

## 📞 支持

如有問題，請參考：

1. [遷移指南](./docs/bot_framework_migration.md)
2. [M365 Agent Framework 文檔](./docs/m365_agent_framework.md)
3. [實現檢查清單](./IMPLEMENTATION_CHECKLIST.md)

---

**版本**: 1.0  
**狀態**: ✅ 完整  
**最後更新**: 2026-02-08
