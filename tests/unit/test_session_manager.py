"""
測試 SessionManager 功能
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import asyncio
from datetime import datetime, timedelta, timezone
from app.utils.session_manager import SessionManager
from app.models.user_session import UserSession


def test_session_manager_initialization():
    """測試 SessionManager 初始化"""
    print("Testing SessionManager initialization...")

    user_sessions = {}
    email_sessions = {}

    manager = SessionManager(
        user_sessions=user_sessions,
        email_sessions=email_sessions,
        cleanup_interval=10,
        session_timeout=1
    )

    assert manager.user_sessions is user_sessions
    assert manager.email_sessions is email_sessions
    assert manager.cleanup_interval == 10
    assert manager.session_timeout == 1
    assert manager._is_running == False

    print("  PASS: Initialization successful")


def test_add_and_get_session():
    """測試新增和取得 session"""
    print("Testing add and get session...")

    user_sessions = {}
    email_sessions = {}
    manager = SessionManager(user_sessions, email_sessions)

    # 新增 session
    session = UserSession("user123", "test@example.com", "Test User")
    manager.add_session(session)

    assert "user123" in user_sessions
    assert "test@example.com" in email_sessions

    # 取得 session
    retrieved = manager.get_session("user123")
    assert retrieved is not None
    assert retrieved.user_id == "user123"
    assert retrieved.email == "test@example.com"

    print("  PASS: Add and get session works")


def test_remove_session():
    """測試移除 session"""
    print("Testing remove session...")

    user_sessions = {}
    email_sessions = {}
    manager = SessionManager(user_sessions, email_sessions)

    # 新增 session
    session = UserSession("user123", "test@example.com", "Test User")
    manager.add_session(session)

    # 移除 session
    result = manager.remove_session("user123")

    assert result == True
    assert "user123" not in user_sessions
    assert "test@example.com" not in email_sessions

    # 嘗試移除不存在的 session
    result = manager.remove_session("nonexistent")
    assert result == False

    print("  PASS: Remove session works")


def test_cleanup_expired_sessions():
    """測試清理過期 sessions"""
    print("Testing cleanup expired sessions...")

    user_sessions = {}
    email_sessions = {}

    # 設定 1 小時超時
    manager = SessionManager(
        user_sessions,
        email_sessions,
        session_timeout=1  # 1 hour timeout
    )

    # 新增新 session（不會過期）
    session1 = UserSession("user1", "user1@example.com", "User 1")
    manager.add_session(session1)

    # 新增過期 session（修改 last_activity 為 2 小時前）
    session2 = UserSession("user2", "user2@example.com", "User 2")
    session2.last_activity = datetime.now(timezone.utc) - timedelta(hours=2)
    user_sessions["user2"] = session2
    email_sessions["user2@example.com"] = session2

    # 執行清理
    async def run_cleanup():
        return await manager.cleanup_expired_sessions()

    cleaned_count = asyncio.run(run_cleanup())

    assert cleaned_count == 1, f"Should clean 1 session, but cleaned {cleaned_count}"
    assert "user1" in user_sessions, "Active session should remain"
    assert "user2" not in user_sessions, "Expired session should be removed"
    assert "user1@example.com" in email_sessions
    assert "user2@example.com" not in email_sessions

    print("  PASS: Cleanup expired sessions works")


def test_get_stats():
    """測試取得統計資訊"""
    print("Testing get stats...")

    user_sessions = {}
    email_sessions = {}
    manager = SessionManager(user_sessions, email_sessions)

    # 新增 sessions
    session1 = UserSession("user1", "user1@example.com")
    session2 = UserSession("user2", "user2@example.com")
    manager.add_session(session1)
    manager.add_session(session2)

    stats = manager.get_stats()

    assert stats["user_sessions_count"] == 2
    assert stats["email_sessions_count"] == 2
    assert stats["is_running"] == False
    assert stats["cleanup_interval"] == 3600  # default
    assert stats["session_timeout_hours"] == 4  # default

    print("  PASS: Get stats works")


def test_start_and_stop():
    """測試啟動和停止 SessionManager"""
    print("Testing start and stop...")

    user_sessions = {}
    email_sessions = {}
    manager = SessionManager(
        user_sessions,
        email_sessions,
        cleanup_interval=1,  # 1 second for quick test
        session_timeout=1
    )

    async def test_lifecycle():
        # 啟動
        await manager.start()
        assert manager._is_running == True
        assert manager._cleanup_task is not None

        # 等待一小段時間
        await asyncio.sleep(0.5)

        # 停止
        await manager.stop()
        assert manager._is_running == False

    asyncio.run(test_lifecycle())

    print("  PASS: Start and stop works")


def test_force_cleanup():
    """測試強制清理"""
    print("Testing force cleanup...")

    user_sessions = {}
    email_sessions = {}
    manager = SessionManager(user_sessions, email_sessions, session_timeout=1)

    # 新增過期 session
    session = UserSession("user1", "user1@example.com")
    session.last_activity = datetime.now(timezone.utc) - timedelta(hours=2)
    user_sessions["user1"] = session
    email_sessions["user1@example.com"] = session

    # 強制清理
    async def run_force_cleanup():
        return await manager.force_cleanup()

    cleaned = asyncio.run(run_force_cleanup())

    assert cleaned == 1
    assert len(user_sessions) == 0

    print("  PASS: Force cleanup works")


def test_update_activity_on_get():
    """測試 get_session 時更新活動時間"""
    print("Testing update activity on get...")

    user_sessions = {}
    email_sessions = {}
    manager = SessionManager(user_sessions, email_sessions)

    # 新增 session
    session = UserSession("user1", "user1@example.com")
    old_activity = session.last_activity
    manager.add_session(session)

    # 等待一小段時間
    import time
    time.sleep(0.1)

    # 取得 session（應更新 last_activity）
    retrieved = manager.get_session("user1")

    assert retrieved.last_activity > old_activity

    print("  PASS: Activity update on get works")


def run_all_tests():
    """執行所有測試"""
    print("="*60)
    print("SessionManager Unit Tests")
    print("="*60)
    print()

    tests = [
        test_session_manager_initialization,
        test_add_and_get_session,
        test_remove_session,
        test_cleanup_expired_sessions,
        test_get_stats,
        test_start_and_stop,
        test_force_cleanup,
        test_update_activity_on_get,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print()
    print("="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
