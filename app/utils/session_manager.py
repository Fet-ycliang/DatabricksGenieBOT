"""
Session 管理器

自動清理過期的使用者 sessions，防止記憶體洩漏。
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict
from app.models.user_session import UserSession, is_conversation_timed_out

logger = logging.getLogger(__name__)


class SessionManager:
    """
    自動管理和清理使用者 sessions

    負責定期清理過期的 sessions，防止記憶體累積導致 OOM。
    """

    def __init__(
        self,
        user_sessions: Dict[str, UserSession],
        email_sessions: Dict[str, UserSession],
        cleanup_interval: int = 3600,  # 預設每小時清理一次
        session_timeout: int = 4,  # 預設 4 小時超時
    ):
        """
        初始化 SessionManager

        Args:
            user_sessions: 按 user_id 索引的 sessions 字典
            email_sessions: 按 email 索引的 sessions 字典
            cleanup_interval: 清理間隔（秒），預設 3600 秒（1 小時）
            session_timeout: Session 超時時間（小時），預設 4 小時
        """
        self.user_sessions = user_sessions
        self.email_sessions = email_sessions
        self.cleanup_interval = cleanup_interval
        self.session_timeout = session_timeout
        self._cleanup_task: asyncio.Task = None
        self._is_running = False

        # 統計資訊
        self.total_cleanups = 0
        self.total_sessions_cleaned = 0

    async def start(self) -> None:
        """啟動自動清理任務"""
        if self._is_running:
            logger.warning("SessionManager 已經在運行中")
            return

        self._is_running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info(
            f"SessionManager 已啟動 (清理間隔: {self.cleanup_interval}s, "
            f"超時時間: {self.session_timeout}h)"
        )

    async def stop(self) -> None:
        """停止自動清理任務"""
        if not self._is_running:
            return

        self._is_running = False

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        logger.info(
            f"SessionManager 已停止 "
            f"(總清理次數: {self.total_cleanups}, "
            f"總清理 sessions: {self.total_sessions_cleaned})"
        )

    async def _cleanup_loop(self) -> None:
        """清理迴圈：定期檢查並清理過期 sessions"""
        logger.info("Session 清理迴圈已啟動")

        while self._is_running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self.cleanup_expired_sessions()

            except asyncio.CancelledError:
                logger.info("Session 清理迴圈已取消")
                break

            except Exception as e:
                logger.error(f"Session 清理發生錯誤: {e}", exc_info=True)
                # 發生錯誤仍繼續運行，避免因單次錯誤中斷清理

    async def cleanup_expired_sessions(self) -> int:
        """
        清理過期的 sessions

        Returns:
            清理的 session 數量
        """
        now = datetime.now(timezone.utc)
        timeout_delta = timedelta(hours=self.session_timeout)

        expired_user_ids = []
        expired_emails = []

        # 檢查 user_sessions
        for user_id, session in self.user_sessions.items():
            if now - session.last_activity > timeout_delta:
                expired_user_ids.append(user_id)

        # 檢查 email_sessions
        for email, session in self.email_sessions.items():
            if now - session.last_activity > timeout_delta:
                expired_emails.append(email)

        # 清理過期 sessions
        for user_id in expired_user_ids:
            session = self.user_sessions.pop(user_id, None)
            if session:
                logger.info(
                    f"清理過期 session: user_id={user_id}, "
                    f"email={session.email}, "
                    f"閒置時間={now - session.last_activity}"
                )

        for email in expired_emails:
            self.email_sessions.pop(email, None)

        cleaned_count = len(expired_user_ids)

        if cleaned_count > 0:
            self.total_cleanups += 1
            self.total_sessions_cleaned += cleaned_count

            logger.info(
                f"Session 清理完成: 清理了 {cleaned_count} 個過期 sessions "
                f"(剩餘: {len(self.user_sessions)} user sessions, "
                f"{len(self.email_sessions)} email sessions)"
            )
        else:
            logger.debug(
                f"Session 檢查完成: 無過期 sessions "
                f"(當前: {len(self.user_sessions)} user sessions, "
                f"{len(self.email_sessions)} email sessions)"
            )

        return cleaned_count

    def get_stats(self) -> dict:
        """
        取得統計資訊

        Returns:
            統計資訊字典
        """
        return {
            "is_running": self._is_running,
            "user_sessions_count": len(self.user_sessions),
            "email_sessions_count": len(self.email_sessions),
            "cleanup_interval": self.cleanup_interval,
            "session_timeout_hours": self.session_timeout,
            "total_cleanups": self.total_cleanups,
            "total_sessions_cleaned": self.total_sessions_cleaned,
        }

    async def force_cleanup(self) -> int:
        """
        強制立即執行清理

        Returns:
            清理的 session 數量
        """
        logger.info("強制執行 session 清理")
        return await self.cleanup_expired_sessions()

    def get_session(self, user_id: str) -> UserSession:
        """
        取得 session 並更新活動時間

        Args:
            user_id: 使用者 ID

        Returns:
            UserSession 或 None
        """
        session = self.user_sessions.get(user_id)
        if session:
            session.update_activity()
        return session

    def add_session(self, session: UserSession) -> None:
        """
        新增 session

        Args:
            session: UserSession 物件
        """
        self.user_sessions[session.user_id] = session
        self.email_sessions[session.email] = session
        logger.info(
            f"新增 session: user_id={session.user_id}, email={session.email}"
        )

    def remove_session(self, user_id: str) -> bool:
        """
        移除指定的 session

        Args:
            user_id: 使用者 ID

        Returns:
            是否成功移除
        """
        session = self.user_sessions.pop(user_id, None)
        if session:
            self.email_sessions.pop(session.email, None)
            logger.info(
                f"移除 session: user_id={user_id}, email={session.email}"
            )
            return True
        return False
