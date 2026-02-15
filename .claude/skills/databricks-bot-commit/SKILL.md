---
name: databricks-bot-commit
description: |
  Git commit 助手。生成規範的 commit 訊息（Conventional Commits），分析變更內容。
  觸發：「提交」「commit」「git commit」「commit message」
  幫助撰寫清晰、一致的 commit 訊息。
---

# DatabricksGenieBOT Git Commit Helper

生成規範的 commit 訊息，遵循 Conventional Commits 和專案慣例。

## Conventional Commits 格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

---

## 1. Commit Types

| Type | 說明 | 範例 |
|------|------|------|
| `feat` | 新功能 | feat: 新增圖表視覺化功能 |
| `fix` | Bug 修復 | fix: 修復會話超時問題 |
| `docs` | 文檔變更 | docs: 更新 API 文檔 |
| `style` | 程式碼格式（不影響功能） | style: 格式化 Python 代碼 |
| `refactor` | 重構（不是新功能或修復） | refactor: 簡化 Genie 服務邏輯 |
| `perf` | 效能優化 | perf: 優化 HTTP 連接池 |
| `test` | 新增或修改測試 | test: 新增 EmailExtractor 測試 |
| `build` | 建置系統變更 | build: 更新 dependencies |
| `ci` | CI/CD 變更 | ci: 新增 GitHub Actions workflow |
| `chore` | 雜項變更 | chore: 更新 .gitignore |

---

## 2. Commit 訊息範本

### 新功能 (feat)

```bash
git commit -m "$(cat <<'EOF'
feat: 新增使用者回饋系統

- 新增 FeedbackCard 顯示讚/倒讚按鈕
- 整合 Databricks Genie Feedback API
- 新增回饋追蹤和日誌記錄
- 可透過環境變數 ENABLE_FEEDBACK_CARDS 控制

影響：用戶可以對查詢結果提供回饋，幫助改進 Genie 模型

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

### Bug 修復 (fix)

```bash
git commit -m "$(cat <<'EOF'
fix: 修復會話超時導致的記憶體洩漏

問題：
- 會話物件沒有自動清理
- 長時間執行導致 OOM

解決方案：
- 實作 SessionManager 自動清理機制
- 預設 4 小時後清除閒置會話
- 新增會話統計和監控

修復 #42

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

### 重構 (refactor)

```bash
git commit -m "$(cat <<'EOF'
refactor: 提取圖表分析為共用模組

變更：
- 從 bot/cards/chart_cards.py 提取 ChartAnalyzer
- 移至 app/utils/chart_analyzer.py
- 移除重複的圖表生成邏輯
- 統一圖表樣式配置

優點：
- 減少程式碼重複（-150 行）
- 提升可測試性
- 便於未來擴展更多圖表類型

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

### 效能優化 (perf)

```bash
git commit -m "$(cat <<'EOF'
perf: 優化 Genie API 呼叫效能

優化項目：
- 使用 HTTP 連接池重用連接（-30% 延遲）
- 實作 LRU + TTL 快取系統
- 優化日誌採樣（減少 99% I/O）
- 新增查詢效能指標收集

效能提升：
- API 回應時間：1200ms → 850ms（-29%）
- 連接建立時間：200ms → 20ms（-90%）
- 記憶體使用：降低 15%

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

### 測試 (test)

```bash
git commit -m "$(cat <<'EOF'
test: 新增 EmailExtractor 單元測試

- 測試 JWT Token 解碼（4 種 claims）
- 測試 Activity 提取
- 測試混合策略（Token → Activity → Graph API）
- 測試錯誤處理和回退機制
- 共 19 個測試案例，覆蓋率 100%

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

### 文檔 (docs)

```bash
git commit -m "$(cat <<'EOF'
docs: 新增 Azure 部署完整指南

- 新增 Azure App Service 部署步驟
- 新增 Container Apps 比較分析
- 新增 Application Insights 整合指南
- 新增環境變數配置說明
- 新增故障排除 FAQ

文檔位置：
- docs/deployment/azure_hosting_comparison.md
- docs/application_insights_integration.md

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## 3. 專案特定慣例

### Commit 訊息語言
- 使用**繁體中文**（專案主要語言）
- 技術術語保持英文（API, HTTP, Azure）

### Co-Authored-By
```bash
# 與 Claude 協作時總是加上
Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

### 關聯 Issue
```bash
# 修復 issue
fix: 修復登入錯誤

修復 #123
Closes #123

# 相關 issue
feat: 新增功能

相關 #456
```

---

## 4. Commit 工作流程

### 標準流程

```bash
# 1. 查看變更
git status
git diff

# 2. 添加檔案（避免使用 git add -A）
git add app/services/feature.py
git add tests/unit/test_feature.py
git add docs/feature.md

# 3. 確認暫存
git status

# 4. 提交（使用 HEREDOC 確保格式）
git commit -m "$(cat <<'EOF'
feat: 新增功能

