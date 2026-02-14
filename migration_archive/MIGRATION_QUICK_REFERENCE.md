# Migration Skill - 快速參考卡片

## 🎯 一句話總結
一套完整的遷移工具和 API，幫助您從 Bot Framework 無縫遷移到 M365 Agent Framework。

---

## 📊 關鍵數字

| 指標 | 值 |
|------|-----|
| 新增 Skill | 1 個 (MigrationSkill) |
| API 端點 | 8 個 |
| 支持方式 | 3 種 (API, CLI, Python) |
| 複雜度評分範圍 | 0-100 分 |
| 遷移步驟 | 6 個 |
| 工作量範圍 | 1 天 - 1.5+ 周 |

---

## 🚀 30 秒快速開始

```bash
# 1. 分析項目
python migration_utils.py analyze .

# 2. 查看計劃
python migration_utils.py plan

# 3. 生成 Skill
python migration_utils.py generate YourDialog

# 4. 查看報告
python migration_utils.py report
```

---

## 🎮 常用命令

### 分析和規劃
```bash
# 分析項目複雜度
python migration_utils.py analyze .

# 生成遷移計劃
python migration_utils.py plan
```

### 代碼生成
```bash
# 生成 Skill 模板
python migration_utils.py generate DialogName [type]

# 示例
python migration_utils.py generate SSODialog component
python migration_utils.py generate MyDialog waterfall
```

### 映射管理
```bash
# 創建映射
python migration_utils.py map SourceName type TargetSkill "description"

# 更新狀態
python migration_utils.py update SourceName status

# 示例
python migration_utils.py map SSODialog dialog SSOSkill "SSO認證"
python migration_utils.py update SSODialog in_progress
python migration_utils.py update SSODialog completed
```

### 資源和報告
```bash
# 顯示遷移指南
python migration_utils.py guide

# 顯示檢查清單
python migration_utils.py checklist

# 生成報告
python migration_utils.py report
```

---

## 🌐 REST API 速查表

### 分析
```
GET /api/m365/migration/analyze?project_path=.
```

### 規劃
```
GET /api/m365/migration/plan
```

### 代碼生成
```
POST /api/m365/migration/generate-skill
Body: {"dialog_name": "Name", "dialog_type": "type"}
```

### 映射
```
POST /api/m365/migration/create-mapping
Body: {"source_name": "", "source_type": "", ...}

PATCH /api/m365/migration/mapping/{source_name}
Body: {"status": "in_progress"}

GET /api/m365/migration/mapping-status
```

### 資源
```
GET /api/m365/migration/guide
GET /api/m365/migration/checklist
GET /api/m365/migration/report
```

---

## 🐍 Python API 速查表

```python
from app.bot_instance import M365_AGENT_FRAMEWORK

# 分析
analysis = await M365_AGENT_FRAMEWORK.migration_skill.analyze_bot_framework_project(".")

# 規劃
plan = await M365_AGENT_FRAMEWORK.migration_skill.create_migration_plan(analysis)

# 生成
template = await M365_AGENT_FRAMEWORK.migration_skill.generate_skill_template("Dialog")

# 映射
mapping = M365_AGENT_FRAMEWORK.migration_skill.create_mapping(
    "SSODialog", "dialog", "SSOSkill", "description"
)

# 更新狀態
success = M365_AGENT_FRAMEWORK.migration_skill.update_mapping_status("SSODialog", "completed")

# 獲取狀態
status = M365_AGENT_FRAMEWORK.migration_skill.get_mapping_status()

# 報告
report = M365_AGENT_FRAMEWORK.migration_skill.generate_migration_report()
```

---

## 📊 複雜度對應

| 評分 | 等級 | 工作量 | 示例 |
|------|------|--------|------|
| < 30 | 簡單 | 1 天 | 1-2 Dialog |
| 30-60 | 中等 | 3 天 | 3-5 Dialog |
| 60-80 | 複雜 | 1 周 | 6-10 Dialog |
| > 80 | 非常複雜 | 1.5+ 周 | 10+ Dialog |

---

## 📈 遷移流程圖

