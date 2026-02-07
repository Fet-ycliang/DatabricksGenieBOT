---
name: fastapi-py
description: Build high-performance APIs with FastAPI. Use when creating REST endpoints, documenting APIs with OpenAPI, or handling HTTP requests.
---

# FastAPI

Build robust, high-performance APIs with automatic OpenAPI documentation.

## Installation

```bash
pip install "fastapi[standard]"
```

## Basic App Structure

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

## Running the Server

Use `fastapi dev` for development (auto-reload) or `fastapi run` for production.

```bash
fastapi dev main.py
```

## Best Practices

### 1. Dependency Injection

Use `Depends` to handle shared logic like database connections or authentication.

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

### 2. Error Handling

Use `HTTPException` for predictable errors.

```python
@app.get("/items/{item_id}")
async def read_item(item_id: str):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    return items[item_id]
```

### 3. Pydantic Models

Always use Pydantic models for request/response validation. This ensures your OpenAPI spec is accurate.

### 4. CORS

If your frontend is on a different domain, enable CORS.

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

## Documentation

FastAPI automatically generates:

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`

## Integration with Bot Framework

To serve a Bot Framework bot alongside your API:

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
