"""
認證技能 - 處理 SSO 和身份驗證

遷移自: bot/dialogs/sso_dialog.py
功能:
    - OAuth 2.0 SSO 流程
    - 令牌獲取和刷新
    - 用戶身份驗證
    - 會話管理
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from azure.identity import DefaultAzureCredential
from pydantic import BaseModel
from app.services.m365_agent import GraphApiClient
import logging

logger = logging.getLogger(__name__)


class AuthTokenInfo(BaseModel):
    """認證令牌信息"""
    user_id: str
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: int = 3600
    scope: str = "default"
    authenticated_at: datetime = None
    expires_at: datetime = None
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.authenticated_at is None:
            self.authenticated_at = datetime.utcnow()
        if self.expires_at is None:
            self.expires_at = self.authenticated_at + timedelta(seconds=self.expires_in)
    
    def is_expired(self) -> bool:
        """檢查令牌是否已過期"""
        return datetime.utcnow() > self.expires_at
    
    def get_remaining_seconds(self) -> int:
        """獲取令牌剩餘秒數"""
        remaining = (self.expires_at - datetime.utcnow()).total_seconds()
        return max(0, int(remaining))


class UserAuthContext(BaseModel):
    """用戶認證上下文"""
    user_id: str
    channel_id: str
    conversation_id: str
    authenticated: bool = False
    token_info: Optional[AuthTokenInfo] = None
    auth_method: str = "oauth"  # oauth, saml, custom
    metadata: Dict[str, Any] = {}


class AuthenticationSkill:
    """
    認證技能 - 處理 SSO 和身份驗證
    
    遷移自: bot/dialogs/sso_dialog.py
    
    功能:
        - OAuth 2.0 SSO 流程
        - 令牌獲取和刷新
        - 用戶身份驗證
        - 會話管理
        - 用戶個人資料檢索
    """
    
    def __init__(self):
        """初始化認證技能"""
        self.name = "authentication"
        self.description = "處理用戶 SSO 身份驗證和令牌管理"
        
        try:
            self.credential = DefaultAzureCredential()
        except Exception as e:
            logger.warning(f"無法初始化 DefaultAzureCredential: {str(e)}")
            self.credential = None
        
        self.graph_client: Optional[GraphApiClient] = None
        self.authenticated_users: Dict[str, AuthTokenInfo] = {}
        self.user_contexts: Dict[str, UserAuthContext] = {}
        
        logger.info(f"✅ AuthenticationSkill 已初始化")
    
    async def get_auth_prompt(
        self, 
        connection_name: str = "SSO",
        custom_text: str = None
    ) -> Dict[str, Any]:
        """
        獲取認證提示信息
        
        遷移自: SSODialog.prompt_step()
        
        參數:
            connection_name: OAuth 連接名稱
            custom_text: 自定義提示文本
        
        返回:
            認證提示配置字典
        """
        return {
            "status": "success",
            "prompt": custom_text or "請登入 (Please sign in)",
            "title": "登入 (Sign In)",
            "subtitle": "為了繼續，請完成身份驗證",
            "timeout": 300000,  # 5 分鐘
            "connection_name": connection_name,
            "auth_method": "oauth"
        }
    
    async def authenticate_user(
        self,
        user_id: str,
        token: str,
        conversation_id: str = None,
        channel_id: str = None
    ) -> Dict[str, Any]:
        """
        認證用戶並存儲令牌
        
        遷移自: SSODialog.login_step()
        
        參數:
            user_id: 用戶 ID
            token: OAuth 訪問令牌
            conversation_id: 對話 ID
            channel_id: 頻道 ID
        
        返回:
            認證結果字典
        """
        try:
            # 創建令牌信息
            token_info = AuthTokenInfo(
                user_id=user_id,
                access_token=token,
                refresh_token=None,
                token_type="Bearer",
                expires_in=3600,
                scope="profile email offline_access"
            )
            
            # 存儲令牌
            self.authenticated_users[user_id] = token_info
            
            # 創建用戶認證上下文
            if conversation_id and channel_id:
                context = UserAuthContext(
                    user_id=user_id,
                    channel_id=channel_id,
                    conversation_id=conversation_id,
                    authenticated=True,
                    token_info=token_info,
                    auth_method="oauth"
                )
                self.user_contexts[user_id] = context
            
            logger.info(f"✅ 用戶 {user_id} 已成功認證")
            
            return {
                "status": "success",
                "message": f"用戶已成功認證",
                "user_id": user_id,
                "authenticated": True,
                "expires_in": token_info.expires_in
            }
        
        except Exception as e:
            logger.error(f"❌ 認證失敗 (用戶 {user_id}): {str(e)}")
            return {
                "status": "error",
                "message": f"認證失敗: {str(e)}",
                "error": str(e),
                "user_id": user_id
            }
    
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        獲取認證用戶的個人資料
        
        參數:
            user_id: 用戶 ID
        
        返回:
            用戶個人資料信息
        """
        if user_id not in self.authenticated_users:
            return {
                "status": "error",
                "message": "用戶未認證",
                "user_id": user_id
            }
        
        try:
            if not self.credential:
                return {
                    "status": "error",
                    "message": "Azure 認證不可用",
                    "user_id": user_id
                }
            
            # 在實際應用中，可以使用令牌來調用 Graph API
            # 此處為示例實現
            return {
                "status": "success",
                "user_id": user_id,
                "profile": {
                    "mail": "user@example.com",
                    "displayName": "User Name"
                }
            }
        
        except Exception as e:
            logger.error(f"❌ 獲取個人資料失敗 (用戶 {user_id}): {str(e)}")
            return {
                "status": "error",
                "message": f"獲取個人資料失敗: {str(e)}",
                "user_id": user_id
            }
    
    async def refresh_token(self, user_id: str) -> Dict[str, Any]:
        """
        刷新用戶令牌
        
        參數:
            user_id: 用戶 ID
        
        返回:
            刷新結果
        """
        if user_id not in self.authenticated_users:
            return {
                "status": "error",
                "message": "用戶未認證",
                "user_id": user_id
            }
        
        try:
            token_info = self.authenticated_users[user_id]
            
            # 模擬令牌刷新 (在實際應用中應使用刷新令牌)
            token_info.authenticated_at = datetime.utcnow()
            token_info.expires_at = datetime.utcnow() + timedelta(seconds=token_info.expires_in)
            
            logger.info(f"✅ 用戶 {user_id} 的令牌已刷新")
            
            return {
                "status": "success",
                "message": "令牌已刷新",
                "user_id": user_id,
                "expires_in": token_info.expires_in,
                "expires_at": token_info.expires_at.isoformat()
            }
        
        except Exception as e:
            logger.error(f"❌ 令牌刷新失敗 (用戶 {user_id}): {str(e)}")
            return {
                "status": "error",
                "message": f"令牌刷新失敗: {str(e)}",
                "user_id": user_id
            }
    
    async def logout_user(self, user_id: str) -> Dict[str, Any]:
        """
        登出用戶
        
        參數:
            user_id: 用戶 ID
        
        返回:
            登出結果
        """
        try:
            removed = False
            
            if user_id in self.authenticated_users:
                del self.authenticated_users[user_id]
                removed = True
            
            if user_id in self.user_contexts:
                del self.user_contexts[user_id]
                removed = True
            
            if removed:
                logger.info(f"✅ 用戶 {user_id} 已登出")
                return {
                    "status": "success",
                    "message": "用戶已登出",
                    "user_id": user_id
                }
            
            return {
                "status": "warning",
                "message": "用戶未登錄",
                "user_id": user_id
            }
        
        except Exception as e:
            logger.error(f"❌ 登出失敗 (用戶 {user_id}): {str(e)}")
            return {
                "status": "error",
                "message": f"登出失敗: {str(e)}",
                "user_id": user_id
            }
    
    async def is_user_authenticated(self, user_id: str) -> bool:
        """
        檢查用戶是否已認證
        
        參數:
            user_id: 用戶 ID
        
        返回:
            認證狀態
        """
        if user_id not in self.authenticated_users:
            return False
        
        token_info = self.authenticated_users[user_id]
        return not token_info.is_expired()
    
    async def get_user_auth_context(self, user_id: str) -> Optional[UserAuthContext]:
        """
        獲取用戶認證上下文
        
        參數:
            user_id: 用戶 ID
        
        返回:
            用戶認證上下文或 None
        """
        return self.user_contexts.get(user_id)
    
    async def check_token_expiry(self, user_id: str) -> Dict[str, Any]:
        """
        檢查令牌過期狀態
        
        參數:
            user_id: 用戶 ID
        
        返回:
            令牌狀態信息
        """
        if user_id not in self.authenticated_users:
            return {
                "status": "not_authenticated",
                "user_id": user_id
            }
        
        token_info = self.authenticated_users[user_id]
        remaining = token_info.get_remaining_seconds()
        
        status = "valid"
        if remaining < 60:
            status = "expiring_soon"
        elif token_info.is_expired():
            status = "expired"
        
        return {
            "status": status,
            "user_id": user_id,
            "remaining_seconds": remaining,
            "expires_at": token_info.expires_at.isoformat()
        }
    
    async def get_authenticated_users(self) -> List[str]:
        """
        獲取所有已認證的用戶列表
        
        返回:
            已認證的用戶 ID 列表
        """
        return list(self.authenticated_users.keys())
    
    def get_capability_description(self) -> Dict[str, Any]:
        """
        獲取技能的功能描述
        
        返回:
            技能描述字典
        """
        return {
            "name": "認證技能",
            "description": "處理用戶 SSO 身份驗證和令牌管理",
            "version": "1.0.0",
            "methods": {
                "get_auth_prompt": {
                    "description": "獲取認證提示信息",
                    "parameters": ["connection_name", "custom_text"],
                    "returns": "認證提示配置"
                },
                "authenticate_user": {
                    "description": "認證用戶並存儲令牌",
                    "parameters": ["user_id", "token", "conversation_id", "channel_id"],
                    "returns": "認證結果"
                },
                "get_user_profile": {
                    "description": "獲取認證用戶的個人資料",
                    "parameters": ["user_id"],
                    "returns": "用戶個人資料"
                },
                "refresh_token": {
                    "description": "刷新用戶令牌",
                    "parameters": ["user_id"],
                    "returns": "刷新結果"
                },
                "logout_user": {
                    "description": "登出用戶",
                    "parameters": ["user_id"],
                    "returns": "登出結果"
                },
                "is_user_authenticated": {
                    "description": "檢查用戶認證狀態",
                    "parameters": ["user_id"],
                    "returns": "布爾值"
                },
                "check_token_expiry": {
                    "description": "檢查令牌過期狀態",
                    "parameters": ["user_id"],
                    "returns": "令牌狀態信息"
                }
            },
            "migration_notes": "遷移自 bot/dialogs/sso_dialog.py",
            "dependencies": ["azure-identity", "msgraph-core"],
            "async_support": True
        }


# 為了向後相容性，也導出相關類
__all__ = ['AuthenticationSkill', 'AuthTokenInfo', 'UserAuthContext']
