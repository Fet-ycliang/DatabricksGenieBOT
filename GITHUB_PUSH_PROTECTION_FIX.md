# GitHub Push Protection 問題解決指南

## 🚨 問題描述

當嘗試 push 到 GitHub 時，您可能會看到這個錯誤：

```
error: failed to push some refs
GH013: Repository rule violations found
Push cannot contain secrets
```

### 原因

GitHub 的 **Secret Scanning** 功能檢測到提交中包含敏感信息（如 API tokens、密鑰等）。

---

## ⚡ 快速修復（推薦）

### 方案 A：使用 GitHub Secret Scanning Bypass（最快）

1. **等待 GitHub 提供的 bypass 鏈接**
   - 檢查終端輸出中是否有類似的 URL：
   ```
   https://github.com/[username]/[repo]/security/secret-scanning/unblock-secret/[unique-id]
   ```

2. **訪問該鏈接**
   - 使用 GitHub 帳戶登錄
   - 查看檢測到的敏感信息
   - 點擊"Allow"或"Unblock"按鈕

3. **重新 push**
   ```bash
   git push origin develop
   ```

**優點**：快速，允許立即 push  
**缺點**：不清理 git 歷史記錄中的 token

---

## 🔧 徹底修復方案

### 方案 B：清理 Git 歷史（推薦長期解決方案）

使用 **BFG Repo-Cleaner** 移除 git 歷史記錄中所有提及敏感信息的文件：

#### 步驟 1：安裝 BFG
```bash
# 使用 Chocolatey（Windows）
choco install bfg

# 或下載：
# https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar
```

#### 步驟 2：創建修復列表
創建文件 `secrets.txt`，列出所有要移除的敏感信息：
```
dapi_[your_old_token_pattern_here]
```

#### 步驟 3：運行 BFG（從倉庫目錄外）
```bash
bfg --replace-text secrets.txt D:\azure_code\DatabricksGenieBOT
```

#### 步驟 4：清理引用
```bash
cd D:\azure_code\DatabricksGenieBOT
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

#### 步驟 5：強制 push
```bash
git push --force-with-lease origin develop
```

**優點**：完全清理歷史記錄，長期安全  
**缺點**：需要更多步驟，會重寫 commit 歷史

---

### 方案 C：使用 Git Filter-Branch（替代方案）

如果 BFG 不可用，使用 Git 原生工具：

```bash
# 替換所有提交中的敏感信息
# 注意：這個命令很複雜，建議先備份
git filter-branch -f --tree-filter \
  'find . -type f -exec sed -i "s/dapi_[a-zA-Z0-9]\\{32\\}/dapi_REDACTED/g" {} \;' \
  HEAD
```

然後強制 push：
```bash
git push --force-with-lease origin develop
```

---

## 🛡️ 預防措施

### 1. 確保 .env 在 .gitignore

**檢查 .gitignore：**
```bash
grep -n "\.env" .gitignore
```

**應該看到：**
```
# 環境變數
.env
.env.local
```

✅ 已在此倉庫中配置

### 2. 不要在代碼或文檔中硬編碼敏感信息

❌ **不要做這些：**
```python
# ❌ 錯誤：硬編碼 token
DATABRICKS_TOKEN = "dapi_abc123xyz"

# ❌ 錯誤：在文檔中作為示例
DATABRICKS_TOKEN=dapi_abc123xyz
```

✅ **應該這樣做：**
```python
# ✅ 從環境變數讀取
DATABRICKS_TOKEN = os.getenv('DATABRICKS_TOKEN')

# ✅ 在文檔中使用占位符
DATABRICKS_TOKEN=dapi_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
DATABRICKS_TOKEN=dapi_your_token_here
DATABRICKS_TOKEN=dapi_[generated_from_databricks_settings]
```

### 3. 使用 .env.example

創建模板文件供他人參考：

**`.env.example` 內容：**
```bash
# Databricks 配置
DATABRICKS_HOST=https://adb-xxxx.azuredatabricks.net
DATABRICKS_TOKEN=dapi_your_token_here
DATABRICKS_SPACE_ID=your_space_id

