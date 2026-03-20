---
name: databricks-sdk-py
description: Databricks SDK for Python (databricks-sdk). Use when interacting with Databricks Workspace, Unity Catalog, or Genie API. Covers authentication, WorkspaceClient, and Genie conversation management.
---

# Databricks SDK for Python

Interact with Databricks Workspace resources including Genie spaces, SQL warehouses, and Unity Catalog.

## Installation

```bash
pip install databricks-sdk
```

## Environment Variables

```bash
DATABRICKS_HOST=https://<workspace>.cloud.databricks.com
DATABRICKS_TOKEN=dapi...
DATABRICKS_SPACE_ID=<genie-space-id>
```

## Authentication

Authentication is handled via `WorkspaceClient`. It automatically picks up environment variables, or you can pass them explicitly.

```python
import os
from databricks.sdk import WorkspaceClient

# Recommended: Use environment variables
w = WorkspaceClient()

# Explicit (if typically needed for multi-workspace)
w = WorkspaceClient(
    host=os.environ.get("DATABRICKS_HOST"),
    token=os.environ.get("DATABRICKS_TOKEN")
)
```

## Core Workflow: Genie API

The Genie API interactions often require using the `GenieAPI` service client effectively.

### Initialize Genie API

```python
from databricks.sdk.service.dashboards import GenieAPI

# Initialize via WorkspaceClient's api_client
genie_api = GenieAPI(w.api_client)
```

### Start Conversation & Wait for Result

```python
# Start a new conversation
initial_message = genie_api.start_conversation_and_wait(
    space_id=space_id,
    content="Show me sales data for last month"
)

print(f"Conversation ID: {initial_message.conversation_id}")
```

### Continue Conversation

```python
# Send follow-up message
message = genie_api.create_message_and_wait(
    space_id=space_id,
    conversation_id=conversation_id,
    content="Filter by region 'APAC'"
)
```

### Retrieve Query Results

When a message triggers a SQL query, you need to fetch the result from the attachment.

```python
# Check if there is a query result
if message.query_result:
    # Get attachment ID (usually the first one for the SQL query)
    attachment_id = message.attachments[0].attachment_id

    # Get the query result (execution status)
    query_result = genie_api.get_message_attachment_query_result(
        space_id=space_id,
        conversation_id=conversation_id,
        message_id=message.message_id,
        attachment_id=attachment_id
    )

    # If completed, fetch the actual data using Statement Execution API
    if query_result.statement_response.status.state == "SUCCEEDED":
        statement_id = query_result.statement_response.statement_id
        results = w.statement_execution.get_statement(statement_id)

        # Access data
        if results.result and results.result.data_array:
            for row in results.result.data_array:
                print(row)
```

## Best Practices

1.  **Use `_and_wait` methods**: Genie operations are asynchronous. Use `start_conversation_and_wait` and `create_message_and_wait` to simplify flow unless you need custom polling.
2.  **Handle Attachments**: Genie responses often contain attachments with SQL queries, text, or suggested questions. Always check `message.attachments`.
3.  **Statement Execution**: Genie executes queries via SQL Warhouse. Use `w.statement_execution` to retrieve the actual row data using the `statement_id` from the Genie response.
4.  **Error Handling**: Wrap interactions in `try/except` functionality, especially for `ResourceDoesNotExist` or authentication errors.

## Common Patterns

### Extracting Suggested Questions

```python
def extract_suggested_questions(message):
    questions = []
    if message.attachments:
        for attachment in message.attachments:
            if hasattr(attachment, 'suggested_questions') and attachment.suggested_questions:
                 questions.extend(attachment.suggested_questions.questions)
    return questions
```
