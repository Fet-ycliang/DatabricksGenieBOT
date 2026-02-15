from botbuilder.core import MemoryStorage, ConversationState, UserState
from app.core.config import DefaultConfig
from app.core.adapter import ADAPTER
from app.services.genie import GenieService
from app.utils.session_manager import SessionManager
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

# Create Session Manager (啟動由 main.py 的 lifespan 處理)
SESSION_MANAGER = SessionManager(
    user_sessions=BOT.user_sessions,
    email_sessions=BOT.email_sessions,
    cleanup_interval=3600,  # 每小時清理一次
    session_timeout=4,  # 4 小時超時
)
