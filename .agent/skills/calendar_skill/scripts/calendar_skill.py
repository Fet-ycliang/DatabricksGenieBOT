"""
Microsoft 365 Agent 日曆 Skill

提供日曆相關的操作能力
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class CalendarEvent(BaseModel):
    """日曆事件模型"""
    subject: str
    start_time: str
    end_time: str
    organizer_email: Optional[str] = None
    is_online_meeting: bool = False
    online_meeting_url: Optional[str] = None


class CalendarSkill:
    """日曆 Skill - 處理日曆事件"""
    
    def __init__(self, graph_service):
        """
        初始化日曆 Skill
        
        Args:
            graph_service: Microsoft Graph 服務實例
        """
        self.graph_service = graph_service
    
    async def get_upcoming_events(
        self,
        user_id: str = "me",
        count: int = 10
    ) -> List[CalendarEvent]:
        """
        取得即將舉行的活動
        
        Args:
            user_id: 使用者 ID
            count: 要取得的事件數量
            
        Returns:
            日曆事件清單
        """
        try:
            result = await self.graph_service.get_user_calendar_events(
                user_id, 
                count
            )
            
            if "error" in result:
                logger.error(f"取得事件失敗: {result['error']}")
                return []
            
            events = []
            for item in result.get("value", []):
                event = CalendarEvent(
                    subject=item.get("subject", ""),
                    start_time=item.get("start", {}).get("dateTime", ""),
                    end_time=item.get("end", {}).get("dateTime", ""),
                    organizer_email=item.get("organizer", {}).get("emailAddress", {}).get("address"),
                    is_online_meeting=item.get("isOnlineMeeting", False),
                    online_meeting_url=item.get("onlineMeetingUrl")
                )
                events.append(event)
            
            return events
        except Exception as e:
            logger.error(f"處理日曆事件失敗: {str(e)}")
            return []
    
    async def create_event(
        self,
        subject: str,
        start_time: str,
        end_time: str,
        attendees: Optional[List[str]] = None,
        is_online_meeting: bool = False,
        user_id: str = "me"
    ) -> bool:
        """
        建立日曆事件
        
        Args:
            subject: 事件主旨
            start_time: 開始時間
            end_time: 結束時間
            attendees: 參與者電子郵件清單
            is_online_meeting: 是否為線上會議
            user_id: 使用者 ID
            
        Returns:
            是否成功建立
        """
        try:
            event = {
                "subject": subject,
                "start": {
                    "dateTime": start_time,
                    "timeZone": "UTC"
                },
                "end": {
                    "dateTime": end_time,
                    "timeZone": "UTC"
                },
                "isOnlineMeeting": is_online_meeting
            }
            
            if attendees:
                event["attendees"] = [
                    {
                        "emailAddress": {
                            "address": addr
                        },
                        "type": "required"
                    } for addr in attendees
                ]
            
            await self.graph_service.graph_client.post(
                f"/users/{user_id}/events",
                json=event
            )
            
            logger.info(f"已建立事件: {subject}")
            return True
        except Exception as e:
            logger.error(f"建立事件失敗: {str(e)}")
            return False
    
    async def find_free_time(
        self,
        user_ids: List[str],
        start_time: str,
        end_time: str
    ) -> dict:
        """
        找到共同的空閒時間
        
        Args:
            user_ids: 使用者 ID 清單
            start_time: 搜尋開始時間
            end_time: 搜尋結束時間
            
        Returns:
            空閒時間清單
        """
        try:
            attendees = [
                {
                    "type": "required",
                    "emailAddress": {
                        "address": user_id
                    }
                } for user_id in user_ids
            ]
            
            body = {
                "attendees": attendees,
                "timeSlotDuration": "PT30M",
                "startTime": {
                    "dateTime": start_time,
                    "timeZone": "UTC"
                },
                "endTime": {
                    "dateTime": end_time,
                    "timeZone": "UTC"
                }
            }
            
            result = await self.graph_service.graph_client.post(
                "/me/calendar/getSchedule",
                json=body
            )
            
            return result
        except Exception as e:
            logger.error(f"查找空閒時間失敗: {str(e)}")
            return {"error": str(e)}
