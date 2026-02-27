import logging
from datetime import datetime, timezone
from botbuilder.core import BotFrameworkAdapterSettings, BotFrameworkAdapter
from botbuilder.schema import Activity, ActivityTypes
from app.core.config import DefaultConfig

logger = logging.getLogger(__name__)

CONFIG = DefaultConfig()

# 用於使用 Bot Framework Emulator 進行本地開發，使用 BotFrameworkAdapter
# 生產環境或具有完整憑證時使用 BotFrameworkAdapter
SETTINGS = BotFrameworkAdapterSettings(CONFIG.APP_ID or "", CONFIG.APP_PASSWORD or "")
ADAPTER = BotFrameworkAdapter(SETTINGS)

async def on_error(context, error):
    logger.error("[on_turn_error] unhandled error: %s", error, exc_info=True)

    # Send a message to the user
    await context.send_activity("The bot encountered an error or bug.")
    await context.send_activity("To continue to run this bot, please fix the bot source code.")
    # Send a trace activity if we're talking to the Bot Framework Emulator
    if context.activity.channel_id == 'emulator':
        trace_activity = Activity(
            label="TurnError",
            name="on_turn_error Trace",
            timestamp=datetime.now(timezone.utc),
            type=ActivityTypes.trace,
            value=f"{error}",
            value_type="https://www.botframework.com/schemas/error"
        )
        await context.send_activity(trace_activity)

ADAPTER.on_turn_error = on_error
