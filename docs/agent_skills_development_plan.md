# Agent Skills 開發計畫

本文檔分析 DatabricksGenieBOT 專案中適合開發成 Anthropic Agent Skills 的功能模組。

## 什麼是 Anthropic Agent Skills？

Anthropic Agent Skills 是可以透過 `npx skills` 管理的模組化包，用於擴展 Claude Code 的能力。Skills 可以：
- 提供專業領域知識和工作流程
- 分享給 Claude Code 生態系統的其他用戶
- 透過 https://skills.sh/ 發現和安裝

## 功能模組評估

### 🟢 高優先級：非常適合做成 Skills

#### 1. **Databricks Genie Integration Skill**
- **檔案**: `app/services/genie.py` (517 行)
- **功能**:
  - Databricks Genie API 完整封裝
  - 對話建立、訊息傳送、結果解析
  - 查詢效能指標收集
  - 支援 SQL 查詢和自然語言互動
- **通用性**: ⭐⭐⭐⭐⭐ 極高
- **適用場景**: 任何需要整合 Databricks Genie 的專案
- **預估使用者**:
  - 資料科學家和分析師
  - 使用 Databricks 的開發團隊
  - BI 工具開發者
- **建議 Skill 名稱**: `databricks-genie-api`

**Skill 提供的能力**：
```markdown
- 建立和管理 Genie 對話
- 傳送自然語言查詢
- 解析 SQL 查詢結果（表格、圖表）
- 查詢效能監控
- 錯誤處理和重試機制
```

---

#### 2. **Data Chart Generator Skill**
- **檔案**: `app/utils/chart_analyzer.py` (270 行), `bot/cards/chart_cards.py`
- **功能**:
  - 智慧圖表類型選擇（長條圖、圓餅圖、折線圖、散點圖）
  - 基於 Matplotlib/Seaborn 的專業圖表生成
  - 支援中文標籤
  - 自動資料類型檢測
- **通用性**: ⭐⭐⭐⭐⭐ 極高
- **適用場景**: 任何需要資料視覺化的專案
- **預估使用者**:
  - 資料分析工具開發者
  - 報表生成系統
  - Dashboard 開發者
- **建議 Skill 名稱**: `data-chart-generator`

**Skill 提供的能力**：
```markdown
- 自動選擇最適合的圖表類型
- 生成高品質資料視覺化圖表
- 支援多種圖表類型（bar, pie, line, scatter）
- 中文和多語言支援
- 圖表自訂樣式
```

---

#### 3. **Teams Bot SSO Authentication Skill**
- **檔案**: `app/utils/email_extractor.py`, `bot/dialogs/sso_dialog.py`
- **功能**:
  - Teams Bot SSO 認證流程
  - JWT Token 解碼和 email 提取
  - Microsoft Graph API 整合
  - 多來源 email 提取策略
- **通用性**: ⭐⭐⭐⭐ 高
- **適用場景**: Teams Bot 開發
- **預估使用者**:
  - Teams Bot 開發者
  - 企業應用整合團隊
- **建議 Skill 名稱**: `teams-bot-sso-auth`

**Skill 提供的能力**：
```markdown
- 實作 Teams SSO 認證流程
- 從 JWT Token 提取用戶資訊
- 整合 Microsoft Graph API
- 提供認證狀態管理
```

---

### 🟡 中優先級：適合但需調整

#### 4. **Microsoft Graph API Client Skill**
- **檔案**: `app/services/graph.py`
- **功能**:
  - Graph API 認證和呼叫
  - 用戶個人資料取得
- **通用性**: ⭐⭐⭐⭐ 高
- **問題**: 功能較基本，市面上可能已有類似 skills
- **建議**: 整合到 `teams-bot-sso-auth` skill 中，而非獨立 skill

---

#### 5. **LRU + TTL Cache System Skill**
- **檔案**: `app/utils/cache_utils.py`
- **功能**:
  - LRU + TTL 混合快取
  - 裝飾器模式（@cached_query, @cached_chart）
  - 快取統計
- **通用性**: ⭐⭐⭐⭐ 高
- **問題**: 功能較通用，可能與現有快取庫重複
- **建議**: 作為「最佳實踐範例」而非完整 skill

---

### 🔴 低優先級：不適合做成 Skills

#### 6. **Teams Bot Core Infrastructure**
- **檔案**: `bot/handlers/bot.py`, `app/core/adapter.py`
- **原因**: 太專案特定，與 Bot Framework SDK 緊密耦合
- **建議**: 保留在專案內部

