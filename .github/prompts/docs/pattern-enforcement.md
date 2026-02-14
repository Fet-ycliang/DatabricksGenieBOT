# 使用技能強制執行模式

技能如何跨團隊強制執行編碼模式、標準和最佳實踐。

## 技能如何強制執行模式

技能包含 Agent 遵循的明確指引。當技能說「總是使用 X」時，Agent 就會一致地應用該模式。

### 範例：身份驗證模式強制執行

`azure-identity-py` 技能包含：

```markdown
## Authentication

生產環境程式碼請務必使用 `DefaultAzureCredential`：

```python
from azure.identity import DefaultAzureCredential
from azure.cosmos import CosmosClient

credential = DefaultAzureCredential()
client = CosmosClient(url=endpoint, credential=credential)
```

絕不在程式碼中硬編碼 (hardcode) 憑證或使用連接字串。
```

**結果**：載入了此技能的每個 Agent 都將使用 `DefaultAzureCredential`，絕不會使用硬編碼的秘密。

## 技能強制執行的標準模式

### 1. 身份驗證 (azure-identity-py)

| 強執行的模式 | 防止的反模式 |
|------------------|------------------------|
| `DefaultAzureCredential` | 硬編碼的憑證 |
| 環境變數用於設定 | 程式碼中的秘密 |
| 生產環境使用受控識別 | 連接字串 |

### 2. 錯誤處理 (所有技能)

| 強執行的模式 | 防止的反模式 |
|------------------|------------------------|
| 明確的例外處理 | 空的 `except:` 區塊 |
| 特定的例外類型 | 捕捉 `Exception` (通用例外) |
| 有意義的錯誤訊息 | 靜默失敗 |

### 3. Async/Await (Azure SDK 技能)

| 強執行的模式 | 防止的反模式 |
|------------------|------------------------|
| I/O 使用 `async/await` | 阻塞式同步呼叫 |
| Context managers | 未關閉的用戶端 |
| 適當的用戶端生命週期 | 資源洩漏 |

### 4. 型別安全 (所有技能)

| 強執行的模式 | 防止的反模式 |
|------------------|------------------------|
| 函式上的型別提示 | 未定義型別的參數 |
| Pydantic 模型 | 原始 dicts |
| 明確的回傳型別 | 隱式 `Any` |

## 團隊標準化

### 跨專案共享技能

團隊可以透過共享相同的技能集來強制執行一致的模式：

```bash
# 團隊技能儲存庫
team-skills/
├── .github/skills/
│   ├── azure-identity-py/      # 身份驗證模式
│   ├── azure-cosmos-db-py/     # 資料層模式
│   ├── fastapi-router-py/      # API 模式
│   └── team-conventions/       # 自訂團隊規則
```

每個專案都建立指向團隊技能的符號連結 (symlink)：

```bash
# 在每個專案中
ln -s /path/to/team-skills/.github/skills .github/skills
```

**結果**：所有專案都使用相同的模式。更新會即時傳播。

### 自訂團隊技能 (Custom Team Skills)

為內部慣例建立特定於團隊的技能：

```markdown
---
name: team-conventions
description: 平台團隊的內部編碼標準
---

# Team Conventions

## API Response Format

所有端點必須回傳：
```python
{
    "data": <result>,
    "meta": {
        "request_id": str,
        "timestamp": str
    }
}
```

## Logging

使用帶有 correlation IDs 的結構化日誌記錄：
```python
logger.info("Operation completed", extra={
    "correlation_id": request.state.correlation_id,
    "operation": "create_user",
    "duration_ms": elapsed
})
```

## Database Queries

總是使用參數化查詢：
```python
# 正確
query = "SELECT * FROM c WHERE c.id = @id"
params = [{"name": "@id", "value": user_id}]

# 錯誤 - SQL 隱碼攻擊風險
query = f"SELECT * FROM c WHERE c.id = '{user_id}'"
```
```

## 強制執行驗證

### Pre-Commit 檢查

技能與自動驗證搭配使用效果最佳：

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: type-check
        name: Type checking
        entry: mypy src/
        language: system
        
      - id: lint
        name: Linting
        entry: ruff check src/
        language: system
```

### 程式碼審查檢查清單

技能提供隱式的審查標準：

| 若載入了技能 | 審查者檢查 |
|-----------------|-----------------|
| `azure-identity-py` | 沒有硬編碼的憑證？ |
| `azure-cosmos-db-py` | 分割區索引鍵策略有文件記錄？ |
| `fastapi-router-py` | 回應模型已定義？ |
| `pydantic-models-py` | 正確使用模型變體？ |

## 模式強制執行範例

### 範例 1：Cosmos DB 服務層

**技能**：`azure-cosmos-db-py`

**強制執行的模式**：
- 服務類別封裝 CosmosClient
- 分割區索引鍵包含在所有操作中
- 為了安全使用參數化查詢
- 雙重身份驗證支援 (DefaultAzureCredential + 模擬器)

```python
# Agent 一致地產生此模式
class UserService:
    def __init__(self, client: CosmosClient, database: str, container: str):
        self.container = client.get_database_client(database).get_container_client(container)
    
    async def get_user(self, user_id: str, partition_key: str) -> User:
        query = "SELECT * FROM c WHERE c.id = @id"
        params = [{"name": "@id", "value": user_id}]
        items = self.container.query_items(query, parameters=params, partition_key=partition_key)
        # ...
```

### 範例 2：FastAPI Router

**技能**：`fastapi-router-py`

**強制執行的模式**：
- 帶有前綴和標籤的 Router
- 用於身份驗證的依賴注入
- Pydantic 回應模型
- 適當的 HTTP 狀態碼

```python
# Agent 一致地產生此模式
router = APIRouter(prefix="/users", tags=["users"])

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
) -> UserResponse:
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.from_orm(user)
```

### 範例 3：Pydantic 模型

**技能**：`pydantic-models-py`

**強制執行的模式**：
- 帶有共用欄位的基底模型
- 建立模型 (沒有 id，沒有時間戳記)
- 更新模型 (全選填)
- 回應模型 (計算欄位)
- InDB 模型 (有 id、時間戳記)

```python
# Agent 一致地產生此模式
class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: EmailStr | None = None
    name: str | None = None

class UserResponse(UserBase):
    id: str
    created_at: datetime

class UserInDB(UserResponse):
    hashed_password: str
```

## 基於技能強制執行的好處

| 好處 | 技能如何達成 |
|---------|----------------------|
| **一致性** | 所有程式碼使用相同的模式 |
| **入職 (Onboarding)** | 新開發者繼承團隊標準 |
| **維護** | 更新技能 = 更新所有未來的程式碼 |
| **稽核** | 技能記錄「為什麼」而不僅僅是「什麼」 |
| **演進** | 模式隨時間改進 |
