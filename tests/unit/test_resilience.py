"""
測試 retry 和 circuit breaker 機制
"""

import asyncio
import time

import pytest

from app.utils.resilience import (
    CircuitBreaker,
    CircuitBreakerError,
    CircuitState,
    is_transient_error,
    retry_async,
)


# ── is_transient_error ──

class TestIsTransientError:
    def test_timeout_is_transient(self):
        assert is_transient_error(TimeoutError("connection timeout")) is True

    def test_connection_error_is_transient(self):
        assert is_transient_error(ConnectionError("reset")) is True

    def test_http_503_is_transient(self):
        assert is_transient_error(Exception("HTTP 503 Service Unavailable")) is True

    def test_rate_limit_is_transient(self):
        assert is_transient_error(Exception("rate limit exceeded")) is True

    def test_http_429_is_transient(self):
        assert is_transient_error(Exception("status code 429")) is True

    def test_ip_acl_is_permanent(self):
        assert is_transient_error(Exception("IP ACL blocked")) is False

    def test_unauthorized_is_permanent(self):
        assert is_transient_error(Exception("unauthorized access")) is False

    def test_forbidden_is_permanent(self):
        assert is_transient_error(Exception("forbidden")) is False

    def test_not_found_is_permanent(self):
        assert is_transient_error(Exception("not found")) is False

    def test_unknown_error_is_not_transient(self):
        """未知錯誤預設不重試（保守策略）"""
        assert is_transient_error(Exception("some unknown error")) is False


# ── retry_async ──

class TestRetryAsync:
    def test_success_on_first_try(self):
        call_count = 0

        async def succeed():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = asyncio.run(retry_async(succeed, max_retries=3, base_delay=0.01))
        assert result == "ok"
        assert call_count == 1

    def test_success_after_retries(self):
        call_count = 0

        async def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TimeoutError("timeout")
            return "recovered"

        result = asyncio.run(
            retry_async(fail_then_succeed, max_retries=3, base_delay=0.01)
        )
        assert result == "recovered"
        assert call_count == 3

    def test_exhausts_retries(self):
        call_count = 0

        async def always_fail():
            nonlocal call_count
            call_count += 1
            raise TimeoutError("always timeout")

        with pytest.raises(TimeoutError):
            asyncio.run(
                retry_async(always_fail, max_retries=2, base_delay=0.01)
            )
        assert call_count == 3  # 首次 + 2 retries

    def test_permanent_error_not_retried(self):
        call_count = 0

        async def permanent_fail():
            nonlocal call_count
            call_count += 1
            raise Exception("unauthorized access denied")

        with pytest.raises(Exception, match="unauthorized"):
            asyncio.run(
                retry_async(permanent_fail, max_retries=3, base_delay=0.01)
            )
        assert call_count == 1  # 只嘗試一次


# ── CircuitBreaker ──

class TestCircuitBreaker:
    def test_initial_state_is_closed(self):
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60.0, name="test")
        assert cb.state == CircuitState.CLOSED

    def test_stays_closed_on_success(self):
        cb = CircuitBreaker(failure_threshold=3, name="test")

        async def run():
            async def success():
                return "ok"
            result = await cb.call(success)
            assert result == "ok"
            assert cb.state == CircuitState.CLOSED

        asyncio.run(run())

    def test_opens_after_threshold_failures(self):
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=60.0, name="test")

        async def run():
            async def fail():
                raise TimeoutError("timeout")

            for _ in range(3):
                with pytest.raises(TimeoutError):
                    await cb.call(fail)

            assert cb.state == CircuitState.OPEN

            # 後續呼叫應快速失敗
            with pytest.raises(CircuitBreakerError):
                await cb.call(fail)

        asyncio.run(run())

    def test_half_open_after_recovery_timeout(self):
        cb = CircuitBreaker(
            failure_threshold=2, recovery_timeout=0.1, name="test"
        )

        async def run():
            async def fail():
                raise TimeoutError("timeout")

            # 觸發熔斷
            for _ in range(2):
                with pytest.raises(TimeoutError):
                    await cb.call(fail)

            assert cb.state == CircuitState.OPEN

            # 等待冷卻
            await asyncio.sleep(0.15)
            assert cb.state == CircuitState.HALF_OPEN

        asyncio.run(run())

    def test_recovers_from_half_open(self):
        cb = CircuitBreaker(
            failure_threshold=2, recovery_timeout=0.1, name="test"
        )

        async def run():
            async def fail():
                raise TimeoutError("timeout")

            async def succeed():
                return "recovered"

            # 觸發熔斷
            for _ in range(2):
                with pytest.raises(TimeoutError):
                    await cb.call(fail)
            assert cb.state == CircuitState.OPEN

            # 等待冷卻 → HALF_OPEN
            await asyncio.sleep(0.15)

            # 成功的呼叫應恢復為 CLOSED
            result = await cb.call(succeed)
            assert result == "recovered"
            assert cb.state == CircuitState.CLOSED

        asyncio.run(run())

    def test_reset(self):
        cb = CircuitBreaker(failure_threshold=2, name="test")

        async def run():
            async def fail():
                raise TimeoutError("timeout")

            for _ in range(2):
                with pytest.raises(TimeoutError):
                    await cb.call(fail)
            assert cb.state == CircuitState.OPEN

            cb.reset()
            assert cb.state == CircuitState.CLOSED

        asyncio.run(run())

    def test_failure_count_resets_on_success(self):
        cb = CircuitBreaker(failure_threshold=3, name="test")

        async def run():
            async def fail():
                raise TimeoutError("timeout")
            async def succeed():
                return "ok"

            # 2 次失敗（低於閾值）
            for _ in range(2):
                with pytest.raises(TimeoutError):
                    await cb.call(fail)

            # 1 次成功 → 重置計數
            await cb.call(succeed)
            assert cb._failure_count == 0
            assert cb.state == CircuitState.CLOSED

            # 再 2 次失敗不應觸發熔斷
            for _ in range(2):
                with pytest.raises(TimeoutError):
                    await cb.call(fail)
            assert cb.state == CircuitState.CLOSED  # 只有 2/3 次失敗

        asyncio.run(run())


# ── GenieService 整合驗證 ──

def test_genie_service_has_circuit_breaker():
    """GenieService 應有 _circuit_breaker 屬性"""
    from app.services.genie import GenieService
    import inspect
    source = inspect.getsource(GenieService.__init__)
    assert "CircuitBreaker" in source
    assert "_circuit_breaker" in source


def test_genie_service_has_retry_import():
    """genie.py 應 import retry_async 和 CircuitBreaker"""
    import importlib
    genie_mod = importlib.import_module("app.services.genie")
    assert hasattr(genie_mod, "retry_async")
    assert hasattr(genie_mod, "CircuitBreaker")
    assert hasattr(genie_mod, "CircuitBreakerError")


def test_genie_response_exportable():
    """genie.py 應 export GenieResponse 和 _RequestContext"""
    from app.services.genie import GenieResponse, _RequestContext
    assert GenieResponse is not None
    assert _RequestContext is not None


# ── Cache lock 驗證 ──

def test_simple_cache_has_threading_lock():
    """SimpleCache 應有 threading.Lock"""
    from app.utils.cache_utils import SimpleCache
    import threading
    cache = SimpleCache()
    assert type(cache._lock) is type(threading.Lock())


def test_cached_query_has_async_lock():
    """cached_query 模組應有 _query_cache_async_lock"""
    from app.utils.cache_utils import _query_cache_async_lock
    import asyncio
    assert isinstance(_query_cache_async_lock, asyncio.Lock)
