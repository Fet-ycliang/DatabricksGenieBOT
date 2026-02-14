"""
CommandSkill - 命令處理技能

遷移自 bot/handlers/commands.py
負責處理特殊命令、顯示幫助信息、用戶信息查詢
"""

from typing import Dict, Optional, Any, List
from datetime import datetime
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class CommandResponse:
    """命令回應"""
    handled: bool = False
    message: Optional[str] = None
    card_data: Optional[Dict] = None
    requires_graph_api: bool = False
    command_type: Optional[str] = None
    error: Optional[str] = None


class CommandSkill:
    """
    命令處理技能
    
    處理:
    - /help, /info 幫助命令
    - /whoami, /me 用戶信息查詢
    - /logout 登出命令
    - /reset, new chat 重置對話
    - /setuser 設置用戶（測試模式）
    """
    
    def __init__(self):
        """初始化命令處理技能"""
        self.name = "命令處理技能"
        self.supported_commands = [
            "/help", "help", "/info", "info",
            "/whoami", "whoami", "/me", "me",
            "/logout", "logout",
            "/reset", "reset", "new chat",
            "/setuser"
        ]
        logger.info(f"初始化 {self.name}")
    
    async def handle_command(
        self,
        command: str,
        user_id: str,
        user_name: Optional[str] = None,
        user_email: Optional[str] = None,
        conversation_id: Optional[str] = None,
        channel_id: Optional[str] = None,
        admin_contact: Optional[str] = "admin@example.com"
    ) -> CommandResponse:
        """
        處理命令
        
        Args:
            command: 命令文本
            user_id: 用戶 ID
            user_name: 用戶名稱
            user_email: 用戶電子郵件
            conversation_id: 對話 ID
            channel_id: 頻道 ID
            admin_contact: 管理員聯繫方式
            
        Returns:
            CommandResponse: 命令處理結果
        """
        try:
            command_lower = command.lower().strip()
            
            # 檢查是否為支持的命令
            if not await self.is_command(command):
                return CommandResponse(handled=False)
            
            # 路由到相應的處理器
            if command_lower in ["/help", "help", "/commands", "commands", "information", "about"]:
                return await self._handle_help_command(admin_contact)
            
            elif command_lower in ["/info", "info"]:
                return await self._handle_info_command(user_name, conversation_id)
            
            elif command_lower in ["/whoami", "whoami", "who am i", "/me", "me"]:
                return await self._handle_whoami_command(
                    user_id, user_name, user_email, conversation_id
                )
            
            elif command_lower in ["/logout", "logout", "sign out", "disconnect"]:
                return await self._handle_logout_command(user_name)
            
            elif await self._is_reset_command(command_lower):
                return await self._handle_reset_command(user_name)
            
            elif command_lower.startswith("/setuser ") and channel_id == "emulator":
                return await self._handle_setuser_command(command, user_id)
            
            return CommandResponse(handled=False)
            
        except Exception as e:
            logger.error(f"處理命令失敗: {str(e)}")
            return CommandResponse(
                handled=True,
                error=str(e),
                message="❌ 處理命令時發生錯誤。"
            )
    
    async def is_command(self, text: str) -> bool:
        """
        檢查文本是否為命令
        
        Args:
            text: 輸入文本
            
        Returns:
            bool: 是否為命令
        """
        text_lower = text.lower().strip()
        
        # 檢查完整匹配
        for cmd in self.supported_commands:
            if text_lower == cmd or text_lower.startswith(cmd + " "):
                return True
        
        # 檢查重置命令
        if await self._is_reset_command(text_lower):
            return True
        
        return False
    
    async def get_available_commands(self, include_emulator: bool = False) -> List[Dict[str, str]]:
        """
        獲取可用命令列表
        
        Args:
            include_emulator: 是否包含模擬器命令
            
        Returns:
            List[Dict]: 命令列表
        """
        commands = [
            {
                "command": "help",
                "description": "顯示機器人資訊和使用說明"
            },
            {
                "command": "info",
                "description": "獲取入門協助和當前狀態"
            },
            {
                "command": "whoami 或 /me",
                "description": "顯示您的使用者資訊"
            },
            {
                "command": "reset 或 new chat",
                "description": "開始新的對話"
            },
            {
                "command": "logout",
                "description": "清除您的工作階段"
            }
        ]
        
        if include_emulator:
            commands.append({
                "command": "/setuser email@example.com Name",
                "description": "設定測試用戶身分（僅限模擬器）"
            })
        
        return commands
    
    def get_capability_description(self) -> Dict[str, Any]:
        """
        獲取技能描述
        
        Returns:
            Dict: 技能描述信息
        """
        return {
            "name": self.name,
            "description": "處理各種機器人命令，包括幫助、用戶信息、登出等",
            "methods": {
                "handle_command": "處理命令並返回結果",
                "is_command": "檢查文本是否為命令",
                "get_available_commands": "獲取可用命令列表",
                "parse_command": "解析命令參數"
            },
            "supported_commands": self.supported_commands
        }
    
    # === Private Methods ===
    
    async def _handle_help_command(self, admin_contact: str) -> CommandResponse:
        """處理 help 命令"""
        help_text = """🤖 **Databricks Genie 機器人資訊**

**我能做什麼：**
我是一個 Teams 聊天機器人，會自動連接到 Databricks Genie Space，讓您可以直接在 Teams 中透過自然語言來查詢，與您的資料互動。

**我如何運作：**

    • 我使用預先設定的憑證連接到您的 Databricks 工作區

    • 您的對話上下文會在工作階段之間保留，以保持連續性

    • 我會記住我們的對話歷史，以提供更好的後續回應

**工作階段管理：**

    • 對話在閒置 **4 小時** 後會自動重置

    • 您可以隨時輸入 `reset` 或 `new chat` 手動重置
    • 您的電子郵件 **僅用於在 Genie 中記錄查詢** - 不用於 AI 處理

**可用指令：**

    • `help` - 顯示此資訊

    • `info` - 獲取入門協助

    • `whoami` 或 `/me` - 顯示您的使用者資訊和 Graph API 資料

    • `reset` - 開始新的對話

    • `new chat` - 開始新的對話

    • `logout` - 清除您的工作階段

**需要協助？**
請聯絡機器人管理員：""" + admin_contact
        
        return CommandResponse(
            handled=True,
            message=help_text,
            command_type="help"
        )
    
    async def _handle_info_command(
        self,
        user_name: Optional[str],
        conversation_id: Optional[str]
    ) -> CommandResponse:
        """處理 info 命令"""
        display_name = user_name or "用戶"
        status = "新對話" if conversation_id is None else "繼續現有對話"
        
        info_text = f"""🤖 **Databricks Genie 機器人指令**

**👤 使用者：** {display_name}

**開始新對話：**
- `reset` 或 `new chat`

**使用者指令：**
- `whoami` 或 `/me` - 顯示您的使用者資訊（包括 Graph API 資料卡片）
- `help` - 顯示詳細的機器人資訊
- `logout` - 清除您的工作階段（您將在下一條訊息中重新識別）

**一般用法：**
- 詢問我任何有關您資料的問題
- 我會記住我們的對話上下文
- 需要時使用上述指令重新開始

**目前狀態：** {status}
"""
        
        return CommandResponse(
            handled=True,
            message=info_text,
            command_type="info"
        )
    
    async def _handle_whoami_command(
        self,
        user_id: str,
        user_name: Optional[str],
        user_email: Optional[str],
        conversation_id: Optional[str]
    ) -> CommandResponse:
        """處理 whoami 命令"""
        name = user_name or "未知"
        email = user_email or "未設定"
        conv_id = conversation_id or "無 (新對話)"
        
        user_info = f"""👤 **您的資訊**

**名稱：** {name}

**電子郵件：** {email}

**使用者 ID：** {user_id}

**對話 ID：** {conv_id}
"""
        
        return CommandResponse(
            handled=True,
            message=user_info,
            command_type="whoami",
            requires_graph_api=True,  # 指示需要 Graph API 增強
            card_data={
                "type": "user_profile",
                "user_id": user_id,
                "user_name": name,
                "user_email": email
            }
        )
    
    async def _handle_logout_command(self, user_name: Optional[str]) -> CommandResponse:
        """處理 logout 命令"""
        name = user_name or "用戶"
        
        logout_text = f"""👋 **再見 {name}！**

您的工作階段已清除。當您發送下一條訊息時，將重新識別您的身分。
"""
        
        return CommandResponse(
            handled=True,
            message=logout_text,
            command_type="logout"
        )
    
    async def _handle_reset_command(self, user_name: Optional[str]) -> CommandResponse:
        """處理 reset 命令"""
        name = user_name or "用戶"
        
        reset_text = f"""🔄 **正在開始新對話，{name}！**

您現在可以詢問我任何有關您關心的資料問題。
"""
        
        return CommandResponse(
            handled=True,
            message=reset_text,
            command_type="reset"
        )
    
    async def _handle_setuser_command(self, command: str, user_id: str) -> CommandResponse:
        """處理 setuser 命令（僅限模擬器）"""
        parts = command.split(" ", 2)
        
        if len(parts) < 2:
            return CommandResponse(
                handled=True,
                message="""❌ **無效格式**

使用: `/setuser your.email@company.com Your Name`
範例: `/setuser john.doe@company.com John Doe`""",
                command_type="setuser",
                error="Invalid format"
            )
        
        email = parts[1]
        name = parts[2] if len(parts) > 2 else email.split('@')[0]
        
        success_text = f"""✅ **Identity Updated!**

**Name:** {name}
**Email:** {email}

You can now ask me questions about your data!"""
        
        return CommandResponse(
            handled=True,
            message=success_text,
            command_type="setuser",
            card_data={
                "user_id": user_id,
                "email": email,
                "name": name
            }
        )
    
    async def _is_reset_command(self, command: str) -> bool:
        """檢查是否為重置命令"""
        reset_triggers = [
            "new conversation",
            "new chat",
            "start over",
            "reset",
            "clear conversation",
            "/new",
            "/reset",
            "/clear",
            "/start",
            "begin again",
            "fresh start"
        ]
        return command.lower() in reset_triggers
