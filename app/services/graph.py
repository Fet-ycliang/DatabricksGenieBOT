from typing import Optional, Dict, Any
import httpx
from botbuilder.core import TurnContext
from botbuilder.schema import Activity, ActivityTypes

from bot.cards.constants import ADAPTIVE_CARD_VERSION


class GraphService:
    def __init__(self, config):
        self.config = config
        self.base_url = "https://graph.microsoft.com/v1.0"
        self._http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout=30.0, connect=5.0, read=10.0, write=10.0),
            headers={"Accept": "application/json"},
        )

    async def close(self):
        """關閉共享 HTTP client（應用程式關閉時調用）"""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    async def get_user_token(self, turn_context: TurnContext) -> Any:
        # This assumes the bot is authenticated and can get token via adapter
        # In Bot Framework, we use UserTokenClient
        user_token_client = turn_context.turn_state.get("UserTokenClient")
        if user_token_client:
            return await user_token_client.get_user_token(
                turn_context.activity.from_property.id,
                self.config.CONNECTION_NAME,
                turn_context.activity.channel_id,
                None
            )
        # Helper via adapter
        if hasattr(turn_context.adapter, "get_user_token"):
             return await turn_context.adapter.get_user_token(
                turn_context,
                self.config.CONNECTION_NAME,
                None
             )
        return None

    async def get_user_email_and_id(self, turn_context: TurnContext) -> Dict[str, str]:
        """從 activity 中提取基本使用者資訊。完整資料透過 Graph API 取得。"""
        activity = turn_context.activity
        user_id = activity.from_property.id

        return {
            "id": user_id,
            "name": activity.from_property.name,
            "email": None  # Will be filled by graph
        }

    async def get_user_profile(self, access_token: str) -> Dict[str, Any]:
        url = f"{self.base_url}/me"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        resp = await self._http_client.get(url, headers=headers)
        if resp.status_code == 200:
            return resp.json()
        return {}

    @staticmethod
    def create_user_profile_card(user_details: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "AdaptiveCard",
            "version": ADAPTIVE_CARD_VERSION,
            "body": [
                {
                    "type": "TextBlock",
                    "text": f"User Profile: {user_details.get('displayName')}",
                    "size": "Medium",
                    "weight": "Bolder"
                },
                {
                    "type": "FactSet",
                    "facts": [
                        {"title": "Email", "value": user_details.get("mail") or user_details.get("userPrincipalName")},
                        {"title": "Job Title", "value": user_details.get("jobTitle")},
                        {"title": "Office", "value": user_details.get("officeLocation")}
                    ]
                }
            ]
        }
