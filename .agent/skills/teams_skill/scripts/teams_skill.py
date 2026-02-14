"""
Microsoft 365 Agent Teams Skill

提供 Teams 相關的操作能力
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class TeamsChannel(BaseModel):
    """Teams 頻道模型"""
    channel_id: str
    display_name: str
    description: Optional[str] = None


class TeamsMessage(BaseModel):
    """Teams 訊息模型"""
    message_id: str
    from_display_name: str
    body_content: str
    created_datetime: str


class TeamsSkill:
    """Teams Skill - 處理 Teams 操作"""
    
    def __init__(self, graph_service):
        """
        初始化 Teams Skill
        
        Args:
            graph_service: Microsoft Graph 服務實例
        """
        self.graph_service = graph_service
    
    async def list_teams(self, user_id: str = "me") -> List[Dict[str, Any]]:
        """
        列出使用者所屬的 Teams
        
        Args:
            user_id: 使用者 ID
            
        Returns:
            Teams 清單
        """
        try:
            result = await self.graph_service.graph_client.get(
                f"/users/{user_id}/joinedTeams"
            )
            
            return result.get("value", [])
        except Exception as e:
            logger.error(f"列出 Teams 失敗: {str(e)}")
            return []
    
    async def list_channels(self, team_id: str) -> List[TeamsChannel]:
        """
        列出團隊的頻道
        
        Args:
            team_id: 團隊 ID
            
        Returns:
            頻道清單
        """
        try:
            result = await self.graph_service.graph_client.get(
                f"/teams/{team_id}/channels"
            )
            
            channels = []
            for item in result.get("value", []):
                channel = TeamsChannel(
                    channel_id=item.get("id", ""),
                    display_name=item.get("displayName", ""),
                    description=item.get("description")
                )
                channels.append(channel)
            
            return channels
        except Exception as e:
            logger.error(f"列出頻道失敗: {str(e)}")
            return []
    
    async def get_channel_messages(
        self,
        team_id: str,
        channel_id: str,
        count: int = 10
    ) -> List[TeamsMessage]:
        """
        取得頻道訊息
        
        Args:
            team_id: 團隊 ID
            channel_id: 頻道 ID
            count: 返回的訊息數量
            
        Returns:
            訊息清單
        """
        try:
            result = await self.graph_service.graph_client.get(
                f"/teams/{team_id}/channels/{channel_id}/messages",
                params={"$top": count}
            )
            
            messages = []
            for item in result.get("value", []):
                message = TeamsMessage(
                    message_id=item.get("id", ""),
                    from_display_name=item.get("from", {}).get("user", {}).get("displayName", ""),
                    body_content=item.get("body", {}).get("content", ""),
                    created_datetime=item.get("createdDateTime", "")
                )
                messages.append(message)
            
            return messages
        except Exception as e:
            logger.error(f"取得頻道訊息失敗: {str(e)}")
            return []
    
    async def send_message_to_channel(
        self,
        team_id: str,
        channel_id: str,
        message_content: str
    ) -> bool:
        """
        發送訊息到頻道
        
        Args:
            team_id: 團隊 ID
            channel_id: 頻道 ID
            message_content: 訊息內容
            
        Returns:
            是否成功發送
        """
        try:
            body = {
                "body": {
                    "contentType": "html",
                    "content": message_content
                }
            }
            
            await self.graph_service.graph_client.post(
                f"/teams/{team_id}/channels/{channel_id}/messages",
                json=body
            )
            
            logger.info(f"訊息已發送到頻道 {channel_id}")
            return True
        except Exception as e:
            logger.error(f"發送訊息失敗: {str(e)}")
            return False
    
    async def search_teams_messages(
        self,
        search_query: str,
        count: int = 10
    ) -> List[TeamsMessage]:
        """
        搜尋 Teams 訊息
        
        Args:
            search_query: 搜尋查詢
            count: 返回的結果數量
            
        Returns:
            搜尋結果
        """
        try:
            result = await self.graph_service.search_teams_messages(
                "",  # team_id
                search_query,
                count
            )
            
            messages = []
            # 處理搜尋結果
            for item in result.get("value", []):
                if "chatMessage" in item.get("hitsContainers", [{}])[0]:
                    for hit in item["hitsContainers"][0]["hits"]:
                        message = TeamsMessage(
                            message_id=hit.get("hitId", ""),
                            from_display_name=hit.get("properties", {}).get("from", ""),
                            body_content=hit.get("properties", {}).get("body", ""),
                            created_datetime=hit.get("properties", {}).get("createdDateTime", "")
                        )
                        messages.append(message)
            
            return messages
        except Exception as e:
            logger.error(f"搜尋 Teams 訊息失敗: {str(e)}")
            return []
    
    async def create_chat(
        self,
        chat_type: str,
        members: List[str],
        topic: Optional[str] = None
    ) -> Optional[str]:
        """
        建立新的聊天
        
        Args:
            chat_type: 聊天類型 ("oneOnOne", "group")
            members: 成員電子郵件清單
            topic: 聊天主題
            
        Returns:
            新建聊天的 ID，失敗返回 None
        """
        try:
            body = {
                "chatType": chat_type,
                "members": [
                    {
                        "@odata.type": "#microsoft.graph.aadUserConversationMember",
                        "roles": ["owner"],
                        "user@odata.bind": f"https://graph.microsoft.com/v1.0/users/{member}"
                    } for member in members
                ]
            }
            
            if topic:
                body["topic"] = topic
            
            result = await self.graph_service.graph_client.post(
                "/chats",
                json=body
            )
            
            logger.info(f"已建立聊天: {chat_type}")
            return result.get("id")
        except Exception as e:
            logger.error(f"建立聊天失敗: {str(e)}")
            return None
