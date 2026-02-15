# M365 Agent Framework 代碼移除摘要

**日期**：2026-02-16
**決策依據**：POC 評估報告 + 架構分析

## 移除原因

### 1. SDK 不成熟（技術因素）

**Python SDK 0.7.0 狀態**：
- ❌ 僅包含 Activity Protocol 類型定義
- ❌ 缺少核心 Agent Framework（AgentApplication, Storage, Adapters）
- ❌ 官方文檔與實際 SDK 內容不符
- ⏰ 預計需要等待至 2026 Q4 或 2027 Q1 才能達到生產就緒狀態

**參考**：`docs/m365_agents_sdk_evaluation_report.md`

### 2. 0% 整合度（架構因素）

**實際使用情況**：
- M365 API 端點 (`/api/m365/*`) 從未被 Bot 主流程調用
- M365AgentFramework 在 Bot 中僅作為可選參數傳遞，但從未真正使用
- 唯一的整合嘗試（Graph API 取得用戶 email）已在 SSO 處理中被注釋

**架構分析結論**：
> M365 Framework 實質上是**僵屍代碼**，名存實亡，未真正整合。

### 3. 維護負擔（資源因素）

- 增加代碼庫複雜度
- 需要維護但無實際價值
- 混淆新開發者對架構的理解

## 已移除的檔案

### 核心模組
1. `app/core/m365_agent_framework.py` - M365 Agent Framework 協調器
2. `app/services/m365_agent.py` - Microsoft Graph API 客戶端
3. `app/api/m365_agent.py` - M365 專用 API 端點

### 修改的檔案

#### app/bot_instance.py
**變更**：
- 移除 `from app.core.m365_agent_framework import M365AgentFramework`
- 移除 M365AgentFramework 初始化邏輯
- MyBot 建構時不再傳遞 `m365_agent_framework` 參數

#### bot/handlers/bot.py
**變更**：
- 移除 `from app.core.m365_agent_framework import M365AgentFramework`
- 移除 `m365_agent_framework` 建構參數
- 移除 SSO 處理中的 Graph API 調用（使用 placeholder email）

**影響**：
- 用戶 email 現在使用 `{name}@example.com` 格式
- 不影響核心 Genie 查詢功能

#### app/main.py
**變更**：
- 移除 `from app.api.m365_agent import router as m365_router`
- 移除路由註冊 `app.include_router(m365_router, ...)`

## 保留的文檔（歷史參考）

以下文檔保留在版本控制中供未來參考：

1. **POC 評估文檔**：
   - `docs/m365_agents_sdk_evaluation_report.md`
   - `docs/m365_agents_sdk_poc_plan.md`
   - `poc/POC_STATUS.md`
   - `poc/FINDINGS_SUMMARY.md`

2. **遷移計畫文檔**：
   - `migration_archive/` 目錄下的所有文檔
   - `docs/bot_framework_migration.md`
   - `docs/m365_agent_framework.md`

3. **README 和專案指南**：
   - `CLAUDE.md` - 已更新為反映當前架構
   - `README.md` - 包含專案概述

## 未來遷移計畫

### 何時重新評估

**條件**：
1. Microsoft 365 Agents SDK Python 版本達到 **1.0+**
2. SDK 包含完整的 Agent Framework 功能：
   - AgentApplication
   - Storage adapters
   - Activity handlers
   - Authentication flows
3. 官方文檔與實際 SDK 內容一致
4. 社群有成功的 Python 實作案例

**預計時間**：2026 Q4 或 2027 Q1

### 重新評估步驟

1. **檢查 SDK 版本**：
   ```bash
   pip show agents-sdk
   ```

2. **查看 Release Notes**：
   - https://github.com/microsoft/agents-sdk

3. **重新執行 POC**：
   - 參考 `docs/m365_agents_sdk_poc_plan.md`
   - 驗證核心功能可用性

4. **評估遷移成本**：
   - 估算開發時間
   - 評估風險
   - 規劃遷移策略

## 當前架構優勢

移除 M365 代碼後，當前架構更加：

1. **清晰** - 單一技術棧（Bot Framework SDK）
2. **穩定** - 無實驗性代碼
3. **可維護** - 減少複雜度
4. **文檔化** - 架構決策有明確記錄

## 決策批准

- **決策日期**：2026-02-16
- **決策者**：開發團隊（基於技術評估）
- **決策類型**：可逆（SDK 成熟後可重新整合）
- **風險等級**：低（移除的是未使用的代碼）

## 相關文檔

- [M365 Agents SDK 評估報告](m365_agents_sdk_evaluation_report.md)
- [POC 測試計畫](m365_agents_sdk_poc_plan.md)
- [認證系統文檔](authentication.md)
- [專案指南 (CLAUDE.md)](../CLAUDE.md)

---

**注意**：本文檔記錄了重要的架構決策。如需恢復 M365 整合，請參考本文檔的「未來遷移計畫」章節。
