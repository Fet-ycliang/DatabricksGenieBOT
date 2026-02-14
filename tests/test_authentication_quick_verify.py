#!/usr/bin/env python3
"""
AuthenticationSkill 快速驗證腳本

直接驗證核心功能是否正常運作
"""

import asyncio
import sys
from datetime import datetime, timedelta

# 添加路徑以導入本地模塊
sys.path.insert(0, '.')

try:
    from app.services.skills.authentication_skill import (
        AuthenticationSkill,
        AuthTokenInfo,
        UserAuthContext
    )
    print("✅ 成功導入 AuthenticationSkill")
except Exception as e:
    print(f"❌ 導入失敗: {e}")
    sys.exit(1)


async def run_tests():
    """運行基本功能驗證"""
    
    print("\n" + "="*80)
    print("🧪 AuthenticationSkill 快速驗證")
    print("="*80 + "\n")
    
    # 測試 1: 初始化
    print("【測試 1】初始化 AuthenticationSkill...")
    try:
        skill = AuthenticationSkill()
        print(f"✅ 初始化成功")
        print(f"   - 名稱: {skill.name}")
        print(f"   - 描述: {skill.description}")
    except Exception as e:
        print(f"❌ 初始化失敗: {e}")
        return False
    
    # 測試 2: 獲取認證提示
    print("\n【測試 2】獲取認證提示...")
    try:
        prompt = await skill.get_auth_prompt()
        assert prompt["status"] == "success"
        assert "prompt" in prompt
        print(f"✅ 獲取成功")
        print(f"   - 提示文本: {prompt['prompt']}")
        print(f"   - 標題: {prompt['title']}")
    except Exception as e:
        print(f"❌ 獲取失敗: {e}")
        return False
    
    # 測試 3: 認證用戶
    print("\n【測試 3】認證用戶...")
    try:
        result = await skill.authenticate_user("user123", "test_token")
        assert result["status"] == "success"
        assert result["user_id"] == "user123"
        print(f"✅ 認證成功")
        print(f"   - 用戶 ID: {result['user_id']}")
        print(f"   - 消息: {result['message']}")
    except Exception as e:
        print(f"❌ 認證失敗: {e}")
        return False
    
    # 測試 4: 檢查認證狀態
    print("\n【測試 4】檢查認證狀態...")
    try:
        is_auth = await skill.is_user_authenticated("user123")
        assert is_auth is True
        print(f"✅ 狀態檢查成功")
        print(f"   - 用戶已認證: {is_auth}")
    except Exception as e:
        print(f"❌ 狀態檢查失敗: {e}")
        return False
    
    # 測試 5: 檢查令牌過期狀態
    print("\n【測試 5】檢查令牌過期狀態...")
    try:
        expiry = await skill.check_token_expiry("user123")
        assert expiry["status"] == "valid"
        print(f"✅ 令牌檢查成功")
        print(f"   - 狀態: {expiry['status']}")
        print(f"   - 剩餘秒數: {expiry['remaining_seconds']}")
    except Exception as e:
        print(f"❌ 令牌檢查失敗: {e}")
        return False
    
    # 測試 6: 刷新令牌
    print("\n【測試 6】刷新令牌...")
    try:
        result = await skill.refresh_token("user123")
        assert result["status"] == "success"
        print(f"✅ 令牌刷新成功")
        print(f"   - 消息: {result['message']}")
    except Exception as e:
        print(f"❌ 令牌刷新失敗: {e}")
        return False
    
    # 測試 7: 登出用戶
    print("\n【測試 7】登出用戶...")
    try:
        result = await skill.logout_user("user123")
        assert result["status"] == "success"
        print(f"✅ 登出成功")
        print(f"   - 消息: {result['message']}")
    except Exception as e:
        print(f"❌ 登出失敗: {e}")
        return False
    
    # 測試 8: 驗證已登出
    print("\n【測試 8】驗證已登出...")
    try:
        is_auth = await skill.is_user_authenticated("user123")
        assert is_auth is False
        print(f"✅ 驗證成功")
        print(f"   - 用戶已登出: {not is_auth}")
    except Exception as e:
        print(f"❌ 驗證失敗: {e}")
        return False
    
    # 測試 9: 獲取技能描述
    print("\n【測試 9】獲取技能描述...")
    try:
        desc = skill.get_capability_description()
        assert desc["name"] == "認證技能"
        assert "methods" in desc
        assert len(desc["methods"]) > 0
        print(f"✅ 獲取成功")
        print(f"   - 技能名稱: {desc['name']}")
        print(f"   - 可用方法數: {len(desc['methods'])}")
    except Exception as e:
        print(f"❌ 獲取失敗: {e}")
        return False
    
    # 測試 10: 多用戶處理
    print("\n【測試 10】多用戶處理...")
    try:
        skill2 = AuthenticationSkill()
        
        # 認證 3 個用戶
        users = ["alice@contoso.com", "bob@contoso.com", "charlie@contoso.com"]
        for user in users:
            await skill2.authenticate_user(user, f"token_{user}")
        
        # 獲取已認證用戶列表
        authenticated = await skill2.get_authenticated_users()
        assert len(authenticated) == 3
        
        print(f"✅ 多用戶處理成功")
        print(f"   - 已認證用戶: {len(authenticated)}")
        print(f"   - 用戶列表: {', '.join(authenticated)}")
    except Exception as e:
        print(f"❌ 多用戶處理失敗: {e}")
        return False
    
    return True


async def main():
    """主函數"""
    success = await run_tests()
    
    print("\n" + "="*80)
    if success:
        print("✅ 所有測試通過！AuthenticationSkill 功能正常")
        print("="*80)
        print("\n📊 測試摘要:")
        print("  ✓ 10 個功能測試全部通過")
        print("  ✓ 核心功能驗證成功")
        print("  ✓ 可以進行下一步集成")
        return 0
    else:
        print("❌ 有測試失敗，請檢查上述錯誤信息")
        print("="*80)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
