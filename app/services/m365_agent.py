"""
Microsoft 365 Agent Framework 整合模組

提供與 Microsoft 365 services 互動的 agent 功能，包括：
- Microsoft Graph API 整合
- Teams 互動
- OneDrive/SharePoint 檔案訪問
"""

from typing import Optional, List
from pydantic import BaseModel
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AccessToken
from app.core.config import DefaultConfig
import logging
import httpx
import inspect

logger = logging.getLogger(__name__)


class M365Credential(BaseModel):
    """Microsoft 365 認證配置"""
    tenant_id: str
    client_id: str
    client_secret: str
    scope: Optional[List[str]] = None


class GraphApiClient:
    """輕量版 Graph API Client，使用 httpx + Azure Identity。"""

    def __init__(self, credential, scopes: List[str], base_url: str = "https://graph.microsoft.com/v1.0"):
        self._credential = credential
        self._scopes = scopes
        self._client = httpx.AsyncClient(base_url=base_url, timeout=30.0)

    async def _get_access_token(self) -> str:
        token = self._credential.get_token(*self._scopes)
        if inspect.iscoroutine(token):
            token = await token
        return token.token if hasattr(token, "token") else str(token)

    async def get(self, path: str, params: dict | None = None) -> dict:
        access_token = await self._get_access_token()
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await self._client.get(path, params=params, headers=headers)
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        await self._client.aclose()


class M365AgentService:
    """
    Microsoft 365 Agent Framework 服務
    
    管理 Microsoft 365 services 的整合，包括圖表 API 和授權。
    """
    
    def __init__(self, config: DefaultConfig):
        """
        初始化 M365 Agent 服務
        
        Args:
            config: 應用配置
        """
        self.config = config
        self.graph_client: Optional[GraphApiClient] = None
        self.credential: Optional[DefaultAzureCredential] = None
        self._initialize_app_client()
    
    def _initialize_app_client(self):
        """初始化 Application-level Microsoft Graph 客戶端 (使用 DefaultAzureCredential)"""
        try:
            # 使用 DefaultAzureCredential 進行驗證
            self.credential = DefaultAzureCredential(
                exclude_shared_token_cache_credential=True
            )
            
            # 建立 Graph 客戶端
            self.graph_client = GraphApiClient(
                credential=self.credential,
                scopes=["https://graph.microsoft.com/.default"],
            )
            logger.info("Microsoft Graph App-Level 客戶端已初始化")
        except Exception as e:
            logger.error(f"初始化 Microsoft Graph 客戶端失敗: {str(e)}")
            raise

    def get_graph_client(self, token: str = None) -> GraphApiClient:
        """
        取得 Graph Client
        
        Args:
            token: User Access Token (Delegated Auth). 如果為 None，則返回 App-Level Client。
        """
        if not token:
            # 返回預設的 App-Level Client
            return self.graph_client
        
        # 使用 User Token 建立新的 Graph Client (Delegated)
        # 這裡我們使用 Azure Identity 的 OnBehalfOfCredential 或直接使用 TokenCredential
        # 為了簡單起見，我們構建一個簡單的 TokenCredentialWrapper
        
        class SimpleTokenCredential:
            def __init__(self, token):
                self.token = token
            def get_token(self, *scopes, **kwargs):
                # 假設 token 未過期，實際生產環境應檢查過期時間
                import time
                return AccessToken(self.token, int(time.time() + 3600))

        return GraphApiClient(
            credential=SimpleTokenCredential(token),
            scopes=["https://graph.microsoft.com/.default"],
        )
    
    async def get_user_profile(self, user_id: str = "me", token: str = None) -> dict:
        """
        取得使用者個人資料
        
        Args:
            user_id: 使用者 ID，預設為 "me"（當前使用者）
            
        Returns:
            使用者個人資料字典
        """
        try:
            client = self.get_graph_client(token)
            if not client:
                return {"error": "Graph client not initialized"}
            
            response = await client.get(f"/users/{user_id}")
            return response
        except Exception as e:
            logger.error(f"無法取得使用者個人資料: {str(e)}")
            return {"error": str(e)}
    
    async def list_user_emails(self, user_id: str = "me", top: int = 10, token: str = None) -> dict:
        """
        列出使用者的電子郵件
        
        Args:
            user_id: 使用者 ID
            top: 返回的郵件數量
            
        Returns:
            郵件清單
        """
        try:
            client = self.get_graph_client(token)
            if not client:
                return {"error": "Graph client not initialized"}
            
            response = await client.get(
                f"/users/{user_id}/mailFolders/inbox/messages",
                params={"$top": top}
            )
            return response
        except Exception as e:
            logger.error(f"無法列出使用者郵件: {str(e)}")
            return {"error": str(e)}
    
    async def get_user_calendar_events(
        self, 
        user_id: str = "me", 
        top: int = 10,
        token: str = None
    ) -> dict:
        """
        取得使用者的日曆事件
        
        Args:
            user_id: 使用者 ID
            top: 返回的事件數量
            
        Returns:
            日曆事件清單
        """
        try:
            client = self.get_graph_client(token)
            if not client:
                return {"error": "Graph client not initialized"}
            
            response = await client.get(
                f"/users/{user_id}/calendarview",
                params={"$top": top}
            )
            return response
        except Exception as e:
            logger.error(f"無法取得使用者日曆事件: {str(e)}")
            return {"error": str(e)}
    
    async def list_user_drive_items(
        self, 
        user_id: str = "me",
        top: int = 10,
        token: str = None
    ) -> dict:
        """
        列出使用者 OneDrive 中的項目
        
        Args:
            user_id: 使用者 ID
            top: 返回的項目數量
            
        Returns:
            項目清單
        """
        try:
            client = self.get_graph_client(token)
            if not client:
                return {"error": "Graph client not initialized"}
            
            response = await client.get(
                f"/users/{user_id}/drive/root/children",
                params={"$top": top}
            )
            return response
        except Exception as e:
            logger.error(f"無法列出使用者 OneDrive 項目: {str(e)}")
            return {"error": str(e)}
    
    async def search_teams_messages(
        self, 
        team_id: str,
        search_query: str,
        top: int = 10,
        token: str = None
    ) -> dict:
        """
        搜尋 Teams 訊息
        
        Args:
            team_id: Teams 群組 ID
            search_query: 搜尋查詢
            top: 返回的結果數量
            
        Returns:
            搜尋結果
        """
        try:
            client = self.get_graph_client(token)
            if not client:
                return {"error": "Graph client not initialized"}
            
            response = await client.post(
                "/search/query",
                json={
                    "requests": [
                        {
                            "entityTypes": ["chatMessage"],
                            "query": {
                                "query_string": search_query
                            },
                            "from": 0,
                            "size": top
                        }
                    ]
                }
            )
            return response
        except Exception as e:
            logger.error(f"無法搜尋 Teams 訊息: {str(e)}")
            return {"error": str(e)}
