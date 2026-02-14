"""
AuthenticationSkill 單元測試

測試認證功能、令牌管理和用戶會話
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from app.services.skills.authentication_skill import (
    AuthenticationSkill,
    AuthTokenInfo,
    UserAuthContext
)


class TestAuthTokenInfo:
    """測試 AuthTokenInfo 數據類"""
    
    def test_token_creation(self):
        """測試令牌創建"""
        token = AuthTokenInfo(
            user_id="user123",
            access_token="test_token",
            expires_in=3600
        )
        
        assert token.user_id == "user123"
        assert token.access_token == "test_token"
        assert token.expires_in == 3600
        assert token.authenticated_at is not None
        assert token.expires_at is not None
    
    def test_token_not_expired(self):
        """測試令牌未過期"""
        token = AuthTokenInfo(
            user_id="user123",
            access_token="test_token",
            expires_in=3600
        )
        
        assert token.is_expired() is False
        remaining = token.get_remaining_seconds()
        assert remaining > 0
        assert remaining <= 3600
    
    def test_token_expired(self):
        """測試令牌已過期"""
        token = AuthTokenInfo(
            user_id="user123",
            access_token="test_token",
            expires_in=1
        )
        
        # 設置過期時間為過去
        token.expires_at = datetime.utcnow() - timedelta(seconds=10)
        
        assert token.is_expired() is True
        remaining = token.get_remaining_seconds()
        assert remaining == 0


class TestUserAuthContext:
    """測試 UserAuthContext 數據類"""
    
    def test_context_creation(self):
        """測試上下文創建"""
        context = UserAuthContext(
            user_id="user123",
            channel_id="teams",
            conversation_id="conv123",
            authenticated=True
        )
        
        assert context.user_id == "user123"
        assert context.channel_id == "teams"
        assert context.authenticated is True
        assert context.metadata == {}


class TestAuthenticationSkill:
    """測試 AuthenticationSkill"""
    
    @pytest.fixture
    def auth_skill(self):
        """提供 AuthenticationSkill 實例"""
        return AuthenticationSkill()
    
    def test_skill_initialization(self, auth_skill):
        """測試技能初始化"""
        assert auth_skill.name == "authentication"
        assert auth_skill.description is not None
        assert auth_skill.authenticated_users == {}
        assert auth_skill.user_contexts == {}
    
    @pytest.mark.asyncio
    async def test_get_auth_prompt(self, auth_skill):
        """測試獲取認證提示"""
        result = await auth_skill.get_auth_prompt()
        
        assert result["status"] == "success"
        assert "prompt" in result
        assert "title" in result
        assert result["timeout"] == 300000
        assert result["connection_name"] == "SSO"
    
    @pytest.mark.asyncio
    async def test_authenticate_user(self, auth_skill):
        """測試用戶認證"""
        result = await auth_skill.authenticate_user(
            user_id="user123",
            token="test_token_123"
        )
        
        assert result["status"] == "success"
        assert result["user_id"] == "user123"
        assert result["authenticated"] is True
        assert "user123" in auth_skill.authenticated_users
    
    @pytest.mark.asyncio
    async def test_authenticate_user_with_context(self, auth_skill):
        """測試帶上下文的用戶認證"""
        result = await auth_skill.authenticate_user(
            user_id="user123",
            token="test_token_123",
            conversation_id="conv123",
            channel_id="teams"
        )
        
        assert result["status"] == "success"
        assert "user123" in auth_skill.user_contexts
        
        context = auth_skill.user_contexts["user123"]
        assert context.user_id == "user123"
        assert context.conversation_id == "conv123"
        assert context.channel_id == "teams"
    
    @pytest.mark.asyncio
    async def test_is_user_authenticated(self, auth_skill):
        """測試用戶認證檢查"""
        # 未認證用戶
        assert await auth_skill.is_user_authenticated("unknown_user") is False
        
        # 認證用戶
        await auth_skill.authenticate_user("user123", "test_token")
        assert await auth_skill.is_user_authenticated("user123") is True
    
    @pytest.mark.asyncio
    async def test_logout_user(self, auth_skill):
        """測試用戶登出"""
        # 認證用戶
        await auth_skill.authenticate_user("user123", "test_token")
        assert "user123" in auth_skill.authenticated_users
        
        # 登出用戶
        result = await auth_skill.logout_user("user123")
        assert result["status"] == "success"
        assert "user123" not in auth_skill.authenticated_users
    
    @pytest.mark.asyncio
    async def test_logout_nonexistent_user(self, auth_skill):
        """測試登出不存在的用戶"""
        result = await auth_skill.logout_user("unknown_user")
        assert result["status"] == "warning"
    
    @pytest.mark.asyncio
    async def test_get_user_profile(self, auth_skill):
        """測試獲取用戶個人資料"""
        # 未認證用戶
        result = await auth_skill.get_user_profile("unknown_user")
        assert result["status"] == "error"
        assert "未認證" in result["message"]
        
        # 認證用戶
        await auth_skill.authenticate_user("user123", "test_token")
        result = await auth_skill.get_user_profile("user123")
        assert result["status"] == "success"
        assert result["user_id"] == "user123"
    
    @pytest.mark.asyncio
    async def test_refresh_token(self, auth_skill):
        """測試令牌刷新"""
        # 未認證用戶
        result = await auth_skill.refresh_token("unknown_user")
        assert result["status"] == "error"
        
        # 認證用戶
        await auth_skill.authenticate_user("user123", "test_token")
        original_token = auth_skill.authenticated_users["user123"]
        original_time = original_token.authenticated_at
        
        # 等待一小段時間後刷新
        await asyncio.sleep(0.1)
        result = await auth_skill.refresh_token("user123")
        
        assert result["status"] == "success"
        assert result["user_id"] == "user123"
        
        # 驗證刷新後的令牌時間已更新
        refreshed_token = auth_skill.authenticated_users["user123"]
        assert refreshed_token.authenticated_at > original_time
    
    @pytest.mark.asyncio
    async def test_check_token_expiry(self, auth_skill):
        """測試令牌過期檢查"""
        # 未認證用戶
        result = await auth_skill.check_token_expiry("unknown_user")
        assert result["status"] == "not_authenticated"
        
        # 認證用戶
        await auth_skill.authenticate_user("user123", "test_token")
        result = await auth_skill.check_token_expiry("user123")
        
        assert result["status"] == "valid"
        assert result["user_id"] == "user123"
        assert result["remaining_seconds"] > 0
        assert "expires_at" in result
    
    @pytest.mark.asyncio
    async def test_check_token_expiring_soon(self, auth_skill):
        """測試令牌即將過期"""
        # 認證用戶
        await auth_skill.authenticate_user("user123", "test_token")
        
        # 修改過期時間為即將過期
        token = auth_skill.authenticated_users["user123"]
        token.expires_at = datetime.utcnow() + timedelta(seconds=30)
        
        result = await auth_skill.check_token_expiry("user123")
        assert result["status"] == "expiring_soon"
        assert result["remaining_seconds"] < 60
    
    @pytest.mark.asyncio
    async def test_get_authenticated_users(self, auth_skill):
        """測試獲取已認證用戶列表"""
        # 初始為空
        users = await auth_skill.get_authenticated_users()
        assert len(users) == 0
        
        # 認證多個用戶
        await auth_skill.authenticate_user("user1", "token1")
        await auth_skill.authenticate_user("user2", "token2")
        await auth_skill.authenticate_user("user3", "token3")
        
        users = await auth_skill.get_authenticated_users()
        assert len(users) == 3
        assert "user1" in users
        assert "user2" in users
        assert "user3" in users
    
    @pytest.mark.asyncio
    async def test_get_user_auth_context(self, auth_skill):
        """測試獲取用戶認證上下文"""
        # 未建立上下文
        context = await auth_skill.get_user_auth_context("unknown_user")
        assert context is None
        
        # 認證用戶並建立上下文
        await auth_skill.authenticate_user(
            user_id="user123",
            token="test_token",
            conversation_id="conv123",
            channel_id="teams"
        )
        
        context = await auth_skill.get_user_auth_context("user123")
        assert context is not None
        assert context.user_id == "user123"
        assert context.conversation_id == "conv123"
    
    def test_get_capability_description(self, auth_skill):
        """測試獲取技能描述"""
        description = auth_skill.get_capability_description()
        
        assert description["name"] == "認證技能"
        assert "description" in description
        assert "methods" in description
        assert len(description["methods"]) > 0
        assert "authenticate_user" in description["methods"]
        assert "migration_notes" in description


class TestAuthenticationWorkflow:
    """測試完整的認證工作流程"""
    
    @pytest.mark.asyncio
    async def test_complete_sso_workflow(self):
        """測試完整的 SSO 工作流程"""
        skill = AuthenticationSkill()
        user_id = "user123"
        
        # 1. 獲取認證提示
        prompt = await skill.get_auth_prompt()
        assert prompt["status"] == "success"
        
        # 2. 認證用戶
        auth_result = await skill.authenticate_user(
            user_id=user_id,
            token="oauth_token_xyz",
            conversation_id="conv123",
            channel_id="teams"
        )
        assert auth_result["status"] == "success"
        
        # 3. 檢查認證狀態
        is_auth = await skill.is_user_authenticated(user_id)
        assert is_auth is True
        
        # 4. 獲取用戶個人資料
        profile = await skill.get_user_profile(user_id)
        assert profile["status"] == "success"
        
        # 5. 檢查令牌狀態
        expiry = await skill.check_token_expiry(user_id)
        assert expiry["status"] == "valid"
        
        # 6. 登出用戶
        logout_result = await skill.logout_user(user_id)
        assert logout_result["status"] == "success"
        
        # 7. 驗證已登出
        is_auth = await skill.is_user_authenticated(user_id)
        assert is_auth is False
    
    @pytest.mark.asyncio
    async def test_multiple_users_workflow(self):
        """測試多用戶認證工作流程"""
        skill = AuthenticationSkill()
        
        # 認證 3 個用戶
        users = ["alice@example.com", "bob@example.com", "charlie@example.com"]
        
        for user in users:
            result = await skill.authenticate_user(user, f"token_{user}")
            assert result["status"] == "success"
        
        # 驗證所有用戶已認證
        authenticated = await skill.get_authenticated_users()
        assert len(authenticated) == 3
        
        # 登出第一個用戶
        logout = await skill.logout_user(users[0])
        assert logout["status"] == "success"
        
        # 驗證只剩 2 個用戶
        authenticated = await skill.get_authenticated_users()
        assert len(authenticated) == 2
        assert users[0] not in authenticated


if __name__ == "__main__":
    # 運行測試
    # pytest test_authentication_skill.py -v
    print("✅ AuthenticationSkill 測試套件已準備")
    print("運行命令: pytest tests/unit/test_authentication_skill.py -v")
