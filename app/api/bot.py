from fastapi import APIRouter, Request, Response, HTTPException
from botbuilder.core import TurnContext
from botbuilder.schema import Activity

from app.core.adapter import ADAPTER
from app.bot_instance import BOT
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/messages")
async def messages(req: Request):
    """
    Handle Bot Framework messages.
    """
    if "application/json" in req.headers.get("content-type", ""):
        body = await req.json()
    else:
        logger.warning("Unsupported content-type: %s", req.headers.get("content-type"))
        return Response(status_code=415)

    try:
        activity = Activity().deserialize(body)
    except Exception as exc:
        logger.exception("Failed to deserialize activity: %s", exc)
        raise HTTPException(status_code=400, detail="Invalid activity payload")
    auth_header = req.headers.get("Authorization", "")

    try:
        response = await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
        if response:
            return vars(response)
        return Response(status_code=201)
    except Exception as e:
        logger.exception("Bot processing failed: %s", e)
        raise HTTPException(status_code=500, detail="Bot processing error")
