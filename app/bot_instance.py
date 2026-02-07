from botbuilder.core import MemoryStorage, ConversationState, UserState
from app.core.config import DefaultConfig
from app.core.adapter import ADAPTER
from app.services.genie import GenieService
from bot.handlers.bot import MyBot
from bot.dialogs.sso_dialog import SSODialog

CONFIG = DefaultConfig()

# Create MemoryStorage, ConversationState and UserState
MEMORY = MemoryStorage()
CONVERSATION_STATE = ConversationState(MEMORY)
USER_STATE = UserState(MEMORY)

# Create Dialog
DIALOG = SSODialog(CONFIG.CONNECTION_NAME)

# Create Genie Service
GENIE_SERVICE = GenieService(CONFIG)

# Create Bot
BOT = MyBot(CONFIG, GENIE_SERVICE, CONVERSATION_STATE, USER_STATE, DIALOG)
