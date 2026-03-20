---
name: databricks-sdk-py
description: Databricks SDK for Python (databricks-sdk). Use when interacting with Databricks Workspace, Unity Catalog, or Genie API. Covers authentication, WorkspaceClient, and Genie conversation management.
---

# Databricks SDK for Python

與 Databricks Workspace 資源互動，包括 Genie spaces、SQL warehouses 和 Unity Catalog。

## 安裝

```bash
pip install databricks-sdk
```

## 環境變數

```bash
DATABRICKS_HOST=https://<workspace>.cloud.databricks.com
DATABRICKS_TOKEN=dapi...
DATABRICKS_SPACE_ID=<genie-space-id>
```

## 身份驗證

身份驗證透過 `WorkspaceClient` 處理。它會自動讀取環境變數，你也可以明確傳遞它們。

```python
import os
from databricks.sdk import WorkspaceClient

# 推薦：使用環境變數
w = WorkspaceClient()

# 明確指定 (通常用於多 workspace 場景)
w = WorkspaceClient(
    host=os.environ.get("DATABRICKS_HOST"),
    token=os.environ.get("DATABRICKS_TOKEN")
)
```

## 核心工作流程：Genie API

Genie API 互動通常需要有效地使用 `GenieAPI` 服務用戶端。

### 初始化 Genie API

```python
from databricks.sdk.service.dashboards import GenieAPI

# 初始化 (透過 WorkspaceClient 的 api_client)
genie_api = GenieAPI(w.api_client)
```

### 開始對話並等待結果

```python
# 開始新對話
initial_message = genie_api.start_conversation_and_wait(
    space_id=space_id,
    content="Show me sales data for last month"
)

print(f"Conversation ID: {initial_message.conversation_id}")
```

### 繼續對話

```python
# 發送後續訊息
message = genie_api.create_message_and_wait(
    space_id=space_id,
    conversation_id=conversation_id,
    content="Filter by region 'APAC'"
)
```

### 檢索查詢結果

當訊息觸發 SQL 查詢時，你需要從附件中擷取結果。

```python
# 檢查是否有查詢結果
if message.query_result:
    # 取得附件 ID (通常第一個是 SQL 查詢)
    attachment_id = message.attachments[0].attachment_id

    # 取得查詢結果 (執行狀態)
    query_result = genie_api.get_message_attachment_query_result(
        space_id=space_id,
        conversation_id=conversation_id,
        message_id=message.message_id,
        attachment_id=attachment_id
    )

    # 如果完成，使用 Statement Execution API 擷取實際資料
    if query_result.statement_response.status.state == "SUCCEEDED":
        statement_id = query_result.statement_response.statement_id
        results = w.statement_execution.get_statement(statement_id)

        # 存取資料
        if results.result and results.result.data_array:
            for row in results.result.data_array:
                print(row)
```

## 最佳實踐

1.  **使用 `_and_wait` 方法**：Genie 操作是非同步的。除非你需要自訂輪詢，否則使用 `start_conversation_and_wait` 和 `create_message_and_wait` 來簡化流程。
2.  **處理附件 (Handle Attachments)**：Genie 回應通常包含帶有 SQL 查詢、文字或建議問題的附件。務必檢查 `message.attachments`。
3.  **Statement Execution**：Genie 透過 SQL Warehouse 執行查詢。使用 `w.statement_execution` 並搭配 Genie 回應中的 `statement_id` 來檢索實際的資料列。
4.  **錯誤處理**：將互動包裝在 `try/except` 功能中，特別是針對 `ResourceDoesNotExist` 或身份驗證錯誤。

## 常見模式

### 提取建議問題

```python
def extract_suggested_questions(message):
    questions = []
    if message.attachments:
        for attachment in message.attachments:
            if hasattr(attachment, 'suggested_questions') and attachment.suggested_questions:
                 questions.extend(attachment.suggested_questions.questions)
    return questions
```
