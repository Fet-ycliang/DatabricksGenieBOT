import sys
import traceback
from datetime import datetime
from botbuilder.core import BotFrameworkAdapterSettings, BotFrameworkAdapter
from botbuilder.schema import Activity, ActivityTypes
from app.core.config import DefaultConfig

CONFIG = DefaultConfig()

# 用於使用 Bot Framework Emulator 進行本地開發，使用 BotFrameworkAdapter
# 生產環境或具有完整憑證時使用 BotFrameworkAdapter
SETTINGS = BotFrameworkAdapterSettings(CONFIG.APP_ID or "", CONFIG.APP_PASSWORD or "")
ADAPTER = BotFrameworkAdapter(SETTINGS)

async def on_error(context, error):
    # This check writes out errors to console log .vs. app insights.
    # NOTE: In production environment, you should consider logging this to Azure
    #       application insights.
    print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()

    # Send a message to the user
    await context.send_activity("The bot encountered an error or bug.")
    await context.send_activity("To continue to run this bot, please fix the bot source code.")
    # Send a trace activity if we're talking to the Bot Framework Emulator
    if context.activity.channel_id == 'emulator':
        # Create a trace activity that contains the error object
        trace_activity = Activity(
            label="TurnError",
            name="on_turn_error Trace",
            timestamp=datetime.utcnow(),
            type=ActivityTypes.trace,
            value=f"{error}",
            value_type="https://www.botframework.com/schemas/error"
        )
        # Send a trace activity, which will be displayed in Bot Framework Emulator
        await context.send_activity(trace_activity)

ADAPTER.on_turn_error = on_error
