from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.services.genie import GenieService
from app.core.config import DefaultConfig
from app.models.user_session import UserSession

router = APIRouter()
config = DefaultConfig()

# Dependency to get GenieService
def get_genie_service():
    service = GenieService(config)
    try:
        yield service
    finally:
        # In a real app we might want to keep the session open or close it
        # depending on how GenieService manages aiohttp session
        pass 
        # await service.close() # Logic is in on_shutdown

class ChatRequest(BaseModel):
    query: str
    user_email: str
    conversation_id: Optional[str] = None
    space_id: Optional[str] = None

@router.post("/chat")
async def chat(request: ChatRequest, service: GenieService = Depends(get_genie_service)):
    """
    Send a query to Genie.
    """
    space_id = request.space_id or config.DATABRICKS_SPACE_ID
    if not space_id:
        raise HTTPException(status_code=400, detail="Space ID not configured")

    # Create a temporary user session for this request
    # In production, this should come from Auth middleware (e.g. JWT)
    user_session = UserSession(request.user_email, request.user_email)
    user_session.conversation_id = request.conversation_id

    try:
        response_payload, conversation_id, message_id = await service.ask(
            question=request.query,
            space_id=space_id,
            user_session=user_session,
            conversation_id=request.conversation_id
        )
        return {
            "conversation_id": conversation_id,
            "message_id": message_id,
            "response": response_payload 
            # Note: response_payload is a JSON string, we might want to parse it
            # but for now returning as is or parsed
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
