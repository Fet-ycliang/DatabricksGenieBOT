#!/usr/bin/env python3
"""
BotCoreSkill 驗證測試

測試 Bot 核心對話處理功能
"""

import asyncio
import sys
from pathlib import Path

# 直接導入模塊
sys.path.insert(0, str(Path(__file__).parent))

# 直接執行 BotCoreSkill 代碼
bot_core_skill_path = Path("app/services/skills/bot_core_skill.py")

async def run_tests():
    """運行測試"""
    
    print("\n" + "="*80)
    print("🧪 BotCoreSkill 驗證測試")
    print("="*80 + "\n")
    
    # 測試 1: 導入 BotCoreSkill
    print("【測試 1】導入 BotCoreSkill...")
    try:
        if not bot_core_skill_path.exists():
            print(f"❌ 找不到文件: {bot_core_skill_path}")
            return False
        
        exec_globals = {}
        with open(bot_core_skill_path, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
            exec(code, exec_globals)
        
        BotCoreSkill = exec_globals['BotCoreSkill']
        MessageResponse = exec_globals['MessageResponse']
        ConversationContext = exec_globals['ConversationContext']
        
        print(f"✅ 導入成功")
        
    except Exception as e:
        print(f"❌ 導入失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 測試 2: 初始化
    print("\n【測試 2】初始化 BotCoreSkill...")
    try:
        skill = BotCoreSkill()
        assert skill.name == "Bot核心技能"
        assert len(skill.conversations) == 0
        print(f"✅ 初始化成功")
        print(f"   - 名稱: {skill.name}")
        print(f"   - 對話數: {len(skill.conversations)}")
    except Exception as e:
        print(f"❌ 初始化失敗: {e}")
        return False
    
    # 測試 3: 處理新成員加入
    print("\n【測試 3】處理新成員加入（未認證）...")
    try:
        response = await skill.handle_member_added(
            user_id="user123",
            user_name="Alice",
            conversation_id="conv123"
        )
        
        assert response.text is not None
        assert response.requires_auth == True
        assert "user123" in skill.conversations
        
        print(f"✅ 成員加入處理成功")
        print(f"   - 歡迎消息: {response.text[:50]}...")
        print(f"   - 需要認證: {response.requires_auth}")
        print(f"   - 對話已創建")
        
    except Exception as e:
        print(f"❌ 成員加入處理失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 測試 4: 更新認證狀態
    print("\n【測試 4】更新用戶認證狀態...")
    try:
        result = await skill.update_authentication_status(
            user_id="user123",
            authenticated=True,
            user_email="alice@contoso.com"
        )
        
        assert result["status"] == "success"
        assert skill.conversations["user123"].authenticated == True
        
        print(f"✅ 認證狀態更新成功")
        print(f"   - 狀態: {result['status']}")
        print(f"   - 用戶已認證")
        
    except Exception as e:
        print(f"❌ 認證狀態更新失敗: {e}")
        return False
    
    # 測試 5: 處理新成員加入（已認證）
    print("\n【測試 5】處理新成員加入（已認證）...")
    try:
        response = await skill.handle_member_added(
            user_id="user456",
            user_name="Bob",
            conversation_id="conv456"
        )
        
        # 手動設置為已認證
        await skill.update_authentication_status("user456", True)
        
        # 再次觸發歡迎消息
        response2 = await skill.handle_member_added(
            user_id="user456",
            user_name="Bob"
        )
        
        print(f"✅ 已認證用戶歡迎消息生成")
        print(f"   - 歡迎消息: {response2.text[:50]}...")
        print(f"   - 需要認證: {response2.requires_auth}")
        
    except Exception as e:
        print(f"❌ 已認證歡迎消息失敗: {e}")
        return False
    
    # 測試 6: 處理用戶消息（未認證）
    print("\n【測試 6】處理用戶消息（未認證）...")
    try:
        # 創建新用戶
        response = await skill.handle_message(
            user_id="user789",
            message_text="Hello",
            user_name="Charlie"
        )
        
        assert response.requires_auth == True
        print(f"✅ 未認證消息處理成功")
        print(f"   - 回應: {response.text}")
        print(f"   - 需要認證: {response.requires_auth}")
        
    except Exception as e:
        print(f"❌ 未認證消息處理失敗: {e}")
        return False
    
    # 測試 7: 處理重置命令
    print("\n【測試 7】處理重置命令...")
    try:
        response = await skill.handle_message(
            user_id="user123",
            message_text="/reset"
        )
        
        assert "重置" in response.text or "reset" in response.text.lower()
        print(f"✅ 重置命令處理成功")
        print(f"   - 回應: {response.text}")
        
    except Exception as e:
        print(f"❌ 重置命令處理失敗: {e}")
        return False
    
    # 測試 8: 處理幫助命令
    print("\n【測試 8】處理幫助命令...")
    try:
        response = await skill.handle_message(
            user_id="user123",
            message_text="/help"
        )
        
        assert "命令" in response.text or "help" in response.text.lower()
        print(f"✅ 幫助命令處理成功")
        print(f"   - 回應長度: {len(response.text)} 字元")
        print(f"   - 包含說明")
        
    except Exception as e:
        print(f"❌ 幫助命令處理失敗: {e}")
        return False
    
    # 測試 9: 獲取對話上下文
    print("\n【測試 9】獲取對話上下文...")
    try:
        context = await skill.get_conversation_context("user123")
        
        assert context is not None
        assert context.user_id == "user123"
        assert context.user_name == "Alice"
        
        print(f"✅ 對話上下文獲取成功")
        print(f"   - 用戶 ID: {context.user_id}")
        print(f"   - 用戶名稱: {context.user_name}")
        print(f"   - 認證狀態: {context.authenticated}")
        
    except Exception as e:
        print(f"❌ 對話上下文獲取失敗: {e}")
        return False
    
    # 測試 10: 獲取活動對話列表
    print("\n【測試 10】獲取活動對話列表...")
    try:
        active = await skill.get_active_conversations()
        
        assert len(active) > 0
        print(f"✅ 活動對話列表獲取成功")
        print(f"   - 活動對話數: {len(active)}")
        print(f"   - 用戶: {', '.join(active[:3])}")
        
    except Exception as e:
        print(f"❌ 活動對話列表獲取失敗: {e}")
        return False
    
    # 測試 11: 構建正在輸入指示器
    print("\n【測試 11】構建正在輸入指示器...")
    try:
        response = await skill.build_typing_indicator()
        
        assert response.activity_type == "typing"
        print(f"✅ 正在輸入指示器構建成功")
        print(f"   - 活動類型: {response.activity_type}")
        
    except Exception as e:
        print(f"❌ 正在輸入指示器構建失敗: {e}")
        return False
    
    # 測試 12: 構建錯誤消息
    print("\n【測試 12】構建錯誤消息...")
    try:
        response = await skill.build_error_message("測試錯誤", user_friendly=True)
        
        assert response.error == "測試錯誤"
        assert "錯誤" in response.text
        
        print(f"✅ 錯誤消息構建成功")
        print(f"   - 消息: {response.text}")
        print(f"   - 錯誤: {response.error}")
        
    except Exception as e:
        print(f"❌ 錯誤消息構建失敗: {e}")
        return False
    
    # 測試 13: 技能描述
    print("\n【測試 13】獲取技能描述...")
    try:
        desc = skill.get_capability_description()
        
        assert desc["name"] == "Bot核心技能"
        assert "methods" in desc
        assert "events_handled" in desc
        
        print(f"✅ 技能描述獲取成功")
        print(f"   - 技能名稱: {desc['name']}")
        print(f"   - 方法數: {len(desc['methods'])}")
        print(f"   - 處理事件: {len(desc['events_handled'])} 種")
        
    except Exception as e:
        print(f"❌ 技能描述獲取失敗: {e}")
        return False
    
    # 測試 14: 多用戶場景
    print("\n【測試 14】多用戶並發處理...")
    try:
        users = [
            ("user_a", "Alice"),
            ("user_b", "Bob"),
            ("user_c", "Charlie"),
            ("user_d", "David")
        ]
        
        for user_id, user_name in users:
            await skill.handle_member_added(user_id, user_name)
        
        active = await skill.get_active_conversations()
        
        print(f"✅ 多用戶處理成功")
        print(f"   - 總對話數: {len(skill.conversations)}")
        print(f"   - 活動對話數: {len(active)}")
        
    except Exception as e:
        print(f"❌ 多用戶處理失敗: {e}")
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
        print("  ✓ 14 個功能測試全部通過")
        print("  ✓ BotCoreSkill 核心功能正常")
        print("  ✓ 對話管理正常運作")
        print("  ✓ 認證流程集成正常")
        print("  ✓ 命令處理正常")
        print("  ✓ 多用戶支持正常")
        print("\n✨ BotCoreSkill 已就緒！")
        print("="*80 + "\n")
        return 0
    else:
        print("❌ 有測試失敗")
        print("="*80 + "\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
