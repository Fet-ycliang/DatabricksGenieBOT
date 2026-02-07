from typing import Optional, Dict, Any
import aiohttp
from botbuilder.core import TurnContext
from botbuilder.schema import Activity, ActivityTypes

class GraphService:
    def __init__(self, config):
        self.config = config
        self.base_url = "https://graph.microsoft.com/v1.0"

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
        # Try to get from channel data
        activity = turn_context.activity
        user_id = activity.from_property.id
        email = None
        
        # Check standard properties
        if hasattr(activity.from_property, "aad_object_id"):
             # email might not be there directly
             pass
             
        # Just return basic info found in activity, real profile fetch is done via graph
        return {
            "id": user_id,
            "name": activity.from_property.name,
            "email": None # Will be filled by graph
        }

    async def get_user_profile(self, access_token: str) -> Dict[str, Any]:
        url = f"{self.base_url}/me"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
        return {}

    @staticmethod
    def create_user_profile_card(user_details: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "AdaptiveCard",
            "version": "1.3",
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
