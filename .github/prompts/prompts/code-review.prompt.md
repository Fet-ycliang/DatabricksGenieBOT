---
mode: ask
description: Comprehensive code review checklist for CoreAI DIY contributions
---

# 程式碼審查檢查清單 (Code Review Checklist)

在審查 CoreAI DIY 中的程式碼變更時使用此檢查清單。

## 一般

- [ ] 程式碼遵循 AGENTS.md 中的模式
- [ ] 沒有 TypeScript `any` 型別
- [ ] 沒有硬編碼的顏色 (使用設計 tokens)
- [ ] 生產環境程式碼中沒有 console.log 語句
- [ ] 沒有被註解掉的程式碼區塊
- [ ] 變數/函式名稱清晰且具描述性
- [ ] 適當的錯誤處理

## 前端 (React/TypeScript)

### Components (元件)
- [ ] React Flow 節點使用 `memo()` + 具名函式模式
- [ ] 正確的 TypeScript 型別 (沒有隱式 any)
- [ ] 使用設計 tokens (`--frontier-*`, `--foundry-*`)
- [ ] 條件式類別使用 `cn()` 工具函式
- [ ] 元件資料夾中有 Barrel export

### State (狀態 - Zustand)
- [ ] 使用 `subscribeWithSelector` 中介軟體
- [ ] 選擇特定狀態 (而非整個 store)
- [ ] Actions 正確地以不可變 (immutably) 方式更新
- [ ] 型別已匯出 (State, Actions, Store)

### React Flow Nodes (節點)
- [ ] 尊重 `canvasMode` (檢視 vs 編輯)
- [ ] 具有適當的 Handle 元件
- [ ] NodeResizer 僅在編輯模式下出現
- [ ] 使用 `NodeProps<Node<DataType>>`

## 後端 (FastAPI/Python)

### Pydantic Models (模型)
- [ ] 多模型模式 (Base → Create → Update → Response → InDB)
- [ ] 使用 `Field(..., alias="camelCase")` 以相容 JSON
- [ ] Config 具有 `populate_by_name = True`
- [ ] Response model 具有 `from_attributes = True`

### Routers (路由器)
- [ ] 適當的身份驗證依賴項 (`get_current_user` vs `get_current_user_required`)
- [ ] 回傳適當的 HTTP 狀態碼
- [ ] 已定義 response_model
- [ ] 發生錯誤時引發 HTTPException

### Services (服務)
- [ ] 處理 Cosmos DB 可用性 (`_use_cosmos()`)
- [ ] 正確使用 async/await
- [ ] 資料庫操作的錯誤處理

## 安全性

- [ ] 程式碼或註解中沒有秘密
- [ ] 寫入操作需要身份驗證
- [ ] 透過 Pydantic 進行輸入驗證
- [ ] 沒有 SQL/NoSQL 隱碼攻擊漏洞

## 效能

- [ ] React 元件已適當 memoized
- [ ] 沒有不必要的重新渲染 (使用 selectors)
- [ ] 昂貴的計算已 memoized
- [ ] API 呼叫不在 render 路徑中

## 測試

- [ ] 新函式的單元測試
- [ ] 新 UI 的元件測試
- [ ] 新端點的 API 測試
- [ ] 本地測試通過

## 文件

- [ ] 複雜邏輯有註解
- [ ] 公開 API 有 docstrings
- [ ] 若有的話，README 已更新
- [ ] 型別具有自我文件化特性

## Commit (提交)

- [ ] 遵循 conventional commit 格式
- [ ] Commit 訊息描述了「為什麼」，而不僅僅是「什麼」
- [ ] 沒有包含無關的變更
- [ ] `pnpm lint` 通過
- [ ] `pnpm build` 通過
- [ ] `uv run pytest` 通過