```
分析            規劃            開發            測試            部署
 ┌─────────────┬─────────────┬─────────────┬─────────────┬─────────┐
 │ 評估複雜度  │ 生成計劃    │ 實現 Skill  │ 單位/集成   │ 上線   │
 │ 識別問題    │ 計算工作量  │ 編寫代碼    │ 性能測試    │ 監控   │
 │ 提出建議    │ 設定優先級  │ 單元測試   │ 驗收測試    │       │
 └─────────────┴─────────────┴─────────────┴─────────────┴─────────┘
      ↓              ↓              ↓              ↓              ↓
  analyze()      plan()       generate_skill()  (manual)       (manual)
```

---

## ⚡ 常見操作

### 遷移一個 Dialog

```bash
# 1. 創建映射
python migration_utils.py map SSODialog dialog SSOSkill "SSO認證"

# 2. 標記為進行中
python migration_utils.py update SSODialog in_progress

# 3. 生成模板
python migration_utils.py generate SSODialog

# 4. 編輯 SSOSkill.py（實現業務邏輯）

# 5. 標記為完成
python migration_utils.py update SSODialog completed

# 6. 查看進度
python migration_utils.py report
```

---

## 💾 重要文件位置

| 文件 | 功能 |
|------|------|
| `app/services/skills/migration_skill.py` | Skill 核心實現 |
| `app/api/migration.py` | API 路由 |
| `migration_utils.py` | 命令行工具 |
| `docs/bot_framework_migration.md` | 詳細指南 |
| `MIGRATION_SKILL_GUIDE.md` | Skill 使用指南 |

---

## 📚 文檔導航

```
快速開始 → MIGRATION_IMPLEMENTATION_SUMMARY.md (本文件)
   ↓
詳細指南 → MIGRATION_SKILL_GUIDE.md
   ↓
代碼遷移 → docs/bot_framework_migration.md
   ↓
API 文檔 → http://localhost:8000/docs
   ↓
M365 框架 → docs/m365_agent_framework.md
```

---

## ✅ 初次使用檢查清單

```
□ 安裝依賴項: pip install -e .
□ 配置環境變數: .env
□ 啟動應用: uvicorn app.main:app --reload
□ 訪問 API 文檔: http://localhost:8000/docs
□ 運行分析: python migration_utils.py analyze .
□ 查看報告: python migration_utils.py report
□ 閱讀指南: python migration_utils.py guide
□ 生成第一個 Skill: python migration_utils.py generate DialogName
```

---

## 🔍 Debug 提示

```bash
# 查看詳細的分析結果
curl -X GET "http://localhost:8000/api/m365/migration/analyze?project_path=." | python -m json.tool

# 查看遷移計劃
curl -X GET "http://localhost:8000/api/m365/migration/plan" | python -m json.tool

# 查看當前映射狀態
curl -X GET "http://localhost:8000/api/m365/migration/mapping-status" | python -m json.tool

# 查看完整報告
curl -X GET "http://localhost:8000/api/m365/migration/report" | python -m json.tool
```

---

## 🎓 學習路徑

1. 閱讀本卡片 (5 分鐘) ← 你在這裡
2. 閱讀 MIGRATION_SKILL_GUIDE.md (10 分鐘)
3. 運行 `python migration_utils.py analyze .` (1 分鐘)
4. 查看 `python migration_utils.py report` (2 分鐘)
5. 閱讀 `python migration_utils.py guide` (10 分鐘)
6. 生成第一個 Skill (5 分鐘)
7. 閱讀完整指南 (30 分鐘)
8. 開始遷移! 🚀

---

## 📞 快速幫助

| 問題 | 解決方案 |
|------|--------|
| 不知道從何開始 | 運行 `python migration_utils.py analyze .` |
| 不知道有多複雜 | 查看分析結果中的 `complexity_score` |
| 不知道要做什麼 | 運行 `python migration_utils.py plan` |
| 不知道如何編寫代碼 | 運行 `python migration_utils.py generate DialogName` |
| 不知道進度 | 運行 `python migration_utils.py report` |
| 需要指導 | 運行 `python migration_utils.py guide` |

---

## 🌟 核心特性

✨ **完全自動化**: 自動分析、規劃、生成  
🎯 **精確估算**: 基於代碼複雜度的工作量估算  
📊 **詳細報告**: 完整的進度追踪和統計  
🛠️ **易用工具**: CLI、API、Python 三種方式  
📚 **完整文檔**: 指南、示例、檢查清單  

---

**版本**: 1.0 | **狀態**: ✅ 完整 | **最後更新**: 2026-02-08
