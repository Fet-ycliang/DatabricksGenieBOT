"""
Microsoft 365 Agent 配置和管理

協調所有 skills 和服務的初始化
"""

from typing import Optional, Dict, Any
from app.services.m365_agent import M365AgentService
# Skills imports removed as they are moved to Agent Skills
from app.core.config import DefaultConfig
import logging

logger = logging.getLogger(__name__)


class M365AgentFramework:
    """
    Microsoft 365 Agent Framework 管理器
    
    整合所有 Microsoft 365 services 和 skills，提供統一的接口
    """
    
    def __init__(self, config: DefaultConfig):
        """
        初始化 Agent Framework
        
        Args:
            config: 應用配置
        """
        self.config = config
        self.m365_service: Optional[M365AgentService] = None
        
        
        # 初始化框架
        self._initialize_framework()
    
    def _initialize_framework(self):
        """初始化整個 Agent Framework"""
        try:
            # 初始化 Microsoft 365 服務
            self.m365_service = M365AgentService(self.config)
            
            # Skills 已被移動至 Agent Skills (.antigravity/skills)，在此停用初始化
            logger.info("Microsoft 365 Agent Framework 已初始化 (Skills 已遷移至 Agent Skills 並停用)")
        except Exception as e:
            logger.error(f"初始化 Agent Framework 失敗: {str(e)}")
            raise
    

    
    async def get_user_context(self, user_id: str = "me") -> Dict[str, Any]:
        """
        取得使用者完整上下文信息
        
        包括個人資料
        """
        try:
            context = {
                "user_id": user_id,
                "profile": await self.m365_service.get_user_profile(user_id)
            }
            
            return context
        except Exception as e:
            logger.error(f"取得使用者上下文失敗: {str(e)}")
            return {"error": str(e)}
