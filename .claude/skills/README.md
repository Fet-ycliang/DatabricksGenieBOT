# DatabricksGenieBOT Claude Code Skills

專案專屬的 Claude Code 開發輔助 skills，大幅降低開發時的 token 消耗。

## 📦 已安裝的 Skills

### 1. **databricks-bot-dev** - 主開發助手
快速開發模板和專案架構參考。

**觸發詞**: 「新增功能」「建立 API」「FastAPI endpoint」「Bot handler」

**提供內容**:
- 8 種開發模板（API、服務、測試、卡片、Databricks、Azure、圖表）
- 專案架構速查
- 開發工作流程
- 最佳實踐

---

### 2. **databricks-bot-test** - 測試輔助
自動生成測試程式碼和 Mock 模式。

**觸發詞**: 「生成測試」「寫測試」「pytest」「mock」

**提供內容**:
- 單元測試模板（同步、非同步、Mock、參數化）
- 整合測試和效能測試
- 10+ 種測試模式
- Fixture 範例
- 測試覆蓋率工具

---

### 3. **databricks-bot-card** - Adaptive Card 設計器
快速建立 Teams 卡片。

**觸發詞**: 「建立卡片」「Adaptive Card」「Teams card」

**提供內容**:
- 10 種卡片模板（歡迎、結果、圖表、錯誤、回饋等）
- Hero Card 和複合卡片
- 設計最佳實踐
- Card Designer 整合

---

### 4. **databricks-bot-commit** - Git Commit 助手
生成規範的 commit 訊息。

**觸發詞**: 「提交」「commit」「commit message」

**提供內容**:
- Conventional Commits 格式
- 10 種 commit 類型（feat, fix, docs, test等）
- 專案 commit 慣例
- 多階段提交工作流程
- Pre-commit 檢查清單

---

### 5. **databricks-bot-troubleshoot** - 故障排除
診斷和解決常見問題。

**觸發詞**: 「錯誤」「debug」「troubleshoot」「失敗」

**提供內容**:
- Databricks API 錯誤（401, 404, 429）
- Bot Framework 錯誤
- Azure 部署問題
- HTTP/網路錯誤
- 記憶體和效能問題
- 診斷工具

---

### 6. **databricks-bot-optimize** - 效能優化
提升應用程式效能。

**觸發詞**: 「優化」「效能」「速度慢」「performance」

**提供內容**:
- HTTP 連接池優化（90% 提升）
- 快取系統（99% 提升）
- 非同步並發處理（88% 提升）
- 記憶體管理
- 效能監控和基準測試

---

### 7. **databricks-bot-review** - Code Review
程式碼審查指南。

**觸發詞**: 「review」「code review」「檢查程式碼」

**提供內容**:
- 安全性檢查（敏感資訊、SQL 注入、XSS）
- 效能檢查
- 錯誤處理
- 程式碼品質
- Review 流程和評論範本

---

## 🚀 使用方式

### 自動觸發
當您在 Claude Code 中使用觸發詞時，相應的 skill 會自動啟動。

**範例**:
```
你: 新增一個 API 端點來處理用戶查詢
Claude: [databricks-bot-dev skill 啟動]
        [提供 FastAPI 端點模板]

你: 為這個功能寫測試
Claude: [databricks-bot-test skill 啟動]
        [提供測試模板]

你: 優化這段程式碼的效能
Claude: [databricks-bot-optimize skill 啟動]
        [提供優化建議]
```

### 手動使用
直接說明您需要的內容：
```
你: 給我一個 Adaptive Card 的錯誤訊息模板
你: 幫我寫這個服務的單元測試
你: 如何優化 HTTP 請求的效能？
你: 檢查這段程式碼有沒有安全問題
```

---

## 💡 效益

### Token 消耗降低
- **之前**: 每次開發需閱讀 5-10 個檔案（~15,000 tokens）
- **現在**: 直接使用 skill 模板（~2,000 tokens）
- **節省**: **~85% token 消耗**

### 開發速度提升
- 標準化模板減少錯誤
- 快速開始新功能開發
- 一致的程式碼風格

### 知識集中化
- 所有最佳實踐集中在 skills 中
- 團隊成員可以共用同一套標準
- 降低學習曲線

---

## 📊 統計

- **Skills 總數**: 7 個
- **文檔行數**: ~4,500 行
- **涵蓋場景**: 50+ 種
- **開發模板**: 30+ 個
- **最佳實踐**: 100+ 項

---

## 🔄 更新和維護

### 新增 Skill
```bash
# 1. 建立目錄
mkdir -p .claude/skills/new-skill

# 2. 建立 SKILL.md
touch .claude/skills/new-skill/SKILL.md

# 3. 撰寫 frontmatter 和內容
# 4. 提交到版本控制
git add .claude/skills/new-skill/
git commit -m "feat: 新增 new-skill"
```

### 更新現有 Skill
```bash
# 直接編輯 SKILL.md
vim .claude/skills/databricks-bot-dev/SKILL.md

# 提交變更
git commit -m "docs: 更新 databricks-bot-dev skill"
```

---

## 🎯 最佳實踐

### 1. 定期更新
當專案有新的開發模式或最佳實踐時，更新相應的 skill。

### 2. 保持簡潔
每個 skill 應該：
- SKILL.md < 500 行
- 提供即用模板
- 避免冗長解釋

### 3. 使用範例
提供真實的程式碼範例，而不是抽象描述。

### 4. 清楚的觸發詞
選擇明確、容易記憶的觸發詞。

---

## 📚 參考資源

- [Skill 開發指南](.agent/skills/skill-creator/SKILL.md)
- [Claude Code 文檔](https://docs.anthropic.com/claude/docs)
- [專案開發指南](../../CLAUDE.md)

---

## 🤝 貢獻

歡迎改進和新增 skills！

1. 識別常用的開發模式
2. 創建新 skill 或更新現有 skill
3. 測試效果
4. 提交 PR

---

## ⚙️ 配置

Skills 位於 `.claude/skills/` 目錄，由 Claude Code 自動載入。

- **專案級別**: `.claude/skills/` (當前專案)
- **使用者級別**: `~/.claude/skills/` (所有專案)

本專案的 skills 是專案專屬的，僅在此專案中生效。

---

最後更新: 2026-02-16
