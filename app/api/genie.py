from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
import json

from app.services.genie import GenieService
from app.core.config import DefaultConfig
from app.models.user_session import UserSession
from app.core.auth_middleware import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()
config = DefaultConfig()


def get_genie_service() -> GenieService:
    """取得 GenieService 單例（來自 bot_instance）"""
    from app.bot_instance import GENIE_SERVICE
    return GENIE_SERVICE


class ChatRequest(BaseModel):
    query: str
    user_email: Optional[str] = None  # 已棄用，從 token 取得；保留向後相容
    conversation_id: Optional[str] = None

@router.post("/chat")
async def chat(
    request: ChatRequest,
    service: GenieService = Depends(get_genie_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Send a query to Genie.
    """
    space_id = config.DATABRICKS_SPACE_ID
    if not space_id:
        raise HTTPException(status_code=400, detail="Space ID not configured")

    user_email = current_user["email"]
    user_id = current_user["user_id"]
    user_name = current_user.get("name") or user_email
    user_session = UserSession(user_id, user_email, user_name)
    user_session.conversation_id = request.conversation_id

    try:
        response_payload, conversation_id, message_id = await service.ask(
            question=request.query,
            space_id=space_id,
            user_session=user_session,
            conversation_id=request.conversation_id
        )

        # 日誌記錄回應信息
        try:
            response_data = json.loads(response_payload)
            logger.info(f"✅ Genie API 回應成功 - 問題: {request.query[:60]}...")
            if "error" in response_data:
                logger.warning(f"⚠️ Genie 返回錯誤: {response_data['error'][:100]}")
            elif "message" in response_data:
                logger.info(f"💬 返回文字回覆 (長度: {len(response_data.get('message', ''))})")
            elif "data" in response_data:
                data_count = len(response_data.get("data", {}).get("data_array", []))
                logger.info(f"📊 返回資料結果 (筆數: {data_count})")
        except Exception:
            logger.debug("無法解析回應內容")

        return {
            "conversation_id": conversation_id,
            "message_id": message_id,
            "response": response_payload
        }
    except Exception as e:
        logger.error(f"❌ Genie API 調用失敗 - 問題: {request.query[:60]}... - 錯誤: {str(e)[:200]}")
        raise HTTPException(status_code=500, detail="Genie 查詢處理失敗，請稍後再試")
