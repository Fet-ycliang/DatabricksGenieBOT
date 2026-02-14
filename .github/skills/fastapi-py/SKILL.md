---
name: fastapi-py
description: 使用 FastAPI 建置高效能 API。用於建立 REST 端點、使用 OpenAPI 記錄 API 或處理 HTTP 請求。
---

# FastAPI

建置穩健、高效能且具有自動 OpenAPI 文件的 API。

## 安裝

```bash
pip install "fastapi[standard]"
```

## 基本應用程式結構

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="My Service API",
    description="API for accessing Genie Service",
    version="1.0.0"
)

class Item(BaseModel):
    name: str
    description: str | None = None

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/items/")
async def create_item(item: Item):
    return item
```

## 執行伺服器

使用 `fastapi dev` 進行開發 (自動重新載入) 或 `fastapi run` 進行生產。

```bash
fastapi dev main.py
```

## 最佳實踐

### 1. 依賴注入 (Dependency Injection)

使用 `Depends` 處理共用邏輯，如資料庫連線或身份驗證。

```python
from fastapi import Depends

async def get_genie_service():
    service = GenieService()
    try:
        yield service
    finally:
        await service.close()

@app.post("/chat")
async def chat(
    query: str,
    service: GenieService = Depends(get_genie_service)
):
    return await service.ask(query)
```

### 2. 錯誤處理

使用 `HTTPException` 處理可預期的錯誤。

```python
@app.get("/items/{item_id}")
async def read_item(item_id: str):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    return items[item_id]
```

### 3. Pydantic 模型

務必使用 Pydantic 模型進行請求/回應驗證。這確保你的 OpenAPI 規格準確無誤。

### 4. CORS

如果你的前端位於不同網域，請啟用 CORS。

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 文件

FastAPI 自動產生：

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`

## 與 Bot Framework 整合

若要與你的 API 一起提供 Bot Framework 機器人服務：

```python
from fastapi import Request, Response
from botbuilder.core import BotFrameworkAdapter, TurnContext
from botbuilder.schema import Activity

# Assuming ADAPTER and BOT are initialized

@app.post("/api/messages")
async def messages(req: Request):
    if "application/json" in req.headers["content-type"]:
        body = await req.json()
    else:
        return Response(status_code=415)

    activity = Activity().deserialize(body)
    auth_header = req.headers.get("Authorization", "")

    try:
        response = await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
        if response:
            return vars(response)
        return Response(status_code=201)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```