#### 7. **Configuration Management**
- **檔案**: `app/core/config.py`
- **原因**: 每個專案的配置都不同
- **建議**: 不適合做成 skill

---

## 建議的 Skills 開發順序

### 階段 1：核心 Databricks Skill（1 週）
**Skill**: `databricks-genie-api`
- 提取 `app/services/genie.py` 核心邏輯
- 建立獨立的 skill 專案結構
- 撰寫文檔和使用範例
- 發布到 GitHub 並註冊到 skills.sh

**預期影響**: 最高價值，適用於所有 Databricks 用戶

---

### 階段 2：圖表生成 Skill（4-5 天）
**Skill**: `data-chart-generator`
- 提取圖表生成邏輯
- 移除 Teams 相關依賴
- 建立通用介面
- 提供多種輸出格式（PNG, SVG, Base64）

**預期影響**: 高價值，適用於所有需要資料視覺化的專案

---

### 階段 3：Teams SSO Skill（3-4 天）
**Skill**: `teams-bot-sso-auth`
- 整合 SSO 認證流程
- 整合 email 提取邏輯
- 整合 Graph API 客戶端
- 提供完整的認證範例

**預期影響**: 中等價值，專門針對 Teams Bot 開發者

---

## Skill 專案結構建議

每個 skill 應包含：

```
skill-name/
├── README.md                 # Skill 說明和使用指南
├── skill.json               # Skill 設定檔（metadata）
├── prompt.md                # Skill 的核心提示詞
├── examples/                # 使用範例
│   ├── basic_usage.py
│   └── advanced_usage.py
├── src/                     # 核心程式碼
│   ├── __init__.py
│   └── main.py
├── tests/                   # 測試
│   └── test_skill.py
├── docs/                    # 詳細文檔
│   ├── api.md
│   └── troubleshooting.md
└── LICENSE                  # 授權條款
```

---

## 技術考量

### 依賴管理
- **最小化依賴**: 只包含必要的依賴包
- **版本鎖定**: 明確指定依賴版本
- **可選依賴**: 將進階功能設為可選依賴

### 錯誤處理
- **清晰的錯誤訊息**: 幫助使用者快速除錯
- **優雅降級**: 當某些功能不可用時仍能運作
- **詳細日誌**: 提供除錯資訊

### 文檔品質
- **快速開始指南**: 5 分鐘內能跑起來
- **API 文檔**: 清楚的介面說明
- **最佳實踐**: 提供使用建議
- **常見問題**: FAQ 和故障排除

---

## 發布和推廣策略

### 1. GitHub 倉庫設定
- 建立清楚的 README
- 添加 Topics: `claude-code`, `agent-skills`, `databricks`, `data-visualization`
- 設定 GitHub Actions 自動測試
- 提供 Issue 和 PR 模板

### 2. 註冊到 skills.sh
- 提交 skill 到 skills 目錄
- 確保 metadata 正確
- 提供清楚的描述和標籤

### 3. 推廣
- 在 Databricks 社群分享
- 撰寫部落格文章介紹使用方式
- 在 Claude Code 社群推廣

---

## 成本效益分析

### 投資成本
- **開發時間**: 2-3 週（3 個 skills）
- **維護時間**: 每月 2-4 小時（bug 修復、更新）
- **文檔撰寫**: 1 週

### 預期效益
- **社群貢獻**: 幫助其他開發者
- **專案可見度**: 提升專案和團隊知名度
- **程式碼品質**: 迫使模組化和最佳實踐
- **可重用性**: 未來專案可直接使用

### ROI 評估
- **高價值**: `databricks-genie-api` (潛在使用者數千人)
- **中高價值**: `data-chart-generator` (適用場景廣泛)
- **中等價值**: `teams-bot-sso-auth` (特定領域)

---

## 下一步行動

### 立即行動（今天）
1. ✅ 建立本文檔
2. ⏳ 使用 `npx skills init` 初始化第一個 skill
3. ⏳ 選擇從 `databricks-genie-api` 開始

### 本週目標
- 完成 `databricks-genie-api` skill 開發
- 撰寫完整文檔和範例
- 建立測試套件
- 發布到 GitHub

### 本月目標
- 完成 3 個 skills 開發
- 註冊到 skills.sh
- 撰寫推廣文章

---

## 結論

將 DatabricksGenieBOT 的核心功能提取為 Agent Skills 是一個高價值的投資：
- **技術面**: 促進程式碼模組化和可重用性
- **社群面**: 幫助其他開發者，提升專案知名度
- **商業面**: 展示技術能力，潛在的商業機會

建議從 `databricks-genie-api` 開始，這是最有價值且最容易獨立的模組。
