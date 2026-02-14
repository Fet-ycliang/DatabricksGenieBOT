"""
Microsoft 365 Agent 郵件 Skill

提供電子郵件相關的操作能力
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class EmailMessage(BaseModel):
    """電子郵件訊息模型"""
    subject: str
    from_email: str
    received_datetime: str
    body_preview: Optional[str] = None
    importance: str = "normal"


class MailSkill:
    """郵件 Skill - 處理電子郵件操作"""
    
    def __init__(self, graph_service):
        """
        初始化郵件 Skill
        
        Args:
            graph_service: Microsoft Graph 服務實例
        """
        self.graph_service = graph_service
    
    async def get_recent_emails(
        self, 
        user_id: str = "me",
        count: int = 10
    ) -> List[EmailMessage]:
        """
        取得最近的電子郵件
        
        Args:
            user_id: 使用者 ID
            count: 要取得的郵件數量
            
        Returns:
            電子郵件訊息清單
        """
        try:
            result = await self.graph_service.list_user_emails(user_id, count)
            
            if "error" in result:
                logger.error(f"取得郵件失敗: {result['error']}")
                return []
            
            emails = []
            for item in result.get("value", []):
                email = EmailMessage(
                    subject=item.get("subject", ""),
                    from_email=item.get("from", {}).get("emailAddress", {}).get("address", ""),
                    received_datetime=item.get("receivedDateTime", ""),
                    body_preview=item.get("bodyPreview", ""),
                    importance=item.get("importance", "normal")
                )
                emails.append(email)
            
            return emails
        except Exception as e:
            logger.error(f"處理郵件失敗: {str(e)}")
            return []
    
    async def search_emails(
        self,
        user_id: str = "me",
        search_query: str = "",
        count: int = 10
    ) -> List[EmailMessage]:
        """
        搜尋電子郵件
        
        Args:
            user_id: 使用者 ID
            search_query: 搜尋查詢
            count: 返回的郵件數量
            
        Returns:
            符合條件的電子郵件清單
        """
        try:
            # 實作搜尋邏輯
            result = await self.graph_service.graph_client.get(
                f"/users/{user_id}/mailFolders/inbox/messages",
                params={
                    "$search": f'"{search_query}"',
                    "$top": count
                }
            )
            
            emails = []
            for item in result.get("value", []):
                email = EmailMessage(
                    subject=item.get("subject", ""),
                    from_email=item.get("from", {}).get("emailAddress", {}).get("address", ""),
                    received_datetime=item.get("receivedDateTime", ""),
                    body_preview=item.get("bodyPreview", "")
                )
                emails.append(email)
            
            return emails
        except Exception as e:
            logger.error(f"搜尋郵件失敗: {str(e)}")
            return []
    
    async def send_email(
        self,
        to_addresses: List[str],
        subject: str,
        body: str,
        user_id: str = "me"
    ) -> bool:
        """
        發送電子郵件
        
        Args:
            to_addresses: 收件人地址清單
            subject: 郵件主旨
            body: 郵件正文
            user_id: 寄件人 ID
            
        Returns:
            是否成功發送
        """
        try:
            message = {
                "subject": subject,
                "body": {
                    "contentType": "HTML",
                    "content": body
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": addr
                        }
                    } for addr in to_addresses
                ]
            }
            
            await self.graph_service.graph_client.post(
                f"/users/{user_id}/sendMail",
                json={"message": message}
            )
            
            logger.info(f"郵件已發送給 {', '.join(to_addresses)}")
            return True
        except Exception as e:
            logger.error(f"發送郵件失敗: {str(e)}")
            return False
