# Agent 的 MCP 伺服器使用方式

Agent 如何與此儲存庫中設定的 Model Context Protocol (MCP) 伺服器互動。

## 什麼是 MCP？

MCP (Model Context Protocol) 是一個標準，用於將 AI Agent 連接到外部工具和資料來源。MCP 伺服器暴露了 Agent 在任務執行期間可以呼叫的功能。

## 已設定的 MCP 伺服器

此儲存庫在 `.vscode/mcp.json` 中提供 MCP 伺服器設定：

### 文件伺服器 (Documentation Servers)

| 伺服器 | 用途 | 何時使用 |
|--------|---------|-------------|
| `microsoft-docs` | 搜尋 Microsoft Learn | 在任何 Azure SDK 實作之前 **首先** 使用 |
| `context7` | 對索引文件進行語意搜尋 | 當你需要 Foundry 特定的模式時 |
| `deepwiki` | 查詢 GitHub 儲存庫 | 當研究開源軟體實作時 |

### 開發伺服器 (Development Servers)

| 伺服器 | 用途 | 何時使用 |
|--------|---------|-------------|
| `github` | GitHub API 操作 | PR、Issue、程式碼搜尋 |
| `playwright` | 瀏覽器自動化 | 測試、爬蟲、驗證 |
| `terraform` | 基礎設施即程式碼 (IaC) | Azure 資源配置 |
| `eslint` | JavaScript/TypeScript linting | 程式碼品質檢查 |

### 工具伺服器 (Utility Servers)

| 伺服器 | 用途 | 何時使用 |
|--------|---------|-------------|
| `sequentialthinking` | 逐步推理 | 複雜的多步驟問題 |
| `memory` | 持久性儲存 | 跨工作階段的 context |
| `markitdown` | 文件轉換 | 將檔案轉換為 markdown |

## Agent 工作流程：使用 MCP 伺服器

### 模式：實作前先搜尋

**關鍵**：Azure SDK 經常變更。在編寫程式碼之前，務必搜尋官方文件。

```
User: "Create an Azure AI Search index with vector fields"

Agent 工作流程：
1. 首先：查詢 microsoft-docs MCP
   → 搜尋："Azure AI Search vector index Python SDK"
   → 取得：目前的 API 簽章、必要參數
   
2. 然後：載入相關技能
   → azure-search-documents-py
   
3. 最後：實作
   → 使用技能中的模式 + 文件中的目前 API
```

### 範例：microsoft-docs MCP 使用方式

`microsoft-docs` MCP 提供搜尋 Microsoft Learn 的工具：

```
Agent 呼叫：microsoft_docs_search
查詢："azure-ai-projects AIProjectClient Python"

回應：
- Title: "Azure AI Projects client library for Python"
- URL: https://learn.microsoft.com/python/api/azure-ai-projects/
- Excerpt: "AIProjectClient is the main entry point..."
```

如果搜尋結果不完整，則擷取完整頁面：

```
Agent 呼叫：microsoft_docs_fetch
URL: "https://learn.microsoft.com/python/api/azure-ai-projects/"

回應：文件頁面的完整 markdown 內容
```

### 範例：context7 MCP 使用方式

`context7` MCP 提供對此儲存庫索引文件的語意搜尋：

```
Agent 呼叫：context7_query-docs
Library: "/microsoft/agent-skills"
查詢："How to create a Cosmos DB service layer with FastAPI"

回應：
- 來自 azure-cosmos-db-py 的相關技能內容
- 服務層實作的模式
- FastAPI 整合範例
```

### 範例：結合 MCP + 技能

```
任務："Add Azure Blob Storage upload endpoint"

步驟 1：搜尋目前 API
  → microsoft-docs："azure-storage-blob Python upload_blob"
  → 取得：目前的 BlobClient.upload_blob() 簽章

步驟 2：載入技能
  → azure-storage-blob-py：儲存模式
  → fastapi-router-py：端點模式

步驟 3：同時使用兩者進行實作
  → 來自文件的目前 API + 來自技能的模式
```

## MCP 設定格式

MCP 伺服器設定於 `.vscode/mcp.json`：

```json
{
  "servers": {
    "microsoft-docs": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@anthropic/microsoft-docs-mcp"]
    },
    "context7": {
      "type": "stdio", 
      "command": "npx",
      "args": ["-y", "@anthropic/context7-mcp"]
    },
    "github": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@anthropic/github-mcp"],
      "env": {
        "GITHUB_TOKEN": "${env:GITHUB_TOKEN}"
      }
    }
  }
}
```

## Agent 使用 MCP 的決策樹

```
任務是否關於 Azure/Microsoft SDK？
├─ 是 → 首先查詢 microsoft-docs
│       然後載入相關技能
│       然後實作
│
└─ 否 → 任務是否關於此儲存庫的模式？
        ├─ 是 → 查詢 context7
        │       然後載入相關技能
        │
        └─ 否 → 任務是否關於外部程式碼/儲存庫？
                ├─ 是 → 查詢 deepwiki 或 github
                │
                └─ 否 → 原則上採用僅使用技能的方法
```

## 為什麼要結合 MCP + 技能？

| MCP 伺服器提供 | 技能提供 |
|---------------------|----------------|
| 目前的 API 簽章 | 已建立的模式 |
| 最新的文件 | 最佳實踐 |
| 即時資料 | 領域專業知識 |
| 外部整合 | 編碼標準 |

**MCP = 最新資訊。技能 = 經過驗證的模式。**

同時使用兩者以獲得可靠的實作：

```
# 差：僅使用技能 (可能使用過時的 API)
載入 azure-cosmos-db-py → 實作

# 差：僅使用 MCP (沒有模式，重新造輪子)
搜尋文件 → 從頭開始實作

# 好：MCP + 技能
搜尋文件 (目前 API) → 載入技能 (模式) → 實作
```

## 疑難排解

### MCP 伺服器無回應

1. 檢查伺服器是否已安裝：`npx -y @anthropic/microsoft-docs-mcp --version`
2. 驗證 `.vscode/mcp.json` 中的設定
3. 檢查環境變數 (例如 github MCP 的 `GITHUB_TOKEN`)

### context7 的結果過時

Context7 索引透過 GitHub Actions 每日更新。若要取得最新內容：
1. 檢查 workflow 上次執行的時間：`.github/workflows/update-llms-txt.yml`
2. 若要立即更新，手動觸發 workflow
3. 改用 `microsoft-docs` 以取得權威的最新資訊
