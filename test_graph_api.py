"""
測試 Graph API 整合的簡單腳本

此腳本可用於測試 Graph Service 的基本功能
"""

import asyncio
from graph_service import get_teams_user_info
from botbuilder.schema import Activity, ChannelAccount


async def test_teams_user_info():
    """測試從 Teams channel data 提取使用者資訊"""
    
    # 模擬 Teams 活動資料
    class MockTurnContext:
        def __init__(self):
            self.activity = Activity(
                from_property=ChannelAccount(
                    id="29:1234567890abcdef",
                    name="Test User"
                ),
                channel_data={
                    "teamsUser": {
                        "aadObjectId": "12345678-1234-1234-1234-123456789abc",
                        "email": "test.user@company.com"
                    }
                }
            )
    
    # 建立模擬 context
    mock_context = MockTurnContext()
    
    # 測試取得使用者資訊
    user_info = await get_teams_user_info(mock_context)
    
    print("=== 測試結果 ===")
    print(f"Teams 使用者 ID: {user_info['id']}")
    print(f"使用者名稱: {user_info['name']}")
    print(f"AAD Object ID (OpenID): {user_info['aad_object_id']}")
    print(f"Email: {user_info['email']}")
    
    if user_info['aad_object_id'] and user_info['email']:
        print("\n✅ 測試成功！可以從 Teams 取得基本使用者資訊")
    else:
        print("\n⚠️ 警告：某些資訊可能缺失")


def test_configuration():
    """測試環境設定"""
    from config import DefaultConfig
    
    config = DefaultConfig()
    
    print("=== 環境設定檢查 ===")
    print(f"Graph API 自動登入: {'✅ 啟用' if config.ENABLE_GRAPH_API_AUTO_LOGIN else '❌ 停用'}")
    print(f"OAuth 連線名稱: {config.OAUTH_CONNECTION_NAME or '❌ 未設定'}")
    print(f"Bot App ID: {'✅ 已設定' if config.APP_ID else '❌ 未設定'}")
    print(f"Bot App Password: {'✅ 已設定' if config.APP_PASSWORD else '❌ 未設定'}")
    print(f"Tenant ID: {config.APP_TENANTID or '❌ 未設定'}")
    
    print("\n=== 建議 ===")
    if not config.ENABLE_GRAPH_API_AUTO_LOGIN:
        print("💡 設定 ENABLE_GRAPH_API_AUTO_LOGIN=True 以啟用自動登入")
    
    if not config.OAUTH_CONNECTION_NAME and config.ENABLE_GRAPH_API_AUTO_LOGIN:
        print("⚠️ 警告：已啟用 Graph API 但未設定 OAUTH_CONNECTION_NAME")
        print("   請在環境變數中設定 OAUTH_CONNECTION_NAME")
    
    if config.OAUTH_CONNECTION_NAME and config.ENABLE_GRAPH_API_AUTO_LOGIN:
        print("✅ Graph API 設定看起來正確！")
        print(f"   將使用 OAuth 連線: {config.OAUTH_CONNECTION_NAME}")


if __name__ == "__main__":
    print("=" * 50)
    print("Graph API 整合測試")
    print("=" * 50)
    print()
    
    # 測試環境設定
    test_configuration()
    
    print()
    print("=" * 50)
    
    # 測試 Teams 使用者資訊提取
    asyncio.run(test_teams_user_info())
    
    print()
    print("=" * 50)
    print("測試完成！")
    print()
    print("下一步：")
    print("1. 確認 Azure Portal 中已設定 OAuth Connection")
    print("2. 設定環境變數 ENABLE_GRAPH_API_AUTO_LOGIN=True")
    print("3. 設定環境變數 OAUTH_CONNECTION_NAME=GraphConnection")
    print("4. 部署並在 Teams 中測試")