- 詳細說明
- 影響範圍

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"

# 5. 推送
git push origin develop
```

### 多階段提交（推薦）

```bash
# 階段 1: 核心功能
git add app/services/feature.py
git commit -m "feat: 實作 Feature 核心邏輯"

# 階段 2: 測試
git add tests/unit/test_feature.py
git commit -m "test: 新增 Feature 單元測試"

# 階段 3: 文檔
git add docs/feature.md
git commit -m "docs: 新增 Feature 使用文檔"

# 一次推送
git push origin develop
```

---

## 5. Commit 訊息生成器

### 分析變更並生成訊息

```bash
# 查看變更的檔案
git status

# 查看變更內容
git diff --cached

# 查看最近的 commit 風格
git log --oneline -5
```

**範例分析**：

```
變更檔案：
- app/api/feature.py (新增 150 行)
- app/services/feature.py (新增 200 行)
- tests/unit/test_feature.py (新增 100 行)
- docs/feature.md (新增 50 行)

變更性質：
- 新增完整功能模組
- 包含測試和文檔

建議 Commit 訊息：

feat: 新增 Feature 功能模組

- 新增 Feature API 端點（app/api/feature.py）
- 新增 Feature 服務層（app/services/feature.py）
- 實作 HTTP 請求處理和錯誤處理
- 新增 100% 覆蓋率的單元測試
- 新增完整使用文檔

影響：提供新的功能入口，支援 XXX 場景

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

---

## 6. Pre-Commit 檢查清單

提交前檢查：

- [ ] 訊息遵循 Conventional Commits 格式
- [ ] Type 正確（feat/fix/docs/test/refactor/perf）
- [ ] 主題簡潔明確（< 72 字元）
- [ ] Body 說明變更原因和影響
- [ ] 測試通過（`pytest`）
- [ ] 沒有意外包含的檔案（檢查 `git status`）
- [ ] 沒有敏感資訊（密碼、token）
- [ ] 加上 Co-Authored-By（如與 Claude 協作）

---

## 7. 常見場景

### 場景 1: 修復 Pre-commit Hook 失敗

```bash
# 錯誤：commit 失敗（hook error）
# ⚠️ 注意：commit 沒有發生，不要使用 --amend

# 正確做法：修復問題後創建新 commit
# 1. 修復問題
# 2. 重新 add
git add <fixed-files>
# 3. 創建新 commit
git commit -m "fix: 修復 XXX 問題"
```

### 場景 2: 修改上一個 Commit

```bash
# 只在尚未 push 時使用
git commit --amend

# 修改訊息
git commit --amend -m "new message"

# ⚠️ 已經 push 的 commit 不要 amend！
```

### 場景 3: 暫存區管理

```bash
# 只暫存部分變更
git add -p  # 互動式選擇

# 取消暫存
git restore --staged <file>

# 查看暫存的變更
git diff --cached
```

---

## 8. Git Alias（可選）

```bash
# 在 ~/.gitconfig 或 .git/config 中設定

[alias]
    # 簡化提交
    co = commit
    st = status
    br = branch

    # 查看變更
    d = diff
    dc = diff --cached

    # 美化的 log
    lg = log --graph --oneline --decorate --all
    last = log -1 HEAD --stat

    # 提交統計
    stats = shortlog -sn
```

---

## 9. Commit 訊息最佳實踐

### 好的範例 ✅

```
feat: 新增使用者認證快取機制

- 實作 LRU + TTL 快取
- 減少 Graph API 呼叫次數
- 提升登入速度 40%

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**為什麼好**：
- 清楚的 type
- 簡潔的主題
- 說明實作內容
- 量化效能提升

### 不好的範例 ❌

```
update code
```

**為什麼不好**：
- 沒有 type
- 主題太模糊
- 沒有說明變更內容
- 沒有說明影響

---

## 10. 團隊協作

### 多人協作 Commit

```bash
# 與多位作者協作
git commit -m "$(cat <<'EOF'
feat: 實作新功能

Co-Authored-By: User1 <user1@example.com>
Co-Authored-By: User2 <user2@example.com>
Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

### Code Review 後的 Commit

```bash
# Review 後的修改
fix: 根據 Code Review 修正

修正內容：
- 移除未使用的 import
- 修正錯誤處理邏輯
- 新增缺少的類型提示

回應 Review 建議 #123

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

---

## 快速參考

### Type 速查表

```
feat     → 新功能
fix      → Bug 修復
docs     → 文檔
test     → 測試
refactor → 重構
perf     → 效能優化
style    → 格式
build    → 建置
ci       → CI/CD
chore    → 雜項
```

### Commit 範本

```bash
# 設定 commit 範本
git config commit.template .gitmessage.txt

# .gitmessage.txt 內容：
# <type>: <subject>
#
# <body>
#
# Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

---

## 參考資源

- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Commit 最佳實踐](https://chris.beams.io/posts/git-commit/)
- 專案 Commit 歷史：`git log --oneline -20`