# Bot Framework 配置（可選）
APP_ID=your_app_id_here
APP_PASSWORD=your_app_password_here

# 日誌設置
VERBOSE_LOGGING=False
LOG_FILE=./bot_debug.log
TIMEZONE=Asia/Taipei
```

提交 `.env.example` 到 git，但不要提交 `.env`

### 4. 定期輪轉敏感信息

- **API Keys**: 每 90 天更換一次
- **Passwords**: 每 6 個月更換一次
- **Access Tokens**: 在 Databricks 設置中設置合理的過期時間

---

## 🔄 如果 Token 已泄露

如果您的 token 意外被提交到 GitHub：

### 立即行動（重要！）

1. **撤銷舊 token**
   - 登錄 Databricks 工作區
   - 進入 Settings > Developer > Access tokens
   - 找到泄露的 token，點擊"Revoke"

2. **生成新 token**
   - 在同一頁面點擊"Generate new token"
   - 複製新 token

3. **更新本地 .env**
   ```bash
   # 編輯 .env
   DATABRICKS_TOKEN=dapi_your_new_token_here
   ```

4. **驗證新 token**
   ```bash
   python verify_databricks_token.py
   ```

5. **清理 git 歷史**
   - 使用上面的"方案 B"或"方案 C"

6. **通知團隊**
   - 告知任何可能看到過舊 token 的人
   - 確認沒有人用舊 token 進行過未授權操作

---

## 🔍 檢查 Git 歷史中是否有敏感信息

### 快速檢查

```bash
# 搜索 "dapi_" 模式
git log -p | findstr "dapi_"

# 搜索特定字符串
git log -S "your_secret_here" -p
```

### 完整掃描

```bash
# 檢查所有文件和提交
git log --all --source --remotes --format="%h %s" | findstr "token\|password\|secret"
```

---

## 📋 檢查清單

完成以下步驟以確保倉庫安全：

- [ ] .env 文件已添加到 .gitignore
- [ ] .env 未被提交到 git
- [ ] 代碼中沒有硬編碼的敏感信息
- [ ] 文檔中使用的是占位符，不是真實 token
- [ ] 已撤銷任何泄露的 token
- [ ] 已生成新的 token 並更新 .env
- [ ] Git 歷史已清理（使用 BFG 或 filter-branch）
- [ ] 已成功 push 到 GitHub
- [ ] 創建了 .env.example 供他人參考

---

## 📞 其他資源

- [GitHub Secret Scanning 文檔](https://docs.github.com/en/code-security/secret-scanning/about-secret-scanning)
- [BFG Repo-Cleaner 官網](https://rtyley.github.io/bfg-repo-cleaner/)
- [Databricks Token 管理](https://docs.databricks.com/en/dev-tools/auth/pat.html)

---

## 🆘 故障排查

### 問題：Git 強制 push 失敗

```
error: failed to push some refs
hint: Updates were rejected because the tip of your current branch is behind its remote counterpart
```

**解決方案：**
```bash
# 拉取最新更改
git pull origin develop

# 解決衝突後重新 push
git push --force-with-lease origin develop
```

### 問題：BFG 找不到命令

```
bfg: command not found
```

**解決方案：**
- 重新安裝 BFG 或
- 使用完整路徑：`java -jar bfg-1.14.0.jar`

### 問題：仍然無法 push

1. 驗證您正在推送到正確的分支
   ```bash
   git remote -v
   ```

2. 檢查是否還有其他未檢測到的敏感信息
   ```bash
   git log -p | findstr "token\|password\|secret"
   ```

3. 聯繫 GitHub 支持人員

---

**最後更新**: 2026-01-29  
**相關文件**: .env, .gitignore, verify_databricks_token.py
