---
name: M365 Agent Framework SDK
description: Guide for developing Microsoft 365 Agents using Python, Bot Framework, and Graph API.
---

# Microsoft 365 Agent Framework Skill

This skill provides guidance and standardized patterns for building Microsoft 365 Agents (Copilot extensions, Teams bots) using the Python SDK stack.

## Core Components
Your agent likely uses the following stack:
- **Bot Framework SDK (`botbuilder-core`)**: Handles the conversational logic and activity processing.
- **Teams AI Library / M365 Agents SDK**: Manages state, AI interactions, and Teams-specific features.
- **Microsoft Graph SDK (`msgraph-sdk`)**: Accesses M365 data (Calendar, Mail, Files).
- **Adaptive Cards**: The primary UI for M365 agents.

## Development Workflow

### 1. Project Structure
Maintain a clean separation of concerns:
- `bot/`: Contains bot activity handlers (e.g., `TeamsActivityHandler`).
- `models/`: Pydantic models for data and state.
- `services/`: Business logic, Graph API wrappers, and external integrations.
- `app.py` / `main.py`: Entry point for the FastAPI/AIOHTTP server.

### 2. Handling Activities
Agents communicate via Activities. Ensure your bot handler (`bot/bot_instance.py`) correctly routes:
- **Message Activities**: Standard chat interactions.
- **Invoke Activities**: Adaptive Card actions and Message Extensions.
- **Conversation Update**: Welcome messages when the bot is added.

```python
# Example: Basic Activity Handler
from botbuilder.core import TurnContext, ActivityHandler
from botbuilder.schema import ActivityTypes

class MyAgent(ActivityHandler):
    async def on_message_activity(self, turn_context: TurnContext):
        await turn_context.send_activity(f"You said: {turn_context.activity.text}")

    async def on_members_added_activity(self, members_added, turn_context):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Hello and welcome!")
```

### 3. Microsoft Graph Integration
Use `msgraph-sdk` with `azure-identity` for secure access.
- **Auth**: Use `OnBehalfOfCredential` or `ClientSecretCredential` depending on the flow.
- **Scopes**: Define minimal required scopes (e.g., `User.Read`, `Calendars.Read`).

```python
# Example: Graph Client Initialization
from azure.identity import ClientSecretCredential
from msgraph import GraphServiceClient

def get_graph_client():
    cred = ClientSecretCredential(tenant_id, client_id, client_secret)
    return GraphServiceClient(credentials=cred, scopes=["https://graph.microsoft.com/.default"])
```

### 4. Adaptive Cards
Use Adaptive Cards for rich interactions.
- Store card templates in `resources/` or `cards/` as JSON.
- Use `Attachment` to send cards.

## Common Tasks & Snippets

### Sending an Adaptive Card
```python
from botbuilder.schema import Attachment
import json

def create_card_attachment(card_path):
    with open(card_path, "r") as f:
        card_data = json.load(f)
    return Attachment(
        content_type="application/vnd.microsoft.card.adaptive",
        content=card_data
    )
```

### Implementing a Message Extension (Search)
Handle the `composeExtension/query` invoke activity in your bot handler to return search results for the M365 Copilot / Teams search bar.

## Troubleshooting
- **Bot Not Responding**: Check if your endpoint is publicly accessible (use dev tunnels) and matches the Manifest.
- **Auth Errors**: Verify `AZURE_TENANT_ID`, `client_id`, and `client_secret` in `.env`.
- **403 Forbidden**: Ensure the App Registration in Azure AD has the correct API Permissions granted.

## Templates
Find ready-to-use templates in the `templates/` directory:
- `templates/declarativeAgent.json`: Starting point for M365 Copilot extensions.
- `templates/manifest.json`: Standard Teams App Manifest for bot deployment.

