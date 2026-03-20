#!/usr/bin/env python3
"""
CommandSkill 驗證測試
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


async def run_tests():
    """運行測試"""
    
    print("\n" + "="*80)
    print("🧪 CommandSkill 驗證測試")
    print("="*80 + "\n")
    
    # 測試 1: 導入 CommandSkill
    print("【測試 1】導入 CommandSkill...")
    try:
        command_skill_path = Path("app/services/skills/command_skill.py")
        if not command_skill_path.exists():
            print(f"❌ 找不到文件: {command_skill_path}")
            return False
        
        exec_globals = {}
        with open(command_skill_path, 'r', encoding='utf-8', errors='ignore') as f:
            exec(f.read(), exec_globals)
        
        CommandSkill = exec_globals['CommandSkill']
        CommandResponse = exec_globals['CommandResponse']
        
        print(f"✅ 導入成功")
        
    except Exception as e:
        print(f"❌ 導入失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 測試 2: 初始化
    print("\n【測試 2】初始化 CommandSkill...")
    try:
        skill = CommandSkill()
        assert skill.name == "命令處理技能"
        assert len(skill.supported_commands) > 0
        print(f"✅ 初始化成功")
        print(f"   - 名稱: {skill.name}")
        print(f"   - 支持命令數: {len(skill.supported_commands)}")
    except Exception as e:
        print(f"❌ 初始化失敗: {e}")
        return False
    
    # 測試 3: 處理 help 命令
    print("\n【測試 3】處理 help 命令...")
    try:
        response = await skill.handle_command(
            command="help",
            user_id="user123",
            user_name="Alice"
        )
        
        assert response.handled == True
        assert response.command_type == "help"
        assert "Databricks Genie" in response.message
        
        print(f"✅ help 命令處理成功")
        print(f"   - 已處理: {response.handled}")
        print(f"   - 命令類型: {response.command_type}")
        print(f"   - 消息長度: {len(response.message)} 字元")
        
    except Exception as e:
        print(f"❌ help 命令處理失敗: {e}")
        return False
    
    # 測試 4: 處理 info 命令
    print("\n【測試 4】處理 info 命令...")
    try:
        response = await skill.handle_command(
            command="/info",
            user_id="user123",
            user_name="Bob",
            conversation_id="conv123"
        )
        
        assert response.handled == True
        assert response.command_type == "info"
        assert "Bob" in response.message
        
        print(f"✅ info 命令處理成功")
        print(f"   - 包含用戶名: ✓")
        print(f"   - 命令類型: {response.command_type}")
        
    except Exception as e:
        print(f"❌ info 命令處理失敗: {e}")
        return False
    
    # 測試 5: 處理 whoami 命令
    print("\n【測試 5】處理 whoami 命令...")
    try:
        response = await skill.handle_command(
            command="whoami",
            user_id="user123",
            user_name="Charlie",
            user_email="charlie@contoso.com",
            conversation_id="conv456"
        )
        
        assert response.handled == True
        assert response.command_type == "whoami"
        assert response.requires_graph_api == True
        assert "Charlie" in response.message
        assert "charlie@contoso.com" in response.message
        
        print(f"✅ whoami 命令處理成功")
        print(f"   - 需要 Graph API: {response.requires_graph_api}")
        print(f"   - 包含卡片數據: {response.card_data is not None}")
        
    except Exception as e:
        print(f"❌ whoami 命令處理失敗: {e}")
        return False
    
    # 測試 6: 處理 logout 命令
    print("\n【測試 6】處理 logout 命令...")
    try:
        response = await skill.handle_command(
            command="/logout",
            user_id="user123",
            user_name="David"
        )
        
        assert response.handled == True
        assert response.command_type == "logout"
        assert "David" in response.message
        
        print(f"✅ logout 命令處理成功")
        print(f"   - 消息: {response.message[:50]}...")
        
    except Exception as e:
        print(f"❌ logout 命令處理失敗: {e}")
        return False
    
    # 測試 7: 處理 reset 命令
    print("\n【測試 7】處理 reset 命令...")
    try:
        response = await skill.handle_command(
            command="reset",
            user_id="user123",
            user_name="Eve"
        )
        
        assert response.handled == True
        assert response.command_type == "reset"
        
        # 測試其他重置命令
        response2 = await skill.handle_command(
            command="new chat",
            user_id="user123"
        )
        assert response2.handled == True
        
        print(f"✅ reset 命令處理成功")
        print(f"   - 'reset' 指令: ✓")
        print(f"   - 'new chat' 指令: ✓")
        
    except Exception as e:
        print(f"❌ reset 命令處理失敗: {e}")
        return False
    
    # 測試 8: 處理 setuser 命令（模擬器模式）
    print("\n【測試 8】處理 setuser 命令...")
    try:
        response = await skill.handle_command(
            command="/setuser alice@test.com Alice Test",
            user_id="user123",
            channel_id="emulator"
        )
        
        assert response.handled == True
        assert response.command_type == "setuser"
        assert response.card_data is not None
        
        print(f"✅ setuser 命令處理成功")
        print(f"   - 卡片數據: {response.card_data}")
        
    except Exception as e:
        print(f"❌ setuser 命令處理失敗: {e}")
        return False
    
    # 測試 9: 檢查命令識別
    print("\n【測試 9】檢查命令識別...")
    try:
        is_cmd1 = await skill.is_command("help")
        is_cmd2 = await skill.is_command("/info")
        is_cmd3 = await skill.is_command("reset")
        is_cmd4 = await skill.is_command("Hello, how are you?")
        
        assert is_cmd1 == True
        assert is_cmd2 == True
        assert is_cmd3 == True
        assert is_cmd4 == False
        
        print(f"✅ 命令識別正確")
        print(f"   - 'help': {is_cmd1}")
        print(f"   - '/info': {is_cmd2}")
        print(f"   - 'reset': {is_cmd3}")
        print(f"   - 普通消息: {is_cmd4}")
        
    except Exception as e:
        print(f"❌ 命令識別失敗: {e}")
        return False
    
    # 測試 10: 獲取可用命令列表
    print("\n【測試 10】獲取可用命令列表...")
    try:
        commands = await skill.get_available_commands()
        assert len(commands) > 0
        
        commands_with_emulator = await skill.get_available_commands(include_emulator=True)
        assert len(commands_with_emulator) > len(commands)
        
        print(f"✅ 命令列表獲取成功")
        print(f"   - 標準命令: {len(commands)} 個")
        print(f"   - 包含模擬器: {len(commands_with_emulator)} 個")
        
    except Exception as e:
        print(f"❌ 命令列表獲取失敗: {e}")
        return False
    
    # 測試 11: 技能描述
    print("\n【測試 11】獲取技能描述...")
    try:
        desc = skill.get_capability_description()
        
        assert desc["name"] == "命令處理技能"
        assert "methods" in desc
        assert "supported_commands" in desc
        
        print(f"✅ 技能描述獲取成功")
        print(f"   - 技能名稱: {desc['name']}")
        print(f"   - 方法數: {len(desc['methods'])}")
        
    except Exception as e:
        print(f"❌ 技能描述獲取失敗: {e}")
        return False
    
    # 測試 12: 非命令文本處理
    print("\n【測試 12】非命令文本處理...")
    try:
        response = await skill.handle_command(
            command="Hello, show me sales data",
            user_id="user123"
        )
        
        assert response.handled == False
        
        print(f"✅ 非命令文本正確識別")
        print(f"   - 已處理: {response.handled}")
        
    except Exception as e:
        print(f"❌ 非命令文本處理失敗: {e}")
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
        print("  ✓ 12 個功能測試全部通過")
        print("  ✓ CommandSkill 核心功能正常")
        print("  ✓ 命令識別正確")
        print("  ✓ 命令處理完整")
        print("  ✓ 錯誤處理健全")
        print("\n✨ CommandSkill 已就緒！")
        print("="*80 + "\n")
        return 0
    else:
        print("❌ 有測試失敗")
        print("="*80 + "\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
