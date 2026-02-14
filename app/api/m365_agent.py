"""
Microsoft 365 Agent Framework API 端點

提供 HTTP 接口來與 Agent Framework 互動
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
from app.core.m365_agent_framework import M365AgentFramework
from app.core.config import DefaultConfig
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
CONFIG = DefaultConfig()

# 初始化 Agent Framework
try:
    m365_framework = M365AgentFramework(CONFIG)
except Exception as e:
    logger.error(f"初始化 Agent Framework 失敗: {str(e)}")
    m365_framework = None


@router.get("/m365/profile")
async def get_user_profile(user_id: str = "me"):
    """
    取得使用者個人資料
    
    Args:
        user_id: 使用者 ID（預設為當前使用者）
        
    Returns:
        使用者個人資料
    """
    if not m365_framework:
        raise HTTPException(
            status_code=500,
            detail="Agent Framework 未初始化"
        )
    
    try:
        profile = await m365_framework.m365_service.get_user_profile(user_id)
        return {
            "status": "success",
            "profile": profile
        }
    except Exception as e:
        logger.error(f"取得個人資料失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/m365/context")
async def get_user_context(user_id: str = "me"):
    """
    取得使用者完整上下文信息 (僅包含基本資料，Skills 已移除)
    """
    if not m365_framework:
        raise HTTPException(
            status_code=500,
            detail="Agent Framework 未初始化"
        )
    
    try:
        # 僅返回 User Profile，因為其他 Skills 已移除
        profile = await m365_framework.m365_service.get_user_profile(user_id)
        return {
            "status": "success",
            "context": {
                "user_id": user_id,
                "profile": profile
            }
        }
    except Exception as e:
        logger.error(f"取得上下文失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



