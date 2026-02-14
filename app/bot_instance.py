from botbuilder.core import MemoryStorage, ConversationState, UserState
from app.core.config import DefaultConfig
from app.core.adapter import ADAPTER
from app.services.genie import GenieService
from app.core.m365_agent_framework import M365AgentFramework
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

# Initialize Microsoft 365 Agent Framework
try:
    M365_AGENT_FRAMEWORK = M365AgentFramework(CONFIG)
except Exception as e:
    print(f"Warning: Failed to initialize M365 Agent Framework: {str(e)}")
    M365_AGENT_FRAMEWORK = None


# Create Bot
BOT = MyBot(CONFIG, GENIE_SERVICE, CONVERSATION_STATE, USER_STATE, DIALOG, M365_AGENT_FRAMEWORK)
