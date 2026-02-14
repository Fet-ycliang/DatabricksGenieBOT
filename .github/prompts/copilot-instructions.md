# Databricks Genie BOT Copilot 指引

## 專案概述

Databricks Genie BOT 是一個整合 Databricks Genie API 的 Microsoft Teams 機器人專案。本專案使用 FastAPI 作為後端框架，結合 Microsoft Bot Framework SDK 處理對話邏輯，並透過 Databricks SDK 與 Genie 服務互動。

## ⚠️ 優先獲取最新資訊

**Azure SDK 和 Foundry API 經常變更。絕不使用過時的知識。**

在使用 Azure/Foundry SDK 實作任何功能之前：

1. **先搜尋官方文件** — 使用 Microsoft Docs MCP (`microsoft-docs`) 取得目前的 API 簽章、參數和模式。
2. **驗證 SDK 版本** — 檢查 `pip show <package>` 以確認已安裝的版本；不同版本間的 API 可能會有差異。
3. **不要相信快取的知識** — 你的訓練資料可能已經過時。你所「知道」的 SDK 可能有破壞性的變更。

**如果你跳過此步驟並使用過時的模式，你將會產生無法運作的程式碼。**

---

## 核心原則與標準

所有開發工作必須嚴格遵循以下原則：

### 1. 語言要求

**嚴格強制使用繁體中文 (Traditional Chinese)** 於所有人類可讀的文字：
- 實作計畫 (Implementation Plans)
- 程式碼註解 (Code Comments)
- 文件 (Documentation)
- 機器人回應 (Bot Responses)
- Git Commit 訊息

### 2. 編碼標準

- **Python 風格**：遵循 PEP 8。
- **非阻塞 I/O**：所有 I/O 操作 (API, DB) 必須使用 `async/await`。禁止使用 `time.sleep()` 或同步 `requests`。
- **文件字串**：所有函式和類別必須有繁體中文 docstrings (Google/NumPy style)。
- **環境變數**：絕不硬編碼 secrets，使用 `os.environ` 或 `os.getenv`。

### 3.寫程式前先思考

**不要假設。不要隱藏困惑。提出權衡方案。**

- 明確陳述假設。如果不確定，請發問。
- 如果存在多種解釋，請將它們呈現出來 — 不要默默地選擇其中一種。

### 4. 簡潔至上

**用最少的程式碼解決問題。不做推測性的開發。**

- 不要開發超出要求的功能。
- 如果你寫了 200 行程式碼，但其實 50 行就能解決，請重寫。

---

## 儲存庫結構

本專案遵循以下推薦結構：

```text
.
├── .github/             # CI/CD Workflows & SDK Skills
│   ├── skills/          # SDK/Library specific skills (e.g., azure-identity-py)
│   └── prompts/         # Reusable prompts
├── app/                 # 主要應用程式套件
│   ├── main.py          # FastAPI 入口點
│   ├── api/             # API Routers
│   ├── services/        # 業務邏輯
│   └── models/          # Pydantic Models
├── bot/                 # Bot Framework 特定內容
├── tests/               # 測試套件
├── config.py            # 設定檔
├── pyproject.toml       # 依賴管理
└── requirements.txt     # 依賴列表
```

## 技能 (Skills)

本專案使用位於 `.github/skills/` 中的 SDK 層級技能來輔助開發。

### 可用技能

| 技能 | 用途 |
|-------|---------|
| `azure-identity-py` | Azure Identity SDK 身份驗證 (DefaultAzureCredential) |
| `azure-monitor-opentelemetry-py` | Azure Monitor OpenTelemetry 監控整合 |
| `botbuilder-py` | Microsoft Bot Framework SDK for Python |
| `databricks-sdk-py` | Databricks SDK 與 Genie API 互動 |
| `fastapi-py` | FastAPI 框架開發模式 |
| `matplotlib-seaborn-py` | 資料視覺化與圖表產生 |
| `microsoft-graph-py` | Microsoft Graph API 整合 (Async HTTP) |
| `project-guidelines` | 專案核心指引與標準 |
| `python-dotenv` | 環境變數管理 |
| `teams-sso-provider-py` | Teams SSO 身份驗證實作 |

📖 **請參閱 [README.md](../../README.md) 以取得專案詳細資訊與架構說明**

### 技能選擇

只載入與當前任務相關的技能。載入所有技能會導致語境腐爛 (context rot) — 注意力分散和模式混淆。

---

## MCP 伺服器

在 `.vscode/mcp.json` 中預先設定的 Model Context Protocol 伺服器提供了額外的功能：

### 文件與搜尋

| MCP | 用途 |
|-----|---------|
| `microsoft-docs` | **搜尋 Microsoft Learn** — 官方 Azure/Foundry 文件。優先使用此功能。 |
| `context7` | 具有語意搜尋功能的索引文件 |
| `deepwiki` | 詢問有關 GitHub 儲存庫的問題 |

### 開發工具

| MCP | 用途 |
|-----|---------|
| `github` | GitHub API 操作 |
| `playwright` | 瀏覽器自動化與測試 |
| `terraform` | 基礎設施即程式碼 (IaC) |
| `eslint` | JavaScript/TypeScript linting |

---

## SDK 快速參考

| 套件 | 用途 | 安裝 |
|---------|---------|---------|
| `databricks-sdk` | Databricks Genie API 互動 | `pip install databricks-sdk` |
| `botbuilder-core` | Bot Framework 核心邏輯 | `pip install botbuilder-core` |
| `fastapi[standard]` | Web API 框架 | `pip install "fastapi[standard]"` |
| `msgraph-core` | Microsoft Graph 整合 | `pip install msgraph-core` |
| `azure-identity` | 身份驗證 | `pip install azure-identity` |

---

## 慣例

### 程式碼風格

- 所有 I/O 操作優先使用 `async/await`
- 使用 context managers：`with client:` 或 `async with client:`
- 明確關閉用戶端或使用 context managers
- 在所有函式簽章上使用型別提示 (type hints)

### 整潔程式碼檢查清單

在完成任何程式碼變更之前：

- [ ] 函式只做一件事
- [ ] 命名具描述性且能揭示意圖
- [ ] 沒有魔術數字或字串 (使用常數)
- [ ] 錯誤處理是明確的 (沒有空的 catch區塊)
- [ ] 沒有被註解掉的程式碼
- [ ] 測試涵蓋了變更

---

## Do's and Don'ts (要做與不要做)

### 要做 (Do)

- ✅ 使用 `DefaultAzureCredential` 進行身份驗證
- ✅ 對所有 I/O 操作使用 async/await
- ✅ 在實作之前或同時撰寫測試
- ✅ 使用繁體中文撰寫所有文件與註解

### 不要做 (Don't)

- ❌ 硬編碼 (Hardcode) 憑證或端點
- ❌ 壓制型別錯誤 (`as any`, `@ts-ignore`, `# type: ignore`)
- ❌ 留下空的例外處理程序
- ❌ 使用英文撰寫 Commit 訊息或註解

---

## 成功指標

如果你看到以下情況，代表這些原則正在發揮作用：

- diffs 中不必要的變更變少了
- 因過度複雜而導致的重寫變少了
- 澄清問題發生在實作之前 (而不是在犯錯之後)
- 乾淨、極簡的 PR，沒有順便進行的重構 (drive-by refactoring)
- 文件化預期行為的測試
