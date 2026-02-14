"""
IdentitySkill - 用戶身份管理技能

遷移自 bot/handlers/identity.py
負責處理用戶身份驗證、電子郵件輸入、身份確認
"""

from typing import Dict, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class IdentityResponse:
    """身份驗證回應"""
    handled: bool = False
    message: Optional[str] = None
    user_email: Optional[str] = None
    user_name: Optional[str] = None
    requires_email_input: bool = False
    email_validated: bool = False
    cancelled: bool = False
    error: Optional[str] = None


class IdentitySkill:
    """
    用戶身份管理技能
    
    處理:
    - 用戶身份識別流程
    - 電子郵件輸入與驗證
    - 身份確認與會話創建
    - 未識別用戶處理
    """
    
    def __init__(self):
        """初始化身份管理技能"""
        self.name = "身份管理技能"
        self.pending_email_inputs: Dict[str, bool] = {}
        self.validated_emails: Dict[str, str] = {}  # user_id -> email
        logger.info(f"初始化 {self.name}")
    
    async def handle_user_identification(
        self,
        user_id: str,
        message: str,
        admin_contact: Optional[str] = "admin@example.com"
    ) -> IdentityResponse:
        """
        處理用戶身份識別流程
        
        Args:
            user_id: 用戶 ID
            message: 用戶消息
            admin_contact: 管理員聯繫方式
            
        Returns:
            IdentityResponse: 身份處理結果
        """
        try:
            message_lower = message.lower().strip()
            
            # 檢查是否正在等待電子郵件輸入
            if user_id in self.pending_email_inputs:
                return await self._handle_pending_email_input(user_id, message)
            
            # 處理幫助命令
            if message_lower in ["help", "/help", "commands", "/commands"]:
                return await self._show_help(admin_contact)
            
            # 處理 info 命令
            if message_lower in ["info", "/info"]:
                return await self._show_info_for_unidentified()
            
            # 處理電子郵件輸入請求
            if message_lower in ["email", "provide email", "enter email"]:
                return await self._request_email_input(user_id)
            
            # 未識別用戶的默認回應
            return await self._show_welcome_for_unidentified()
            
        except Exception as e:
            logger.error(f"處理用戶身份識別失敗: {str(e)}")
            return IdentityResponse(
                handled=True,
                error=str(e),
                message="❌ 處理身份驗證時發生錯誤。"
            )
    
    async def validate_email(self, email: str) -> bool:
        """
        驗證電子郵件格式
        
        Args:
            email: 電子郵件地址
            
        Returns:
            bool: 是否有效
        """
        # 基本的電子郵件正則表達式
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email))
    
    async def is_user_pending_email(self, user_id: str) -> bool:
        """
        檢查用戶是否正在等待電子郵件輸入
        
        Args:
            user_id: 用戶 ID
            
        Returns:
            bool: 是否等待電子郵件輸入
        """
        return user_id in self.pending_email_inputs
    
    async def cancel_email_input(self, user_id: str) -> bool:
        """
        取消電子郵件輸入流程
        
        Args:
            user_id: 用戶 ID
            
        Returns:
            bool: 是否成功取消
        """
        if user_id in self.pending_email_inputs:
            del self.pending_email_inputs[user_id]
            logger.info(f"取消用戶 {user_id} 的電子郵件輸入流程")
            return True
        return False
    
    async def confirm_email(self, user_id: str, email: str) -> IdentityResponse:
        """
        確認用戶電子郵件
        
        Args:
            user_id: 用戶 ID
            email: 電子郵件地址
            
        Returns:
            IdentityResponse: 確認結果
        """
        if not await self.validate_email(email):
            return IdentityResponse(
                handled=True,
                email_validated=False,
                message="❌ 無效的電子郵件格式"
            )
        
        self.validated_emails[user_id] = email
        
        # 清除待處理狀態
        if user_id in self.pending_email_inputs:
            del self.pending_email_inputs[user_id]
        
        logger.info(f"確認用戶 {user_id} 的電子郵件: {email}")
        
        return IdentityResponse(
            handled=True,
            email_validated=True,
            user_email=email
        )
    
    async def get_validated_email(self, user_id: str) -> Optional[str]:
        """
        獲取已驗證的電子郵件
        
        Args:
            user_id: 用戶 ID
            
        Returns:
            Optional[str]: 電子郵件地址
        """
        return self.validated_emails.get(user_id)
    
    async def clear_user_identity(self, user_id: str):
        """
        清除用戶身份信息
        
        Args:
            user_id: 用戶 ID
        """
        self.validated_emails.pop(user_id, None)
        self.pending_email_inputs.pop(user_id, None)
        logger.info(f"清除用戶 {user_id} 的身份信息")
    
    def get_capability_description(self) -> Dict[str, Any]:
        """
        獲取技能描述
        
        Returns:
            Dict: 技能描述信息
        """
        return {
            "name": self.name,
            "description": "處理用戶身份識別、電子郵件驗證和身份確認",
            "methods": {
                "handle_user_identification": "處理用戶身份識別流程",
                "validate_email": "驗證電子郵件格式",
                "is_user_pending_email": "檢查用戶是否等待電子郵件輸入",
                "cancel_email_input": "取消電子郵件輸入流程",
                "confirm_email": "確認用戶電子郵件",
                "get_validated_email": "獲取已驗證的電子郵件",
                "clear_user_identity": "清除用戶身份信息"
            },
            "features": [
                "電子郵件格式驗證",
                "身份識別流程管理",
                "待處理狀態追蹤",
                "用戶幫助信息"
            ]
        }
    
    # === Private Methods ===
    
    async def _handle_pending_email_input(
        self,
        user_id: str,
        message: str
    ) -> IdentityResponse:
        """處理待處理的電子郵件輸入"""
        message_lower = message.lower().strip()
        
        # 處理取消
        if message_lower == "cancel":
            await self.cancel_email_input(user_id)
            return IdentityResponse(
                handled=True,
                cancelled=True,
                message="""❌ **電子郵件輸入已取消**

您可以稍後輸入任何訊息再試一次。如果需要，我會再次詢問您的電子郵件。"""
            )
        
        # 驗證電子郵件
        if await self.validate_email(message):
            # 提取名稱（從電子郵件地址）
            name = message.split('@')[0].replace('.', ' ').title()
            
            result = await self.confirm_email(user_id, message)
            
            sample_questions = [
                "顯示銷售數據前10筆",
                "分析本月的用戶增長趨勢",
                "生成產品銷售報表"
            ]
            questions_text = "\n".join([f"- {q}" for q in sample_questions])
            
            result.message = f"""✅ **電子郵件已確認！**

歡迎，{name}！我已成功將您登入為 {message}。

現在您可以詢問有關您資料的問題。試著問類似這樣的問題：
{questions_text}"""
            
            result.user_name = name
            return result
        
        # 無效的電子郵件格式
        return IdentityResponse(
            handled=True,
            email_validated=False,
            message="""❌ **無效的電子郵件格式**

請提供有效的電子郵件地址（例如：somebody@fareastone.com.tw）。

輸入 `cancel` 停止電子郵件輸入過程。"""
        )
    
    async def _request_email_input(self, user_id: str) -> IdentityResponse:
        """請求用戶輸入電子郵件"""
        self.pending_email_inputs[user_id] = True
        
        return IdentityResponse(
            handled=True,
            requires_email_input=True,
            message="""📧 **Genie 使用者登入**

請提供您的電子郵件地址（例如：somebody@fareastone.com.tw）。

如果您想停止此過程，請輸入 `cancel`。"""
        )
    
    async def _show_help(self, admin_contact: str) -> IdentityResponse:
        """顯示幫助信息（未識別用戶）"""
        help_text = f"""🤖 **Databricks Genie 機器人資訊**

**我能做什麼：**

我是一個 Teams 機器人，連接到 Databricks Genie Space，讓您可以直接在 Teams 中透過自然語言查詢與您的資料互動。

**我如何運作：**

    • 我使用設定的憑證連接到您的 Databricks 工作區

    • 您的對話上下文會在工作階段之間保留，以保持連續性

    • 我會記住我們的對話歷史，以提供更好的後續回應

**工作階段管理：**

    • 對話在閒置 **4 小時** 後會自動重置

    • 您可以隨時輸入 `reset` 或 `new chat` 手動重置

    • 您的電子郵件 **僅用於在 Genie 中記錄查詢** - 不用於 AI 處理

**可用指令：**

    • `help` - 顯示此資訊

    • `info` - 獲取入門協助

    • `whoami` - 顯示您的使用者資訊

    • `reset` - 開始新的對話

    • `new chat` - 開始新的對話

    • `logout` - 清除您的工作階段

**需要協助？**

請聯絡機器人管理員：{admin_contact}"""
        
        return IdentityResponse(
            handled=True,
            message=help_text
        )
    
    async def _show_info_for_unidentified(self) -> IdentityResponse:
        """顯示未識別用戶的 info 信息"""
        info_text = """🤖 **歡迎使用 Genie 機器人 - 需要使用者登入**

我需要您的電子郵件地址來記錄 Genie 中的查詢以進行追蹤。

**快速開始：**
- 輸入 `email` 提供您的電子郵件地址
- 我將驗證格式並建立您的工作階段

**接下來會發生什麼：**
- 登入後，您可以詢問有關您資料的問題
- 我會記住我們的對話上下文
- 您可以詢問後續問題

**了解更多：**
- 輸入 `help` 了解更多關於 Genie 機器人的資訊
- 輸入 `info` 獲取入門協助

準備好開始了嗎？輸入 `email` 提供您的電子郵件地址！"""
        
        return IdentityResponse(
            handled=True,
            message=info_text
        )
    
    async def _show_welcome_for_unidentified(self) -> IdentityResponse:
        """顯示未識別用戶的歡迎消息"""
        welcome_text = """🤖 **歡迎使用 Genie 機器人**

我需要您的電子郵件地址來記錄 Genie 中的查詢以進行追蹤。

**快速選項：**
- 輸入 `email` 提供您的電子郵件地址
- 輸入 `help` 了解更多關於 Genie 機器人的資訊
- 輸入 `info` 獲取入門協助

登入後，您就可以詢問有關您資料的問題！"""
        
        return IdentityResponse(
            handled=True,
            message=welcome_text,
            requires_email_input=True
        )
