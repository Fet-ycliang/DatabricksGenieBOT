"""Microsoft Graph API 服務，用於取得 Teams 使用者資訊"""

import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from botbuilder.core import TurnContext
from botbuilder.schema import TokenResponse
import aiohttp

logger = logging.getLogger(__name__)


class GraphService:
    """處理與 Microsoft Graph API 的互動"""
    
    GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0"
    
    def __init__(self, connection_name: str = "GraphConnection"):
        """
        初始化 Graph Service
        
        Args:
            connection_name: OAuth 連線名稱（在 Azure Portal 中設定）
        """
        self.connection_name = connection_name
        # ✅ 新增：HTTP 連接池（重用 Session）
        self._http_session: Optional[aiohttp.ClientSession] = None
    
    @asynccontextmanager
    async def get_http_session(self):
        """重用 HTTP Session 減少連接開銷"""
        if self._http_session is None or self._http_session.closed:
            connector = aiohttp.TCPConnector(limit=50, limit_per_host=10)
            timeout = aiohttp.ClientTimeout(total=30)
            self._http_session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )
            logger.info("🔌 GraphService: 已創建新的 HTTP Session（連接池：50，每主機：10）")
        try:
            yield self._http_session
        finally:
            pass  # 重用，不關閉
    
    async def close(self):
        """關閉 HTTP Session（應用程式關閉時調用）"""
        if self._http_session and not self._http_session.closed:
            await self._http_session.close()
            logger.info("🔌 GraphService: 已關閉 HTTP Session")
    
    @staticmethod
    def create_user_profile_card(user_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        創建用戶資料 Adaptive Card
        
        Args:
            user_info: 包含使用者信息的字典
                - email: 電子郵件
                - name: 顯示名稱
                - id: Azure AD Object ID
                - phone_numbers: 電話號碼（可選）
                - office_location: 辦公地點（可選）
                - job_title: 職位（可選）
                - department: 部門（可選）
        
        Returns:
            Adaptive Card JSON 結構
        """
        email = user_info.get('email', 'N/A')
        name = user_info.get('name', '未知使用者')
        aad_id = user_info.get('id', 'N/A')
        phone = user_info.get('phone_numbers', [None])[0] if user_info.get('phone_numbers') else None
        office = user_info.get('office_location', 'N/A')
        job_title = user_info.get('job_title', 'N/A')
        department = user_info.get('department', 'N/A')
        
        # 構建信息行（跳過空值）
        info_facts = [
            {
                "name": "📧 電子郵件",
                "value": email
            },
            {
                "name": "🏢 部門",
                "value": department
            }
        ]
        
        if job_title != 'N/A':
            info_facts.insert(2, {
                "name": "💼 職位",
                "value": job_title
            })
        
        if office != 'N/A':
            info_facts.insert(3, {
                "name": "📍 辦公地點",
                "value": office
            })
        
        if phone:
            info_facts.insert(4, {
                "name": "📞 電話",
                "value": phone
            })
        
        card = {
            "type": "AdaptiveCard",
            "version": "1.5",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "body": [
                {
                    "type": "Container",
                    "style": "emphasis",
                    "items": [
                        {
                            "type": "ColumnSet",
                            "columns": [
                                {
                                    "type": "Column",
                                    "width": "auto",
                                    "items": [
                                        {
                                            "type": "TextBlock",
                                            "text": "👤",
                                            "size": "Large"
                                        }
                                    ]
                                },
                                {
                                    "type": "Column",
                                    "width": "stretch",
                                    "items": [
                                        {
                                            "type": "TextBlock",
                                            "text": "使用者資料",
                                            "weight": "Bolder",
                                            "size": "Medium",
                                            "color": "Accent"
                                        },
                                        {
                                            "type": "TextBlock",
                                            "text": name,
                                            "isSubtle": True,
                                            "spacing": "None"
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                },
                {
                    "type": "Container",
                    "items": [
                        {
                            "type": "FactSet",
                            "facts": info_facts
                        }
                    ],
                    "spacing": "Medium"
                },
                {
                    "type": "Container",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": f"🔐 Azure AD ID: {aad_id[:12]}...",
                            "isSubtle": True,
                            "size": "Small",
                            "wrap": True
                        }
                    ],
                    "spacing": "Small"
                }
            ]
        }
        
        return card
    
    async def get_user_token(self, turn_context: TurnContext) -> Optional[TokenResponse]:
        """
        為當前使用者取得 OAuth token
        
        Args:
            turn_context: Bot Framework 的 TurnContext
            
        Returns:
            TokenResponse 或 None
        """
        try:
            # ✅ 修正：使用正確的 CloudAdapter API
            # CloudAdapter 的 get_user_token 需要：
            # 1. user_id: 使用者 ID
            # 2. connection_name: OAuth 連線名稱
            # 3. channel_id: 頻道 ID
            # 4. magic_code: (可選) 登入代碼
            
            user_id = turn_context.activity.from_property.id
            channel_id = turn_context.activity.channel_id
            
            token_response = await turn_context.adapter.get_user_token(
                context=turn_context,
                connection_name=self.connection_name
            )
            
            if token_response and token_response.token:
                logger.info(f"✅ 成功取得使用者 {user_id} 的 token")
                return token_response
            else:
                logger.warning(f"⚠️ 無法取得使用者 {user_id} 的 token（可能未登入）")
                return None
                
        except AttributeError as e:
            # CloudAdapter 不支援 get_user_token，這是預期的行為
            logger.warning(
                f"⚠️ CloudAdapter 不支援 get_user_token: {e}\n"
                f"   必須在 Azure Portal 中設定 OAuth Connection"
            )
            return None
        except Exception as e:
            logger.error(f"❌ 取得使用者 token 時發生錯誤: {str(e)}")
            return None
    
    async def get_user_profile(self, token: str) -> Optional[Dict[str, Any]]:
        """
        使用 Graph API 取得使用者個人資料
        
        Args:
            token: OAuth access token
            
        Returns:
            包含使用者資訊的字典或 None
        """
        try:
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            # ✅ 使用共享 HTTP Session
            async with self.get_http_session() as session:
                async with session.get(
                    f"{self.GRAPH_API_ENDPOINT}/me",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        user_data = await response.json()
                        logger.info(f"成功取得使用者資料: {user_data.get('userPrincipalName')}")
                        return user_data
                    else:
                        logger.error(f"Graph API 錯誤: {response.status}")
                        error_text = await response.text()
                        logger.error(f"錯誤詳情: {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"呼叫 Graph API 時發生錯誤: {str(e)}")
            return None
    
    async def get_user_groups(self, turn_context: TurnContext) -> Optional[list[dict]]:
        """
        列出使用者直接所屬的 Azure AD 群組
        
        Args:
            turn_context: Bot Framework 的 TurnContext
            
        Returns:
            群組/角色清單或 None
        """
        try:
            token_response = await self.get_user_token(turn_context)
            if not token_response or not token_response.token:
                logger.warning("無法取得使用者 token，無法查詢 memberOf")
                return None

            headers = {
                "Authorization": f"Bearer {token_response.token}",
                "Content-Type": "application/json"
            }

            # ✅ 使用共享 HTTP Session
            async with self.get_http_session() as session:
                async with session.get(
                    f"{self.GRAPH_API_ENDPOINT}/me/memberOf",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        groups = data.get("value", [])
                        logger.info(f"成功取得 {len(groups)} 個 memberOf 群組/角色")
                        return groups
                    else:
                        text = await response.text()
                        logger.error(f"memberOf 查詢失敗: {response.status} - {text}")
                        return None
        except Exception as e:
            logger.error(f"呼叫 memberOf 時發生錯誤: {str(e)}")
            return None
    
    async def get_user_email_and_id(self, turn_context: TurnContext) -> Optional[Dict[str, str]]:
        """
        取得使用者的 email 和 OpenID 資訊
        
        優先級：
        1. 首先嘗試從 Teams channel_data 取得 (無需 OAuth)
        2. 其次嘗試使用 OAuth token 呼叫 Graph API
        3. 最後回退到最小化資訊
        
        Args:
            turn_context: Bot Framework 的 TurnContext
            
        Returns:
            包含 'email', 'id', 'name', 'upn' 的字典或 None
        """
        from_property = turn_context.activity.from_property
        channel_data = turn_context.activity.channel_data
        
        # ✅ 步驟 1: 從 Teams 提供的信息中提取（不需要 OAuth）
        teams_user_aad_id = None
        teams_user_email = None
        
        if channel_data:
            teams_user = channel_data.get('teamsUser', {})
            teams_user_aad_id = teams_user.get('aadObjectId')
            teams_user_email = teams_user.get('email')
        
        logger.info(
            f"📱 Teams 提供的基本信息:\n"
            f"   User ID: {from_property.id}\n"
            f"   Name: {getattr(from_property, 'name', 'N/A')}\n"
            f"   AAD ID: {teams_user_aad_id or '未提供'}\n"
            f"   Email: {teams_user_email or '未提供'}"
        )
        
        # ✅ 步驟 2: 嘗試透過 OAuth 取得完整個人資料
        token_response = await self.get_user_token(turn_context)
        
        if token_response and token_response.token:
            logger.info("🔐 OAuth token 已取得，正在呼叫 Graph API 以取得完整資訊...")
            user_profile = await self.get_user_profile(token_response.token)
            
            if user_profile:
                logger.info("✅ Graph API 成功返回完整使用者資訊")
                return {
                    'email': user_profile.get('mail') or user_profile.get('userPrincipalName'),
                    'id': user_profile.get('id'),  # 這是 AAD Object ID (OpenID)
                    'name': user_profile.get('displayName'),
                    'upn': user_profile.get('userPrincipalName'),
                    'given_name': user_profile.get('givenName'),
                    'surname': user_profile.get('surname'),
                    'phone_numbers': user_profile.get('mobilePhone'),
                    'office_location': user_profile.get('officeLocation'),
                    'job_title': user_profile.get('jobTitle'),
                    'department': user_profile.get('department')
                }
        else:
            logger.warning(
                "⚠️ OAuth token 未取得。原因可能是：\n"
                "   1. OAuth Connection 未在 Azure Portal 中配置\n"
                "   2. 使用者未授權存取資訊\n"
                "   3. 使用本地 Bot Emulator (不支持 OAuth)\n"
                "   → 將使用 Teams 提供的基本資訊"
            )
        
        # ✅ 步驟 3: 回退到 Teams 提供的基本資訊
        return {
            'email': teams_user_email or getattr(from_property, 'email', None),
            'id': teams_user_aad_id or from_property.id,
            'name': getattr(from_property, 'name', None),
            'upn': None,
            'given_name': None,
            'surname': None,
            'phone_numbers': None,
            'office_location': None,
            'job_title': None,
            'department': None
        }
    
    async def sign_out_user(self, turn_context: TurnContext) -> bool:
        """
        登出使用者（清除 OAuth token）
        
        Args:
            turn_context: Bot Framework 的 TurnContext
            
        Returns:
            是否成功登出
        """
        try:
            await turn_context.adapter.sign_out_user(
                turn_context,
                self.connection_name
            )
            logger.info(f"使用者 {turn_context.activity.from_property.id} 已登出")
            return True
        except Exception as e:
            logger.error(f"登出使用者時發生錯誤: {str(e)}")
            return False
    
    async def prompt_for_sign_in(self, turn_context: TurnContext) -> None:
        """
        提示使用者登入（顯示 OAuth 登入卡片）
        
        Args:
            turn_context: Bot Framework 的 TurnContext
        """
        try:
            from botbuilder.schema import (
                CardAction,
                ActionTypes,
                Attachment,
                AttachmentLayoutTypes,
                HeroCard,
                OAuthCard
            )
            
            # ✅ 取得 OAuth 登入連結
            sign_in_link = await turn_context.adapter.get_oauth_sign_in_link(
                turn_context,
                self.connection_name
            )
            
            # ✅ 創建 OAuth 登入卡片
            oauth_card = OAuthCard(
                text="請點擊下方按鈕登入以授權存取您的 Microsoft 資訊",
                connection_name=self.connection_name,
                buttons=[
                    CardAction(
                        type=ActionTypes.signin,
                        title="🔐 登入",
                        value=sign_in_link
                    )
                ]
            )
            
            # ✅ 創建附件並發送
            attachment = Attachment(
                content_type="application/vnd.microsoft.card.oauth",
                content=oauth_card
            )
            
            from botbuilder.schema import Activity
            reply = Activity(
                type="message",
                attachments=[attachment]
            )
            
            await turn_context.send_activity(reply)
            logger.info("已傳送 OAuth 登入卡片給使用者")
            
        except Exception as e:
            logger.error(f"提示登入時發生錯誤: {str(e)}")
            # ✅ 如果 OAuth 卡片失敗，回退到文字連結
            try:
                sign_in_link = await turn_context.adapter.get_oauth_sign_in_link(
                    turn_context,
                    self.connection_name
                )
                await turn_context.send_activity(
                    f"🔐 請點擊以下連結登入以授權存取您的 Microsoft 資訊：\n\n{sign_in_link}"
                )
                logger.warning("OAuth 卡片發送失敗，已回退到文字連結")
            except Exception as fallback_error:
                logger.error(f"回退到文字連結也失敗: {str(fallback_error)}")


async def get_teams_user_info(turn_context: TurnContext) -> Dict[str, Optional[str]]:
    """
    快速從 Teams 取得使用者基本資訊（不需要額外的 API 呼叫）
    
    這個函式不需要 OAuth token，直接從 Teams activity 中提取資訊
    
    Args:
        turn_context: Bot Framework 的 TurnContext
        
    Returns:
        包含 'id', 'name', 'aad_object_id' 的字典
    """
    from_property = turn_context.activity.from_property
    channel_data = turn_context.activity.channel_data
    
    # 從 Teams channel data 取得 AAD Object ID
    aad_object_id = None
    user_email = None
    
    if channel_data:
        teams_user = channel_data.get('teamsUser', {})
        aad_object_id = teams_user.get('aadObjectId')
        user_email = teams_user.get('email')
    
    return {
        'id': from_property.id,  # Teams 使用者 ID
        'name': getattr(from_property, 'name', None),
        'aad_object_id': aad_object_id,  # Azure AD Object ID (OpenID)
        'email': user_email
    }
