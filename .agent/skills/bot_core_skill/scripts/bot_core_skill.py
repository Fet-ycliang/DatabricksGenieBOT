"""
BotCoreSkill - Bot 核心對話處理技能

遷移自 bot/handlers/bot.py 的 MyBot Handler
負責處理用戶互動、歡迎消息、對話流程管理
"""

from typing import Dict, Optional, List, Any
from datetime import datetime
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConversationContext:
    """對話上下文"""
    user_id: str
    conversation_id: Optional[str] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    channel_id: Optional[str] = None
    authenticated: bool = False
    last_activity: Optional[datetime] = None
    pending_message: Optional[str] = None
    
    def __post_init__(self):
        if self.last_activity is None:
            self.last_activity = datetime.now()


@dataclass
class MessageResponse:
    """消息回應"""
    text: Optional[str] = None
    card_data: Optional[Dict] = None
    suggested_actions: Optional[List[str]] = None
    activity_type: str = "message"  # message, typing, event
    requires_auth: bool = False
    error: Optional[str] = None


class BotCoreSkill:
    """
    Bot 核心技能
    
    處理:
    - 用戶加入事件
    - 消息處理路由
    - 歡迎消息生成
    - 對話上下文管理
    - 重置命令
    """
    
    def __init__(self):
        """初始化 Bot 核心技能"""
        self.name = "Bot核心技能"
        self.conversations: Dict[str, ConversationContext] = {}
        logger.info(f"初始化 {self.name}")
    
    async def handle_member_added(
        self,
        user_id: str,
        user_name: Optional[str] = None,
        conversation_id: Optional[str] = None,
        channel_id: Optional[str] = None
    ) -> MessageResponse:
        """
        處理新成員加入事件
        
        Args:
            user_id: 用戶 ID
            user_name: 用戶名稱
            conversation_id: 對話 ID
            channel_id: 頻道 ID
            
        Returns:
            MessageResponse: 歡迎消息回應
        """
        try:
            logger.info(f"新成員加入: {user_id} ({user_name})")
            
            # 創建或獲取對話上下文
            context = await self._get_or_create_context(
                user_id=user_id,
                user_name=user_name,
                conversation_id=conversation_id,
                channel_id=channel_id
            )
            
            # 檢查用戶是否已認證
            if context.authenticated:
                welcome_message = self._build_authenticated_welcome(context)
            else:
                welcome_message = self._build_unauthenticated_welcome(context)
            
            return MessageResponse(
                text=welcome_message["text"],
                card_data=welcome_message.get("card"),
                activity_type="message",
                requires_auth=not context.authenticated
            )
            
        except Exception as e:
            logger.error(f"處理成員加入失敗: {str(e)}")
            return MessageResponse(
                error=f"處理成員加入失敗: {str(e)}",
                text="歡迎！系統正在初始化，請稍候..."
            )
    
    async def handle_message(
        self,
        user_id: str,
        message_text: str,
        conversation_id: Optional[str] = None,
        user_name: Optional[str] = None
    ) -> MessageResponse:
        """
        處理用戶消息
        
        Args:
            user_id: 用戶 ID
            message_text: 消息文本
            conversation_id: 對話 ID
            user_name: 用戶名稱
            
        Returns:
            MessageResponse: 處理結果
        """
        try:
            logger.info(f"處理消息: {user_id} - {message_text}")
            
            # 獲取或創建上下文
            context = await self._get_or_create_context(
                user_id=user_id,
                user_name=user_name,
                conversation_id=conversation_id
            )
            
            # 更新最後活動時間
            context.last_activity = datetime.now()
            
            # 檢查是否為特殊命令
            if self._is_reset_command(message_text):
                return await self._handle_reset_command(user_id)
            
            if self._is_help_command(message_text):
                return await self._handle_help_command()
            
            # 檢查認證狀態
            if not context.authenticated:
                return MessageResponse(
                    text="請先登入以使用 Databricks Genie 服務。",
                    requires_auth=True,
                    card_data={"type": "login_prompt"}
                )
            
            # 正常消息處理（需要與 GenieService 集成）
            return MessageResponse(
                text="收到您的消息，正在處理...",
                activity_type="typing"
            )
            
        except Exception as e:
            logger.error(f"處理消息失敗: {str(e)}")
            return MessageResponse(
                error=f"處理消息失敗: {str(e)}",
                text="抱歉，處理您的消息時發生錯誤。"
            )
    
    async def handle_reset(self, user_id: str) -> MessageResponse:
        """
        重置用戶對話
        
        Args:
            user_id: 用戶 ID
            
        Returns:
            MessageResponse: 重置結果
        """
        return await self._handle_reset_command(user_id)
    
    async def get_conversation_context(self, user_id: str) -> Optional[ConversationContext]:
        """
        獲取對話上下文
        
        Args:
            user_id: 用戶 ID
            
        Returns:
            ConversationContext: 對話上下文
        """
        return self.conversations.get(user_id)
    
    async def update_authentication_status(
        self,
        user_id: str,
        authenticated: bool,
        user_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        更新用戶認證狀態
        
        Args:
            user_id: 用戶 ID
            authenticated: 認證狀態
            user_email: 用戶電子郵件
            
        Returns:
            Dict: 更新結果
        """
        try:
            context = self.conversations.get(user_id)
            if not context:
                return {
                    "status": "error",
                    "message": f"找不到用戶 {user_id} 的對話上下文"
                }
            
            context.authenticated = authenticated
            if user_email:
                context.user_email = user_email
            
            logger.info(f"更新用戶 {user_id} 認證狀態: {authenticated}")
            
            return {
                "status": "success",
                "user_id": user_id,
                "authenticated": authenticated,
                "message": f"認證狀態已更新"
            }
            
        except Exception as e:
            logger.error(f"更新認證狀態失敗: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def get_active_conversations(self) -> List[str]:
        """
        獲取活動對話列表
        
        Returns:
            List[str]: 用戶 ID 列表
        """
        # 過濾出最近 1 小時內有活動的對話
        active_conversations = []
        now = datetime.now()
        
        for user_id, context in self.conversations.items():
            if context.last_activity:
                delta = now - context.last_activity
                if delta.total_seconds() < 3600:  # 1 小時
                    active_conversations.append(user_id)
        
        return active_conversations
    
    def get_capability_description(self) -> Dict[str, Any]:
        """
        獲取技能描述
        
        Returns:
            Dict: 技能描述信息
        """
        return {
            "name": self.name,
            "description": "Bot 核心對話處理技能，處理用戶互動、歡迎消息、對話流程管理",
            "methods": {
                "handle_member_added": "處理新成員加入事件，發送歡迎消息",
                "handle_message": "處理用戶消息，路由到適當的處理器",
                "handle_reset": "重置用戶對話上下文",
                "get_conversation_context": "獲取用戶對話上下文",
                "update_authentication_status": "更新用戶認證狀態",
                "get_active_conversations": "獲取活動對話列表",
                "build_typing_indicator": "構建正在輸入指示器",
                "build_error_message": "構建錯誤消息"
            },
            "events_handled": [
                "member_added",
                "message_received",
                "reset_command",
                "help_command"
            ]
        }
    
    # === Private Methods ===
    
    async def _get_or_create_context(
        self,
        user_id: str,
        user_name: Optional[str] = None,
        conversation_id: Optional[str] = None,
        channel_id: Optional[str] = None
    ) -> ConversationContext:
        """獲取或創建對話上下文"""
        if user_id not in self.conversations:
            self.conversations[user_id] = ConversationContext(
                user_id=user_id,
                user_name=user_name,
                conversation_id=conversation_id,
                channel_id=channel_id
            )
            logger.info(f"創建新對話上下文: {user_id}")
        else:
            # 更新信息
            context = self.conversations[user_id]
            if user_name:
                context.user_name = user_name
            if conversation_id:
                context.conversation_id = conversation_id
            if channel_id:
                context.channel_id = channel_id
        
        return self.conversations[user_id]
    
    def _build_authenticated_welcome(self, context: ConversationContext) -> Dict:
        """構建已認證用戶的歡迎消息"""
        user_name = context.user_name or "用戶"
        
        return {
            "text": f"歡迎回來，{user_name}！👋\n\n"
                   f"您可以開始詢問 Databricks Genie 任何問題。\n"
                   f"輸入 /help 查看可用命令。",
            "card": {
                "type": "authenticated_welcome",
                "user_name": user_name,
                "suggested_questions": [
                    "顯示最近的資料",
                    "分析銷售趨勢",
                    "生成報表"
                ]
            }
        }
    
    def _build_unauthenticated_welcome(self, context: ConversationContext) -> Dict:
        """構建未認證用戶的歡迎消息"""
        return {
            "text": "👋 歡迎使用 Databricks Genie Bot！\n\n"
                   "請先登入以使用所有功能。\n"
                   "點擊下方按鈕進行單一登入 (SSO)。",
            "card": {
                "type": "login_prompt",
                "auth_required": True
            }
        }
    
    def _is_reset_command(self, text: str) -> bool:
        """檢查是否為重置命令"""
        reset_keywords = ["/reset", "reset", "new chat", "重置", "新對話"]
        return text.lower().strip() in reset_keywords
    
    def _is_help_command(self, text: str) -> bool:
        """檢查是否為幫助命令"""
        help_keywords = ["/help", "help", "幫助", "說明"]
        return text.lower().strip() in help_keywords
    
    async def _handle_reset_command(self, user_id: str) -> MessageResponse:
        """處理重置命令"""
        try:
            if user_id in self.conversations:
                old_context = self.conversations[user_id]
                # 創建新上下文，保留基本信息
                self.conversations[user_id] = ConversationContext(
                    user_id=user_id,
                    user_name=old_context.user_name,
                    user_email=old_context.user_email,
                    authenticated=old_context.authenticated
                )
                logger.info(f"重置用戶對話: {user_id}")
            
            return MessageResponse(
                text="✅ 對話已重置！您可以開始新的對話了。",
                activity_type="message"
            )
            
        except Exception as e:
            logger.error(f"重置對話失敗: {str(e)}")
            return MessageResponse(
                error=str(e),
                text="重置對話時發生錯誤。"
            )
    
    async def _handle_help_command(self) -> MessageResponse:
        """處理幫助命令"""
        help_text = """
📖 **Databricks Genie Bot 使用說明**

**可用命令:**
- `/help` - 顯示此幫助信息
- `/reset` 或 `new chat` - 重置對話，開始新的對話
- 直接輸入問題 - 向 Databricks Genie 提問

**功能:**
✓ 與 Databricks Genie 自然語言對話
✓ 數據查詢與分析
✓ 自動生成圖表
✓ 建議後續問題

**範例問題:**
• "顯示銷售數據前10筆"
• "分析本月的用戶增長趨勢"
• "生成產品銷售報表"

如有問題，請聯繫系統管理員。
"""
        
        return MessageResponse(
            text=help_text,
            activity_type="message"
        )
    
    async def build_typing_indicator(self) -> MessageResponse:
        """構建正在輸入指示器"""
        return MessageResponse(
            activity_type="typing"
        )
    
    async def build_error_message(self, error: str, user_friendly: bool = True) -> MessageResponse:
        """
        構建錯誤消息
        
        Args:
            error: 錯誤信息
            user_friendly: 是否使用用戶友好的消息
            
        Returns:
            MessageResponse: 錯誤消息
        """
        if user_friendly:
            text = "❌ 抱歉，處理您的請求時發生錯誤。請稍後再試。"
        else:
            text = f"❌ 錯誤: {error}"
        
        return MessageResponse(
            text=text,
            error=error,
            activity_type="message"
        )
