---
mode: ask
description: Create a new Zustand store with subscribeWithSelector middleware
---

# 建立 Zustand Store (Create Zustand Store)

遵守 CoreAI DIY 模式建立一個新的 Zustand store。

## 變數

- `STORE_NAME`: Store 名稱 (例如 `settings`)
- `STORE_DESCRIPTION`: Store 管理內容的簡短描述
- `STATE_FIELDS`: 關鍵狀態欄位
- `ACTIONS`: Store 所需的關鍵動作

## 步驟

### 1. 建立 Store 檔案

建立 `src/frontend/src/store/${STORE_NAME}-store.ts`：

```typescript
import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';

// State interface
export interface ${STORE_NAME.charAt(0).toUpperCase() + STORE_NAME.slice(1)}State {
  // Add ${STATE_FIELDS}
  isLoading: boolean;
  error: string | null;
}

// Actions interface
export interface ${STORE_NAME.charAt(0).toUpperCase() + STORE_NAME.slice(1)}Actions {
  // Add ${ACTIONS}
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

// Combined store type
export type ${STORE_NAME.charAt(0).toUpperCase() + STORE_NAME.slice(1)}Store = 
  ${STORE_NAME.charAt(0).toUpperCase() + STORE_NAME.slice(1)}State & 
  ${STORE_NAME.charAt(0).toUpperCase() + STORE_NAME.slice(1)}Actions;

// Initial state
const initialState: ${STORE_NAME.charAt(0).toUpperCase() + STORE_NAME.slice(1)}State = {
  // Initialize ${STATE_FIELDS}
  isLoading: false,
  error: null,
};

// Create store with subscribeWithSelector
export const use${STORE_NAME.charAt(0).toUpperCase() + STORE_NAME.slice(1)}Store = create<${STORE_NAME.charAt(0).toUpperCase() + STORE_NAME.slice(1)}Store>()(
  subscribeWithSelector((set, get) => ({
    ...initialState,
    
    // Add action implementations
    
    setLoading: (loading) => set({ isLoading: loading }),
    
    setError: (error) => set({ error }),
    
    reset: () => set(initialState),
  }))
);
```

### 2. 從 Barrel 匯出

新增至 `src/frontend/src/store/index.ts`：

```typescript
export { use${STORE_NAME.charAt(0).toUpperCase() + STORE_NAME.slice(1)}Store } from './${STORE_NAME}-store';
export type {
  ${STORE_NAME.charAt(0).toUpperCase() + STORE_NAME.slice(1)}State,
  ${STORE_NAME.charAt(0).toUpperCase() + STORE_NAME.slice(1)}Actions,
  ${STORE_NAME.charAt(0).toUpperCase() + STORE_NAME.slice(1)}Store,
} from './${STORE_NAME}-store';
```

### 3. 在元件中使用

```typescript
import { use${STORE_NAME.charAt(0).toUpperCase() + STORE_NAME.slice(1)}Store } from '@/store';

function MyComponent() {
  // Select specific state (prevents unnecessary re-renders)
  const value = use${STORE_NAME.charAt(0).toUpperCase() + STORE_NAME.slice(1)}Store((state) => state.value);
  const action = use${STORE_NAME.charAt(0).toUpperCase() + STORE_NAME.slice(1)}Store((state) => state.action);
  
  // Or use multiple selectors
  const { value, action } = use${STORE_NAME.charAt(0).toUpperCase() + STORE_NAME.slice(1)}Store((state) => ({
    value: state.value,
    action: state.action,
  }));
  
  return <button onClick={() => action(newValue)}>Update</button>;
}
```

### 4. 訂閱變更 (選填)

```typescript
// Subscribe to specific state changes
use${STORE_NAME.charAt(0).toUpperCase() + STORE_NAME.slice(1)}Store.subscribe(
  (state) => state.value,
  (value, prevValue) => {
    console.log('Value changed from', prevValue, 'to', value);
  }
);
```

## 模式

### 非同步動作 (Async Actions)
```typescript
loadData: async () => {
  set({ isLoading: true, error: null });
  try {
    const data = await fetchData();
    set({ data, isLoading: false });
  } catch (error) {
    set({ error: error.message, isLoading: false });
  }
},
```

### 計算值 (Computed Values)
```typescript
// Use get() to access current state
getFilteredItems: () => {
  const { items, filter } = get();
  return items.filter(item => item.matches(filter));
},
```

### 批次更新 (Batch Updates)
```typescript
// Single set() call for multiple updates
updateMultiple: (updates) => {
  set({
    field1: updates.field1,
    field2: updates.field2,
    field3: updates.field3,
  });
},
```

## 檢查清單

- [ ] Store 檔案已建立並使用 subscribeWithSelector
- [ ] State 介面已定義
- [ ] Actions 介面已定義
- [ ] Initial state 已定義
- [ ] 已從 Barrel 匯出
- [ ] 已新增測試
