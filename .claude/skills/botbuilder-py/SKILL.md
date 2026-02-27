---
name: botbuilder-py
description: Microsoft Bot Framework SDK for Python (botbuilder-py). Use when developing chatbots, handling user activities, managing state, or sending Adaptive Cards.
---

# Microsoft Bot Framework SDK for Python

Build conversational bots using the Bot Framework SDK.

## Installation

```bash
pip install botbuilder-core botbuilder-integration-aiohttp botbuilder-schema
```

## Environment Variables

```bash
APP_ID=<microsoft-app-id>
APP_PASSWORD=<microsoft-app-password>
```

## Authentication & Adapter Setup

### Aiohttp Integration

```python
from botbuilder.core import BotFrameworkAdapterSettings, BotFrameworkAdapter
from botbuilder.integration.aiohttp import CloudAdapter, ConfigurationBotFrameworkAuthentication

# Production: CloudAdapter
ADAPTER = CloudAdapter(ConfigurationBotFrameworkAuthentication(config))

# Local Dev / Emulator: BotFrameworkAdapter
SETTINGS = BotFrameworkAdapterSettings("", "")
ADAPTER = BotFrameworkAdapter(SETTINGS)
```

## Core Workflow: Activity Handler

Subclass `ActivityHandler` to manage event-driven conversations.

```python
from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import Activity, ActivityTypes

class MyBot(ActivityHandler):
    async def on_message_activity(self, turn_context: TurnContext):
        # Handle user text message
        text = turn_context.activity.text
        if text:
             await turn_context.send_activity(f"You said: {text}")
        else:
             # Handle other message types (e.g. adaptive card submit)
             if turn_context.activity.value:
                 await self._handle_card_submit(turn_context)

    async def on_members_added_activity(self, members_added, turn_context):
        # Welcome new members
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Welcome to the bot!")
```

## Sending Adaptive Cards

Adaptive Cards are standard JSON-serialized card objects.

```python
from botbuilder.schema import Attachment, Activity, ActivityTypes
import json

def create_adaptive_card():
    card_content = {
        "type": "AdaptiveCard",
        "version": "1.3",
        "body": [
            {
                "type": "TextBlock",
                "text": "Hello, Adaptive Card!"
            }
        ]
    }

    return Attachment(
        content_type="application/vnd.microsoft.card.adaptive",
        content=card_content
    )

async def send_card(turn_context: TurnContext):
    card_attachment = create_adaptive_card()
    message = Activity(
        type=ActivityTypes.message,
        attachments=[card_attachment]
    )
    await turn_context.send_activity(message)
```

## Error Handling

Implement global error handling for the adapter.

```python
async def on_error(context: TurnContext, error: Exception):
    print(f"CRITICAL ERROR: {error}")
    await context.send_activity("The bot encountered an error or bug.")

ADAPTER.on_turn_error = on_error
```

## Best Practices

1.  **State Management**: Use `ConversationState` and `UserState` to persist data across turns.
2.  **Middleware**: Use middleware (e.g., `TranscriptLoggerMiddleware`) for logging and inspection.
3.  **Typing Indicator**: Send a typing activity (`ActivityTypes.typing`) before long-running operations (>1s).
4.  **Async/Await**: The SDK is fully async. Always await `send_activity` and other I/O bound calls.

## FastAPI Integration (Standard Pattern)

When using FastAPI, simply call `process_activity` in your route handler:

```python
# In your FastAPI route handler
async def messages(req: Request):
    # ... parse request ...
    response = await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
    return response
```

Ensure your `ADAPTER` is a `CloudAdapter` (for production) or `BotFrameworkAdapter` (for local dev) configured with `aiohttp` compatible settings, as FastAPI handles the underlying async storage similarly.
