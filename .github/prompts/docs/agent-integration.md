# 技能 (Skills) 之 Agent 整合

AI Agent 如何從此儲存庫發現、載入和使用技能。

## 技能發現機制

Agent 透過兩階段流程發現技能：

### 第一階段：目錄掃描

在啟動時，Agent 會掃描設定好的技能目錄 (通常是 `.github/skills/`)，尋找包含 `SKILL.md` 檔案的資料夾：

```
.github/skills/
├── azure-cosmos-db-py/
│   └── SKILL.md          # 有效的技能
├── azure-ai-agents-ts/
│   └── SKILL.md          # 有效的技能
├── mcp-builder/
│   └── SKILL.md          # 有效的技能
└── some-folder/
    └── README.md         # 不是技能 (沒有 SKILL.md)
```

### 第二階段：中繼資料擷取

對於每個發現的技能，Agent 僅解析 YAML frontmatter：

```yaml
---
name: azure-cosmos-db-py
description: 使用 Python/FastAPI 依照生產級模式建置 Azure Cosmos DB NoSQL 服務。
---
```

這個中繼資料會在啟動時載入到 Agent 的 context 中，每個技能約佔用 50-100 個 tokens。

## VS Code / GitHub Copilot 發現

GitHub Copilot 和 VS Code agents 透過以下方式發現技能：

1. **Workspace 掃描**：自動偵測 `.github/skills/` 中的技能
2. **Copilot 指引**：`.github/copilot-instructions.md` 檔案參考可用的技能
3. **Agent 角色**：`.github/agents/` 中的檔案 (例如 `backend.agent.md`) 可以指定要載入哪些技能

### Copilot 設定範例

在 `.github/copilot-instructions.md` 中：

```markdown
## Available Skills

For Azure Cosmos DB work, load the `azure-cosmos-db-py` skill.
For FastAPI endpoints, load the `fastapi-router-py` skill.
```

## 漸進式揭露 (Progressive Disclosure)

技能使用三層載入策略以有效管理 context：

| 層級 | 內容 | 載入時機 | Token 成本 |
|------|---------|-------------|------------|
| **1. 中繼資料** | `name` + `description` (來自 frontmatter) | 啟動時 | 每個技能 ~50-100 |
| **2. 指引** | 完整的 `SKILL.md` 本文 | 啟動 (Activation) 時 | ~500-2000 |
| **3. 資源** | `scripts/`, `references/`, `assets/` 中的檔案 | 依需求 | 不定 |

### 範例：技能啟動流程

```
User: "Create a Cosmos DB service for user data"

Agent 思考：
  → 掃描已載入的中繼資料尋找相關技能
  → 發現："azure-cosmos-db-py: Build Azure Cosmos DB NoSQL services..."
  → 透過讀取完整的 SKILL.md 啟動技能
  → 遵循指引實作服務
```

## 依據 Agent 類型的技能載入

### Claude Code / Copilot CLI

基於檔案系統的 Agent 透過 shell 指令載入技能：

```bash
cat /path/to/skills/azure-cosmos-db-py/SKILL.md
```

可用技能提示中的 `location` 欄位會告訴 Agent 去哪裡找到它。

### 基於工具的 Agent (Tool-Based Agents)

沒有檔案系統存取權限的 Agent 使用專用工具：

```python
# Agent 呼叫載入技能的工具
result = load_skill("azure-cosmos-db-py")
```

## 選擇性載入的最佳實踐

**絕不要一次載入所有技能。** 這會導致語境腐爛 (context rot)：

- 注意力分散到不相關的領域
- 在不相關的指引上浪費 tokens
- 混淆來自不同 SDK 的模式

**請改為這樣做：**

```
User request: "Add a blob storage endpoint"

Agent 應該：
1. 識別任務領域：Azure Storage + API 端點
2. 僅載入：azure-storage-blob-py, fastapi-router-py
3. 忽略：azure-cosmos-db-py, react-flow-node-ts 等
```

## 將技能新增至你的專案

### 透過 npx (推薦)

```bash
npx skills add microsoft/agent-skills
# 從互動式精靈中選擇技能
```

### 手動安裝

```bash
# 複製特定技能
cp -r agent-skills/.github/skills/azure-cosmos-db-py your-project/.github/skills/

# 或在多專案設定中使用符號連結 (symlink)
ln -s /path/to/agent-skills/.github/skills/mcp-builder /path/to/your-project/.github/skills/mcp-builder
```

## 技能命名慣例

技能使用語言後綴進行自動分類：

| 後綴 | 語言 | 範例 |
|--------|----------|---------|
| `-py` | Python | `azure-cosmos-db-py` |
| `-dotnet` | .NET/C# | `azure-ai-inference-dotnet` |
| `-ts` | TypeScript | `azure-ai-agents-ts` |
| `-java` | Java | `azure-cosmos-java` |
| (無) | 跨語言 | `mcp-builder`, `azd-deployment` |

這允許 Agent 根據專案的技術堆疊過濾技能。
