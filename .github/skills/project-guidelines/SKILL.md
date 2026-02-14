---
name: project-guidelines
description: 核心專案指引與編碼標準。在產生程式碼、註解、文件或機器人回應時使用，以確保一致性。
---

# 專案指引與標準

此專案中的所有變更都必須遵循這些指引。

## 1. 語言要求

**嚴格強制使用繁體中文 (Traditional Chinese)** 於所有人類可讀的文字。

### Artifacts & 規劃

- **規則**：Agent 產生的所有實作計畫、演練 (walkthroughs) 和推論 artifacts 必須使用繁體中文。

### 程式碼註解

- **規則**：所有程式碼註解必須使用繁體中文。
- **範例**：

  ```python
  # ✅ 正確：計算總收入
  total_revenue = calculate_total()

  # ❌ 錯誤：Calculate total revenue
  ```

### 文件

- **規則**：`README.md`、`*.md` 檔案和 docstrings 必須使用繁體中文。
- **例外**：特定的技術術語，若英文術語在業界更為標準 (例如 "OAuth", "Token", "DataFrame")。

### 機器人回應

- **規則**：發送給使用者的所有文字 (Activity text, Adaptive Cards, 錯誤訊息) 必須使用繁體中文 (台灣地區設定)。
- **語氣**：專業、有幫助且有禮貌。

### Git Commit 訊息

- **規則**：所有 git commit 訊息必須使用 **繁體中文 (Traditional Chinese)**。
- **格式**：`type: description` (例如 `feat: 新增登入功能`, `fix: 修復 Teams 連線問題`)。
- **類型**：`feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`。

### Git 合併策略

- **規則**：所有合併到 `main` 分支的操作必須使用 `--no-ff` (no fast-forward) 選項。
- **理由**：為了保留功能分支的提交歷史並維持清晰的變更脈絡，即使合併可以是 fast-forward。
- **指令**：`git merge --no-ff <branch_name>`

## 2. 編碼標準

### Python

- 遵循 PEP 8 風格指南。
- 函式簽章使用型別提示 (`typing` 模組)。
- 使用 `logger` 代替 `print` 進行輸出。

### 錯誤處理

- 不要向使用者暴露原始堆疊追蹤 (stack traces)。
- 將完整錯誤記錄到主控台/Application Insights。
- 回傳繁體中文的使用者友善錯誤訊息。

## 3. 環境變數

- 絕不硬編碼秘密 (secrets)。
- 務必使用 `os.environ` 或 `os.getenv`。
- 在 `.env.example` 中記錄新變數。

## 4. 進階編碼標準

### Async/Await (非阻塞 I/O)

- **規則**：所有 I/O 操作 (API 呼叫、資料庫查詢) 必須是非同步的。
- **禁止**：`time.sleep()`、同步 `requests` 函式庫。
- **必要**：`asyncio.sleep()`、`aiohttp`。

### Docstrings (文件字串)

- **規則**：所有函式和類別必須有 **繁體中文** 的 docstrings。
- **風格**：Google Style 或 NumPy Style。
- **內容**：描述、參數 (Args)、回傳值 (Returns)、引發例外 (Raises)。

  ```python
  def fetch_data(user_id: str) -> dict:
      """
      從 Genie API 獲取用戶數據。

      Args:
          user_id (str): 用戶的唯一標識符。

      Returns:
          dict: 包含用戶數據的字典。

      Raises:
          ValueError: 如果 user_id 無效。
      """
  ```

### Import 排序

- **順序**：標準函式庫 (Standard Library) -> 第三方 (Third Party) -> 本地應用程式 (Local Application)。
- **範例**：

  ```python
  import os
  import json

  import aiohttp
  from botbuilder.core import TurnContext

  from config import DefaultConfig
  ```

### 測試

- **單元測試**：業務邏輯必須要有。
- **Mocking**：外部服務 (Genie API, Graph API) 必須被 mock。絕不在單元測試中進行真實的網路呼叫。

## 5. 推薦的目錄結構

為了支援可擴展的 FastAPI + Bot Framework 架構，請使用以下結構：

```text
.
├── .antigravity/        # Agent Skills
├── .github/             # CI/CD Workflows
├── app/                 # 主要應用程式套件
│   ├── __init__.py
│   ├── main.py          # FastAPI 入口點 (was app.py)
│   ├── api/             # API Routers
│   │   ├── routes.py    # 一般路由
│   │   └── bot.py       # Bot Framework 處理程序
│   ├── core/            # 設定 & 配置
│   │   └── config.py
│   ├── services/        # 業務邏輯
│   │   └── genie.py     # GenieService
│   └── models/          # Pydantic Models & Schemas
├── bot/                 # Bot Framework 特定內容
│   ├── dialogs/         # ComponentDialogs
│   ├── cards/           # Adaptive Cards
│   └── handlers/        # ActivityHandlers
├── tests/               # 測試套件
│   ├── unit/            # 單元測試
│   └── integration/     # 整合測試
├── docs/                # 文件
│   ├── api/             # API 規格
│   └── architecture/    # 設計文件
├── logs/                # Log 檔案 (gitignored)
├── .env                 # 秘密 (gitignored)
├── .gitignore
└── requirements.txt
```
