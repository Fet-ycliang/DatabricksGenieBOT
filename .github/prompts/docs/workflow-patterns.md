# 工作流程模式：結合技能與提示詞

如何將技能與提示詞組合成多步驟工作流程。

## 技能 vs 提示詞 (Skills vs Prompts)

| 元件 | 用途 | 位置 | 何時使用 |
|-----------|---------|----------|-----------|
| **技能 (Skills)** | 領域專業知識、SDK 模式、編碼標準 | `.github/skills/` | 任務符合技能描述時 |
| **提示詞 (Prompts)** | 特定動作的可重複使用範本 | `.github/prompts/` | 使用者明確呼叫或 Agent 選擇時 |

技能提供 **知識**。提示詞提供 **結構**。

## 組合技能 + 提示詞

### 範例 1：新增 API 端點

**任務**："新增用於更新使用者設定檔的 PUT 端點"

**所需元件**：
- 技能：`fastapi-router-py` — FastAPI 模式、回應模型、驗證
- 技能：`pydantic-models-py` — 請求/回應架構模式
- 提示詞：`add-endpoint.prompt.md` — 逐步端點建立範本

**工作流程**：

```
1. Agent 載入 fastapi-router-py 技能
   → 學習：Router 模式、依賴注入、回應模型
   
2. Agent 載入 pydantic-models-py 技能
   → 學習：基底/建立/更新/回應模型模式
   
3. Agent 使用 add-endpoint.prompt.md 結構：
   → 步驟 1：定義 Pydantic 模型 (UserUpdate, UserResponse)
   → 步驟 2：建立帶有 PUT 處理程序的 Router
   → 步驟 3：新增身份驗證依賴項
   → 步驟 4：撰寫測試
```

### 範例 2：建置帶有儲存功能的資料服務

**任務**："建立由 Cosmos DB 支援的文件服務"

**所需元件**：
- 技能：`azure-cosmos-db-py` — Cosmos DB 服務模式
- 技能：`azure-identity-py` — 使用 DefaultAzureCredential 的身份驗證
- 技能：`pydantic-models-py` — 模型定義

**工作流程**：

```
1. Agent 載入 azure-identity-py 技能
   → 建立：使用 DefaultAzureCredential，絕不硬編碼憑證
   
2. Agent 載入 azure-cosmos-db-py 技能
   → 學習：服務層模式、分割區索引鍵策略、參數化查詢
   
3. Agent 載入 pydantic-models-py 技能
   → 學習：模型變體模式 (Base, Create, Update, Response, InDB)
   
4. Agent 實作：
   → DocumentBase, DocumentCreate, DocumentResponse 模型
   → 帶有 CRUD 操作的 DocumentService 類別
   → 適當的錯誤處理和日誌記錄
```

### 範例 3：帶有狀態的前端元件

**任務**："建立帶有可拖曳節點的工作流程編輯器"

**所需元件**：
- 技能：`react-flow-node-ts` — 自訂 React Flow 節點
- 技能：`zustand-store-ts` — 狀態管理
- 提示詞：`create-node.prompt.md` — 節點元件範本
- 提示詞：`create-store.prompt.md` — Store 建立範本

**工作流程**：

```
1. Agent 使用 create-store.prompt.md 搭配 zustand-store-ts 技能
   → 建立：帶有節點、邊緣、動作的 workflowStore
   
2. Agent 使用 create-node.prompt.md 搭配 react-flow-node-ts 技能
   → 建立：帶有 handles、TypeScript 型別的自訂節點元件
   
3. Agent 整合元件
   → 將 store 連接至 React Flow 畫布
   → 新增拖放功能
```

## 多步驟工作流程範本

對於複雜任務，明確建構工作流程：

```markdown
## Task: [描述]

### Step 1: [設定]
- Load skills: [skill-1], [skill-2]
- Verify: [檢查]

### Step 2: [實作]
- Use prompt: [prompt-name]
- Apply patterns from: [skill-name]
- Verify: [檢查]

### Step 3: [整合]
- Connect components
- Verify: [檢查]

### Step 4: [測試]
- Write tests following TDD pattern
- Verify: All tests pass
```

## 此儲存庫中的提示詞範本

| 提示詞 | 用途 | 適合搭配 |
|--------|---------|-------------------|
| `add-endpoint.prompt.md` | 建立 REST API 端點 | `fastapi-router-py`, `pydantic-models-py` |
| `create-store.prompt.md` | 建立 Zustand stores | `zustand-store-ts` |
| `create-node.prompt.md` | 建立 React Flow 節點 | `react-flow-node-ts` |
| `code-review.prompt.md` | 審查程式碼變更 | 任何領域 context 的技能 |

## 最佳實踐

### 1. 在提示詞之前載入技能

技能建立 context 和模式。提示詞建構執行。

```
正確：
1. 載入 azure-cosmos-db-py (建立模式)
2. 應用 add-endpoint.prompt.md (建構實作)

錯誤：
1. 應用 add-endpoint.prompt.md (無領域 context)
2. 載入 azure-cosmos-db-py (太遲了，未應用模式)
```

### 2. 限制活躍的技能

同時保持 2-3 個相關技能活躍。更多會導致語境稀釋。

```
優：fastapi-router-py + pydantic-models-py + azure-cosmos-db-py
劣：載入所有 127 個技能「以防萬一」
```

### 3. 為複雜領域鏈接技能

當任務橫跨多個領域時，依邏輯順序鏈接技能：

```
Authentication → Data Layer → API Layer → Frontend
azure-identity-py → azure-cosmos-db-py → fastapi-router-py → react-flow-node-ts
```

### 4. 使用提示詞提高可重複性

如果你經常執行相同的工作流程，請建立提示詞範本：

```markdown
---
name: new-azure-endpoint
description: Create a new Azure-backed API endpoint with full stack
---

## Steps

1. Load skills: azure-identity-py, [data-skill], fastapi-router-py
2. Create Pydantic models for request/response
3. Implement service layer with Azure SDK
4. Create FastAPI router with endpoint
5. Add authentication dependency
6. Write tests
```
