---
mode: ask
description: Create a new React Flow node component with proper typing, styling, and store integration
---

# 建立新節點類型 (Create New Node Type)

遵守既定模式為 CoreAI DIY 畫布建立一個新節點類型。

## 變數

- `NODE_TYPE`: 節點類型識別符 (例如 `my-node`)
- `NODE_NAME`: 顯示名稱 (例如 `MyNode`)
- `NODE_DESCRIPTION`: 節點用途的簡短描述
- `NODE_PROPERTIES`: 節點所需的關鍵屬性

## 步驟

### 1. 定義型別

新增至 `src/frontend/src/types/index.ts`：

```typescript
export interface ${NODE_NAME}Data extends Record<string, unknown> {
  title: string;
  // Add ${NODE_PROPERTIES}
}

export type ${NODE_NAME} = Node<${NODE_NAME}Data, '${NODE_TYPE}'>;
```

更新 `AppNode` 聯集 (union) 以包含 `${NODE_NAME}`。

### 2. 建立元件

建立 `src/frontend/src/components/nodes/${NODE_NAME}.tsx`：

```typescript
import { memo, useCallback } from 'react';
import { NodeProps, Node, Handle, Position, NodeResizer } from '@xyflow/react';
import { ${NODE_NAME}Data } from '@/types';
import { useAppStore } from '@/store';

type ${NODE_NAME}Props = NodeProps<Node<${NODE_NAME}Data>>;

export const ${NODE_NAME} = memo(function ${NODE_NAME}({
  id,
  data,
  selected,
}: ${NODE_NAME}Props) {
  const updateNode = useAppStore((state) => state.updateNode);
  const canvasMode = useAppStore((state) => state.canvasMode);
  
  return (
    <>
      {canvasMode === 'editing' && (
        <NodeResizer minWidth={200} minHeight={150} isVisible={selected} />
      )}
      <div className="bg-[var(--frontier-surface)] border-2 border-[var(--frontier-border)] rounded-xl p-4">
        <Handle type="target" position={Position.Top} />
        <h3 className="text-[var(--frontier-text)] font-medium">{data.title}</h3>
        {/* Add node content */}
        <Handle type="source" position={Position.Bottom} />
      </div>
    </>
  );
});
```

### 3. 從 Barrel 匯出

新增至 `src/frontend/src/components/nodes/index.ts`：

```typescript
export { ${NODE_NAME} } from './${NODE_NAME}';
```

### 4. 新增預設資料

在 `src/frontend/src/store/app-store.ts` 中，新增至 `getDefaultNodeData`：

```typescript
case '${NODE_TYPE}':
  return { title: 'New ${NODE_NAME}', ...data } as NodeDataMap[T];
```

### 5. 註冊節點類型

在畫布頁面中，新增至 `nodeTypes`：

```typescript
const nodeTypes: NodeTypes = {
  // ...existing types
  '${NODE_TYPE}': ${NODE_NAME},
};
```

### 6. 新增至選單

新增項目至 AddBlockMenu, ConnectMenu, 和 NodeContextMenu。

## 檢查清單

- [ ] `types/index.ts` 中的型別定義
- [ ] `components/nodes/` 中的元件
- [ ] Barrel export
- [ ] store 中的預設資料
- [ ] 已註冊於 nodeTypes
- [ ] 已新增至選單
- [ ] 鍵盤快速鍵 (選填)
- [ ] 已新增測試
