#!/usr/bin/env python3
"""
IdentitySkill 驗證測試
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


async def run_tests():
    """運行測試"""
    
    print("\n" + "="*80)
    print("🧪 IdentitySkill 驗證測試")
    print("="*80 + "\n")
    
    # 測試 1: 導入 IdentitySkill
    print("【測試 1】導入 IdentitySkill...")
    try:
        identity_skill_path = Path("app/services/skills/identity_skill.py")
        if not identity_skill_path.exists():
            print(f"❌ 找不到文件: {identity_skill_path}")
            return False
        
        exec_globals = {}
        with open(identity_skill_path, 'r', encoding='utf-8', errors='ignore') as f:
            exec(f.read(), exec_globals)
        
        IdentitySkill = exec_globals['IdentitySkill']
        IdentityResponse = exec_globals['IdentityResponse']
        
        print(f"✅ 導入成功")
        
    except Exception as e:
        print(f"❌ 導入失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 測試 2: 初始化
    print("\n【測試 2】初始化 IdentitySkill...")
    try:
        skill = IdentitySkill()
        assert skill.name == "身份管理技能"
        assert len(skill.pending_email_inputs) == 0
        print(f"✅ 初始化成功")
        print(f"   - 名稱: {skill.name}")
    except Exception as e:
        print(f"❌ 初始化失敗: {e}")
        return False
    
    # 測試 3: 電子郵件格式驗證
    print("\n【測試 3】電子郵件格式驗證...")
    try:
        valid_emails = [
            "test@example.com",
            "user.name@company.co.uk",
            "alice+tag@contoso.com"
        ]
        
        invalid_emails = [
            "not-an-email",
            "@example.com",
            "user@",
            "user name@example.com"
        ]
        
        for email in valid_emails:
            assert await skill.validate_email(email) == True
        
        for email in invalid_emails:
            assert await skill.validate_email(email) == False
        
        print(f"✅ 電子郵件驗證正確")
        print(f"   - 有效郵件: {len(valid_emails)} 個通過")
        print(f"   - 無效郵件: {len(invalid_emails)} 個被拒")
        
    except Exception as e:
        print(f"❌ 電子郵件驗證失敗: {e}")
        return False
    
    # 測試 4: 未識別用戶的歡迎消息
    print("\n【測試 4】未識別用戶的歡迎消息...")
    try:
        response = await skill.handle_user_identification(
            user_id="new_user",
            message="Hello"
        )
        
        assert response.handled == True
        assert "電子郵件" in response.message
        assert response.requires_email_input == True
        
        print(f"✅ 歡迎消息生成成功")
        print(f"   - 已處理: {response.handled}")
        print(f"   - 需要電子郵件: {response.requires_email_input}")
        
    except Exception as e:
        print(f"❌ 歡迎消息生成失敗: {e}")
        return False
    
    # 測試 5: 請求電子郵件輸入
    print("\n【測試 5】請求電子郵件輸入...")
    try:
        response = await skill.handle_user_identification(
            user_id="user123",
            message="email"
        )
        
        assert response.handled == True
        assert response.requires_email_input == True
        assert await skill.is_user_pending_email("user123") == True
        
        print(f"✅ 電子郵件輸入請求成功")
        print(f"   - 用戶待處理狀態: ✓")
        
    except Exception as e:
        print(f"❌ 電子郵件輸入請求失敗: {e}")
        return False
    
    # 測試 6: 處理有效的電子郵件輸入
    print("\n【測試 6】處理有效的電子郵件輸入...")
    try:
        # 用戶現在處於待處理狀態，輸入電子郵件
        response = await skill.handle_user_identification(
            user_id="user123",
            message="alice@contoso.com"
        )
        
        assert response.handled == True
        assert response.email_validated == True
        assert response.user_email == "alice@contoso.com"
        assert await skill.is_user_pending_email("user123") == False
        
        # 驗證已保存
        validated_email = await skill.get_validated_email("user123")
        assert validated_email == "alice@contoso.com"
        
        print(f"✅ 電子郵件輸入處理成功")
        print(f"   - 驗證通過: ✓")
        print(f"   - 電子郵件: {response.user_email}")
        print(f"   - 待處理狀態清除: ✓")
        
    except Exception as e:
        print(f"❌ 電子郵件輸入處理失敗: {e}")
        return False
    
    # 測試 7: 處理無效的電子郵件輸入
    print("\n【測試 7】處理無效的電子郵件輸入...")
    try:
        # 設置新用戶為待處理狀態
        await skill.handle_user_identification("user456", "email")
        
        # 輸入無效電子郵件
        response = await skill.handle_user_identification(
            user_id="user456",
            message="not-an-email"
        )
        
        assert response.handled == True
        assert response.email_validated == False
        assert "無效" in response.message
        # 用戶仍處於待處理狀態
        assert await skill.is_user_pending_email("user456") == True
        
        print(f"✅ 無效電子郵件正確處理")
        print(f"   - 驗證失敗: ✓")
        print(f"   - 錯誤消息: ✓")
        
    except Exception as e:
        print(f"❌ 無效電子郵件處理失敗: {e}")
        return False
    
    # 測試 8: 取消電子郵件輸入
    print("\n【測試 8】取消電子郵件輸入...")
    try:
        # 用戶輸入 cancel
        response = await skill.handle_user_identification(
            user_id="user456",
            message="cancel"
        )
        
        assert response.handled == True
        assert response.cancelled == True
        assert await skill.is_user_pending_email("user456") == False
        
        print(f"✅ 取消操作成功")
        print(f"   - 已取消: {response.cancelled}")
        print(f"   - 待處理狀態清除: ✓")
        
    except Exception as e:
        print(f"❌ 取消操作失敗: {e}")
        return False
    
    # 測試 9: 處理 help 命令
    print("\n【測試 9】處理 help 命令...")
    try:
        response = await skill.handle_user_identification(
            user_id="user789",
            message="help"
        )
        
        assert response.handled == True
        assert "Databricks Genie" in response.message
        
        print(f"✅ help 命令處理成功")
        print(f"   - 消息長度: {len(response.message)} 字元")
        
    except Exception as e:
        print(f"❌ help 命令處理失敗: {e}")
        return False
    
    # 測試 10: 處理 info 命令
    print("\n【測試 10】處理 info 命令...")
    try:
        response = await skill.handle_user_identification(
            user_id="user789",
            message="/info"
        )
        
        assert response.handled == True
        assert "歡迎使用 Genie 機器人" in response.message
        
        print(f"✅ info 命令處理成功")
        
    except Exception as e:
        print(f"❌ info 命令處理失敗: {e}")
        return False
    
    # 測試 11: 清除用戶身份
    print("\n【測試 11】清除用戶身份...")
    try:
        # 確認 user123 有已驗證的電子郵件
        email_before = await skill.get_validated_email("user123")
        assert email_before == "alice@contoso.com"
        
        # 清除身份
        await skill.clear_user_identity("user123")
        
        # 驗證已清除
        email_after = await skill.get_validated_email("user123")
        assert email_after is None
        
        print(f"✅ 身份清除成功")
        print(f"   - 清除前: {email_before}")
        print(f"   - 清除後: {email_after}")
        
    except Exception as e:
        print(f"❌ 身份清除失敗: {e}")
        return False
    
    # 測試 12: 技能描述
    print("\n【測試 12】獲取技能描述...")
    try:
        desc = skill.get_capability_description()
        
        assert desc["name"] == "身份管理技能"
        assert "methods" in desc
        assert "features" in desc
        
        print(f"✅ 技能描述獲取成功")
        print(f"   - 技能名稱: {desc['name']}")
        print(f"   - 方法數: {len(desc['methods'])}")
        print(f"   - 功能數: {len(desc['features'])}")
        
    except Exception as e:
        print(f"❌ 技能描述獲取失敗: {e}")
        return False
    
    # 測試 13: 多用戶並發處理
    print("\n【測試 13】多用戶並發處理...")
    try:
        users = ["user_a", "user_b", "user_c"]
        
        # 所有用戶請求輸入電子郵件
        for user_id in users:
            await skill.handle_user_identification(user_id, "email")
        
        # 驗證所有用戶都在待處理狀態
        for user_id in users:
            assert await skill.is_user_pending_email(user_id) == True
        
        # 用戶輸入電子郵件
        emails = {
            "user_a": "alice@test.com",
            "user_b": "bob@test.com",
            "user_c": "charlie@test.com"
        }
        
        for user_id, email in emails.items():
            response = await skill.handle_user_identification(user_id, email)
            assert response.email_validated == True
        
        # 驗證所有電子郵件已保存
        for user_id, expected_email in emails.items():
            actual_email = await skill.get_validated_email(user_id)
            assert actual_email == expected_email
        
        print(f"✅ 多用戶並發處理成功")
        print(f"   - 處理用戶數: {len(users)}")
        print(f"   - 驗證電子郵件: {len(emails)} 個")
        
    except Exception as e:
        print(f"❌ 多用戶並發處理失敗: {e}")
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
        print("  ✓ 13 個功能測試全部通過")
        print("  ✓ IdentitySkill 核心功能正常")
        print("  ✓ 電子郵件驗證正確")
        print("  ✓ 身份流程管理完整")
        print("  ✓ 多用戶支持正常")
        print("  ✓ 錯誤處理健全")
        print("\n✨ IdentitySkill 已就緒！")
        print("="*80 + "\n")
        return 0
    else:
        print("❌ 有測試失敗")
        print("="*80 + "\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
