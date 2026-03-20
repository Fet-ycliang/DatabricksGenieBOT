#!/usr/bin/env python3
"""
AuthenticationSkill 獨立驗證 - 不依賴 app.py

直接測試 AuthenticationSkill 模塊功能
"""

import asyncio
import sys
from pathlib import Path

# 直接導入模塊而不使用 app 包
sys.path.insert(0, str(Path(__file__).parent))


async def run_tests():
    """運行基本功能驗證"""
    
    print("\n" + "="*80)
    print("🧪 AuthenticationSkill 驗證 (獨立模式)")
    print("="*80 + "\n")
    
    # 直接導入 AuthenticationSkill 代碼
    print("【步驟 1】導入 AuthenticationSkill...")
    try:
        # 讀取並執行 AuthenticationSkill 代碼
        auth_skill_path = Path("app/services/skills/authentication_skill.py")
        if not auth_skill_path.exists():
            print(f"❌ 找不到文件: {auth_skill_path}")
            return False
        
        # 執行模塊
        exec_globals = {}
        with open(auth_skill_path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
            exec(code, exec_globals)
        
        AuthenticationSkill = exec_globals['AuthenticationSkill']
        print(f"✅ 導入成功")
        
    except Exception as e:
        print(f"❌ 導入失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 測試 1: 初始化
    print("\n【測試 1】初始化 AuthenticationSkill...")
    try:
        skill = AuthenticationSkill()
        print(f"✅ 初始化成功")
        print(f"   - 名稱: {skill.name}")
        print(f"   - 已認證用戶: {len(skill.authenticated_users)}")
    except Exception as e:
        print(f"❌ 初始化失敗: {e}")
        return False
    
    # 測試 2: 認證用戶
    print("\n【測試 2】認證用戶...")
    try:
        result = await skill.authenticate_user("user123", "test_token")
        assert result["status"] == "success"
        assert result["user_id"] == "user123"
        print(f"✅ 認證成功")
        print(f"   - 用戶 ID: {result['user_id']}")
        print(f"   - 消息: {result['message']}")
    except Exception as e:
        print(f"❌ 認證失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 測試 3: 檢查認證狀態
    print("\n【測試 3】檢查認證狀態...")
    try:
        is_auth = await skill.is_user_authenticated("user123")
        assert is_auth is True
        print(f"✅ 狀態檢查成功")
        print(f"   - 用戶已認證: {is_auth}")
    except Exception as e:
        print(f"❌ 狀態檢查失敗: {e}")
        return False
    
    # 測試 4: 獲取認證提示
    print("\n【測試 4】獲取認證提示...")
    try:
        prompt = await skill.get_auth_prompt()
        assert prompt["status"] == "success"
        assert "prompt" in prompt
        print(f"✅ 獲取成功")
        print(f"   - 提示文本: {prompt['prompt']}")
    except Exception as e:
        print(f"❌ 獲取失敗: {e}")
        return False
    
    # 測試 5: 檢查令牌狀態
    print("\n【測試 5】檢查令牌狀態...")
    try:
        expiry = await skill.check_token_expiry("user123")
        assert expiry["status"] == "valid"
        print(f"✅ 令牌檢查成功")
        print(f"   - 狀態: {expiry['status']}")
        print(f"   - 剩餘秒數: {expiry['remaining_seconds']}")
    except Exception as e:
        print(f"❌ 令牌檢查失敗: {e}")
        return False
    
    # 測試 6: 獲取已認證用戶
    print("\n【測試 6】獲取已認證用戶...")
    try:
        users = await skill.get_authenticated_users()
        assert "user123" in users
        print(f"✅ 獲取成功")
        print(f"   - 已認證用戶: {users}")
    except Exception as e:
        print(f"❌ 獲取失敗: {e}")
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
        print(f"   - 用戶已登出")
    except Exception as e:
        print(f"❌ 驗證失敗: {e}")
        return False
    
    # 測試 9: 多用戶場景
    print("\n【測試 9】多用戶認證場景...")
    try:
        skill2 = AuthenticationSkill()
        
        # 認證多個用戶
        for i in range(3):
            user_id = f"user{i+1}@contoso.com"
            await skill2.authenticate_user(user_id, f"token_{i+1}")
        
        users = await skill2.get_authenticated_users()
        assert len(users) == 3
        
        print(f"✅ 多用戶認證成功")
        print(f"   - 認證用戶數: {len(users)}")
        for user in users:
            print(f"     • {user}")
    except Exception as e:
        print(f"❌ 多用戶認證失敗: {e}")
        return False
    
    # 測試 10: 技能描述
    print("\n【測試 10】獲取技能描述...")
    try:
        desc = skill.get_capability_description()
        assert desc["name"] == "認證技能"
        assert "methods" in desc
        
        print(f"✅ 獲取成功")
        print(f"   - 技能名稱: {desc['name']}")
        print(f"   - 方法數: {len(desc['methods'])}")
        print(f"   - 可用方法:")
        for method_name in list(desc['methods'].keys())[:5]:
            print(f"     • {method_name}")
        if len(desc['methods']) > 5:
            print(f"     • ... 還有 {len(desc['methods']) - 5} 個方法")
    except Exception as e:
        print(f"❌ 獲取失敗: {e}")
        return False
    
    return True


async def main():
    """主函數"""
    success = await run_tests()
    
    print("\n" + "="*80)
    if success:
        print("✅ 所有測試通過！")
        print("="*80)
        print("\n📊 測試結果:")
        print("  ✓ 10 個功能測試全部通過")
        print("  ✓ AuthenticationSkill 核心功能正常")
        print("  ✓ 異步操作正常運作")
        print("  ✓ 令牌管理功能正常")
        print("  ✓ 多用戶支持正常")
        print("\n✨ 可以進行下一步框架集成工作！")
        return 0
    else:
        print("❌ 有測試失敗")
        print("="*80)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
