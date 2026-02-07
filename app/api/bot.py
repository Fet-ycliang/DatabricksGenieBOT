from fastapi import APIRouter, Request, Response, HTTPException
from botbuilder.core import TurnContext
from botbuilder.schema import Activity

from app.core.adapter import ADAPTER
from app.bot_instance import BOT

router = APIRouter()

@router.post("/messages")
async def messages(req: Request):
    """
    Handle Bot Framework messages.
    """
    if "application/json" in req.headers.get("content-type", ""):
        body = await req.json()
    else:
        return Response(status_code=415)

    activity = Activity().deserialize(body)
    auth_header = req.headers.get("Authorization", "")

    try:
        response = await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
        if response:
            return vars(response)
        return Response(status_code=201)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
