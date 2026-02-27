"""
彈性工具：Retry 與 Circuit Breaker

提供指數退避重試和 circuit breaker 機制，
用於保護對 Databricks Genie API 的呼叫。
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Any, Callable, Set, Type

logger = logging.getLogger(__name__)


# ── 暫時性錯誤判斷 ──

# 已知永久性錯誤關鍵字（不應 retry）
_PERMANENT_ERROR_KEYWORDS = frozenset([
    "ip acl",
    "unauthorized",
    "forbidden",
    "not found",
    "invalid space",
    "permission denied",
])


def is_transient_error(exc: Exception) -> bool:
    """判斷例外是否為暫時性錯誤（值得 retry）"""
    error_str = str(exc).lower()

    # 永久性錯誤 → 不 retry
    for keyword in _PERMANENT_ERROR_KEYWORDS:
        if keyword in error_str:
            return False

    # 已知暫時性錯誤類型
    transient_types = (
        TimeoutError,
        ConnectionError,
        ConnectionResetError,
        ConnectionAbortedError,
    )
    if isinstance(exc, transient_types):
        return True

    # HTTP 狀態碼型別的暫時性錯誤
    for keyword in ("timeout", "429", "500", "502", "503", "504", "rate limit",
                    "temporarily unavailable", "connection reset", "server error"):
        if keyword in error_str:
            return True

    return False


# ── Retry with Exponential Backoff ──

async def retry_async(
    func: Callable[..., Any],
    *args,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    backoff_factor: float = 2.0,
    retryable_check: Callable[[Exception], bool] = is_transient_error,
    operation_name: str = "operation",
    **kwargs,
) -> Any:
    """
    帶指數退避的非同步重試。

    Args:
        func: 要執行的 async 或 sync 函式（如果是 sync，會透過 executor 執行）
        *args: 傳給 func 的位置參數
        max_retries: 最大重試次數（不含首次嘗試）
        base_delay: 初始等待秒數
        max_delay: 最大等待秒數
        backoff_factor: 退避倍數
        retryable_check: 判斷例外是否可重試的函式
        operation_name: 用於日誌的操作名稱
        **kwargs: 傳給 func 的關鍵字參數

    Returns:
        func 的回傳值

    Raises:
        最後一次重試失敗的例外
    """
    last_exc = None

    for attempt in range(max_retries + 1):
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            if attempt > 0:
                logger.info(f"[retry] {operation_name} 第 {attempt + 1} 次嘗試成功")
            return result
        except Exception as exc:
            last_exc = exc

            if attempt >= max_retries:
                logger.error(
                    f"[retry] {operation_name} 已用盡 {max_retries} 次重試，最終失敗: {exc}"
                )
                raise

            if not retryable_check(exc):
                logger.warning(
                    f"[retry] {operation_name} 發生永久性錯誤，不重試: {type(exc).__name__}: {str(exc)[:200]}"
                )
                raise

            delay = min(base_delay * (backoff_factor ** attempt), max_delay)
            logger.warning(
                f"[retry] {operation_name} 第 {attempt + 1}/{max_retries + 1} 次失敗 "
                f"({type(exc).__name__}), {delay:.1f}s 後重試..."
            )
            await asyncio.sleep(delay)

    raise last_exc  # type: ignore[misc]


# ── Circuit Breaker ──

class CircuitState(Enum):
    CLOSED = "CLOSED"        # 正常：請求通過
    OPEN = "OPEN"            # 熔斷：快速失敗
    HALF_OPEN = "HALF_OPEN"  # 探測：允許單一請求嘗試恢復


class CircuitBreakerError(Exception):
    """Circuit breaker 處於 OPEN 狀態時拋出"""
    pass


class CircuitBreaker:
    """
    Circuit Breaker 實作。

    當失敗次數達到閾值時開啟熔斷器，在冷卻期內所有呼叫快速失敗。
    冷卻期後進入半開狀態，允許單一請求嘗試恢復。

    Args:
        failure_threshold: 連續失敗多少次後熔斷
        recovery_timeout: 熔斷後多少秒進入半開狀態
        name: 用於日誌的 breaker 名稱
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        name: str = "default",
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.name = name

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: float = 0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        """取得目前狀態（含自動轉換 OPEN → HALF_OPEN）"""
        if self._state == CircuitState.OPEN:
            if time.monotonic() - self._last_failure_time >= self.recovery_timeout:
                return CircuitState.HALF_OPEN
        return self._state

    async def call(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """
        透過 circuit breaker 執行呼叫。

        Args:
            func: 要執行的 async callable
            *args, **kwargs: 傳給 func 的參數

        Returns:
            func 的回傳值

        Raises:
            CircuitBreakerError: 如果 breaker 處於 OPEN 狀態
        """
        async with self._lock:
            current_state = self.state

            if current_state == CircuitState.OPEN:
                logger.warning(
                    f"[circuit-breaker:{self.name}] OPEN — 快速失敗 "
                    f"(連續失敗 {self._failure_count} 次, "
                    f"冷卻剩餘 {self.recovery_timeout - (time.monotonic() - self._last_failure_time):.0f}s)"
                )
                raise CircuitBreakerError(
                    f"Circuit breaker '{self.name}' is OPEN "
                    f"(failures={self._failure_count}, "
                    f"recovery in {self.recovery_timeout - (time.monotonic() - self._last_failure_time):.0f}s)"
                )

            if current_state == CircuitState.HALF_OPEN:
                logger.info(f"[circuit-breaker:{self.name}] HALF_OPEN — 嘗試恢復")

        # 釋放鎖後執行實際呼叫（不阻塞其他 half-open 探測以外的邏輯）
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as exc:
            await self._on_failure()
            raise

    async def _on_success(self):
        """呼叫成功：重置失敗計數"""
        async with self._lock:
            if self._state != CircuitState.CLOSED or self._failure_count > 0:
                logger.info(
                    f"[circuit-breaker:{self.name}] 呼叫成功，"
                    f"從 {self._state.value} 恢復為 CLOSED"
                )
            self._failure_count = 0
            self._state = CircuitState.CLOSED

    async def _on_failure(self):
        """呼叫失敗：累加失敗計數，可能觸發熔斷"""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()

            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.error(
                    f"[circuit-breaker:{self.name}] 連續失敗 {self._failure_count} 次 "
                    f"(>= {self.failure_threshold})，切換為 OPEN，"
                    f"冷卻 {self.recovery_timeout}s"
                )
            else:
                logger.warning(
                    f"[circuit-breaker:{self.name}] 失敗 "
                    f"{self._failure_count}/{self.failure_threshold}"
                )

    def reset(self):
        """手動重置 breaker（用於測試或管理介面）"""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0
        logger.info(f"[circuit-breaker:{self.name}] 已手動重置")
