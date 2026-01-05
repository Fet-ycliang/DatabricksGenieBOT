# 快速實施指南：3大核心改善

本文檔提供了立即可實施的代碼，用於修復最關鍵的架構問題。

---

## 🚀 改善 1：會話自動清理 (防止內存洩漏)

### 檔案位置: `app.py`

**添加位置：在 `MyBot` 類中**

```python
import asyncio
from datetime import datetime, timezone, timedelta

class MyBot(ActivityHandler):
    def __init__(self, genie_service: GenieService):
        self.genie_service = genie_service
        self.user_sessions: Dict[str, UserSession] = {}
        self.email_sessions: Dict[str, UserSession] = {}
        self.message_feedback: Dict[str, Dict] = {}
        self.pending_email_input: Dict[str, bool] = {}
        self._cleanup_task = None  # 新增：清理任務
        self._last_metrics_log = datetime.now(timezone.utc)  # 新增：指標日誌時間戳
    
    async def cleanup_stale_sessions(self):
        """
        定期清理過期會話和反饋記錄
        - 清理 > 24 小時未使用的會話
        - 清理 > 24 小時的反饋記錄
        - 每小時運行一次
        """
        logger.info("🧹 會話清理任務已啟動")
        
        while True:
            try:
                await asyncio.sleep(3600)  # 每小時檢查一次
                
                now = datetime.now(timezone.utc)
                expired_users = []
                
                # 檢查過期會話
                for user_id, session in self.user_sessions.items():
                    age = now - session.created_at
                    # 清理 24 小時內未使用的會話
                    idle_time = now - session.last_activity
                    
                    if idle_time > timedelta(hours=24) or age > timedelta(hours=72):
                        expired_users.append((user_id, session))
                
                # 移除過期會話
                for user_id, session in expired_users:
                    self.user_sessions.pop(user_id, None)
                    self.email_sessions.pop(session.email, None)
                    logger.info(
                        f"清理過期會話: {session.get_display_name()} "
                        f"(閒置: {(now - session.last_activity).total_seconds() / 3600:.1f}小時)"
                    )
                
                # 清理舊反饋記錄 (保留 < 24 小時)
                cutoff_time = now - timedelta(hours=24)
                expired_feedback = []
                
                for key, data in self.message_feedback.items():
                    try:
                        timestamp_str = data.get('timestamp', now.isoformat())
                        feedback_time = datetime.fromisoformat(timestamp_str)
                        if feedback_time < cutoff_time:
                            expired_feedback.append(key)
                    except Exception as e:
                        logger.warning(f"無法解析反饋時間戳: {e}")
                        expired_feedback.append(key)
                
                for key in expired_feedback:
                    del self.message_feedback[key]
                
                # 記錄清理統計
                if expired_users or expired_feedback:
                    logger.info(
                        f"✅ 清理完成: "
                        f"{len(expired_users)} 個過期會話, "
                        f"{len(expired_feedback)} 條舊反饋, "
                        f"當前活躍會話: {len(self.user_sessions)}"
                    )
                    
                    # 內存使用估計
                    approx_memory = len(self.user_sessions) * 2  # ~2KB per session
                    logger.info(f"估計內存使用: ~{approx_memory}KB")
            
            except Exception as e:
                logger.error(f"會話清理出錯: {e}", exc_info=True)
    
    async def on_turn(self, turn_context: TurnContext):
        """在每個回合開始時啟動清理任務 (僅執行一次)"""
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self.cleanup_stale_sessions())
            logger.info("✅ 會話清理任務已初始化")
        
        await super().on_turn(turn_context)
```

**驗證：** 檢查日誌中是否看到:
```
✅ 會話清理任務已啟動
✅ 清理完成: X 個過期會話...
```

---

## 🚀 改善 2：結構化日誌和監控 (可觀測性)

### 新建檔案: `monitoring.py`

```python
"""
監控和日誌記錄服務
提供結構化日誌和性能指標
"""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict, field
from enum import Enum
from collections import deque

class LogLevel(Enum):
    """日誌級別"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

@dataclass
class StructuredLog:
    """結構化日誌記錄格式"""
    timestamp: str
    level: str
    component: str
    event: str
    user_id: Optional[str] = None
    duration_ms: Optional[float] = None
    status: Optional[str] = None  # success, error, warning
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    
    def to_json(self) -> str:
        """轉換為 JSON 字符串"""
        return json.dumps(asdict(self))

class PerformanceTracker:
    """性能追踪 (P50, P95, P99)"""
    
    def __init__(self, max_samples: int = 1000):
        self.max_samples = max_samples
        self.samples: deque = deque(maxlen=max_samples)
    
    def record(self, duration_ms: float):
        """記錄一個樣本"""
        self.samples.append(duration_ms)
    
    def get_percentile(self, p: float) -> float:
        """獲取百分位 (0-100)"""
        if not self.samples:
            return 0
        sorted_samples = sorted(self.samples)
        index = int(len(sorted_samples) * (p / 100))
        return sorted_samples[min(index, len(sorted_samples) - 1)]
    
    def get_stats(self) -> Dict[str, float]:
        """獲取統計信息"""
        if not self.samples:
            return {
                'count': 0,
                'avg': 0,
                'p50': 0,
                'p95': 0,
                'p99': 0,
                'min': 0,
                'max': 0
            }
        
        samples = list(self.samples)
        return {
            'count': len(samples),
            'avg': sum(samples) / len(samples),
            'p50': self.get_percentile(50),
            'p95': self.get_percentile(95),
            'p99': self.get_percentile(99),
            'min': min(samples),
            'max': max(samples)
        }

class MonitoringService:
    """集中式監控服務"""
    
    def __init__(self, enable_json_logging: bool = True):
        self.enable_json_logging = enable_json_logging
        self.logger = logging.getLogger("databricks_genie_bot")
        
        # 性能追踪器
        self.genie_query_tracker = PerformanceTracker()
        self.graph_api_tracker = PerformanceTracker()
        self.chart_generation_tracker = PerformanceTracker()
        
        # 計數器
        self.query_counts = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'slow': 0,  # > 3 秒
        }
        self.session_counts = {
            'created': 0,
            'active': 0,
            'cleaned': 0,
        }
        
        # 錯誤追踪
        self.error_log: List[StructuredLog] = []
        self.error_threshold = 10
    
    def log_event(
        self,
        component: str,
        event: str,
        level: LogLevel = LogLevel.INFO,
        user_id: Optional[str] = None,
        duration_ms: Optional[float] = None,
        status: Optional[str] = None,
        error_message: Optional[str] = None,
        details: Optional[Dict] = None
    ) -> None:
        """記錄結構化事件"""
        log = StructuredLog(
            timestamp=datetime.now(timezone.utc).isoformat(),
            level=level.value,
            component=component,
            event=event,
            user_id=user_id,
            duration_ms=duration_ms,
            status=status,
            error_message=error_message,
            details=details
        )
        
        # 輸出日誌
        if self.enable_json_logging:
            self.logger.log(
                getattr(logging, level.value),
                log.to_json()
            )
        else:
            self.logger.log(
                getattr(logging, level.value),
                f"[{component}] {event}: {status or ''} ({duration_ms}ms)"
            )
        
        # 追踪錯誤
        if level == LogLevel.ERROR:
            self.error_log.append(log)
            if len(self.error_log) > self.error_threshold:
                self.error_log.pop(0)
    
    def record_genie_query(
        self,
        duration_ms: float,
        user_id: str,
        success: bool = True
    ) -> None:
        """記錄 Genie 查詢指標"""
        self.genie_query_tracker.record(duration_ms)
        self.query_counts['total'] += 1
        
        if success:
            self.query_counts['success'] += 1
        else:
            self.query_counts['failed'] += 1
        
        # 記錄慢查詢警告 (> 3000ms)
        if duration_ms > 3000:
            self.query_counts['slow'] += 1
            self.log_event(
                component="GenieService",
                event="slow_query_detected",
                level=LogLevel.WARNING,
                user_id=user_id,
                duration_ms=duration_ms,
                details={'threshold_ms': 3000}
            )
    
    def record_graph_api_call(self, duration_ms: float, success: bool = True) -> None:
        """記錄 Graph API 呼叫"""
        self.graph_api_tracker.record(duration_ms)
        if not success:
            self.log_event(
                component="GraphService",
                event="graph_api_error",
                level=LogLevel.WARNING,
                duration_ms=duration_ms
            )
    
    def record_chart_generation(self, duration_ms: float, success: bool = True) -> None:
        """記錄圖表生成"""
        self.chart_generation_tracker.record(duration_ms)
        if not success:
            self.log_event(
                component="ChartGenerator",
                event="chart_generation_failed",
                level=LogLevel.ERROR,
                duration_ms=duration_ms
            )
    
    def get_metrics_summary(self, active_sessions: int = 0) -> Dict[str, Any]:
        """獲取監控指標摘要 (用於 /api/health/detailed)"""
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'queries': {
                'total': self.query_counts['total'],
                'successful': self.query_counts['success'],
                'failed': self.query_counts['failed'],
                'slow': self.query_counts['slow'],
                'success_rate': (
                    self.query_counts['success'] / self.query_counts['total'] * 100
                    if self.query_counts['total'] > 0 else 0
                ),
                'genie_latency': self.genie_query_tracker.get_stats(),
            },
            'sessions': {
                'active': active_sessions,
                'created_total': self.session_counts['created'],
                'cleaned_total': self.session_counts['cleaned'],
            },
            'graph_api': self.graph_api_tracker.get_stats(),
            'charts': self.chart_generation_tracker.get_stats(),
            'recent_errors': [asdict(log) for log in self.error_log[-5:]],
        }
    
    def log_summary_stats(self) -> None:
        """記錄摘要統計信息"""
        stats = self.get_metrics_summary()
        
        self.logger.info(
            "\n" + "="*80 + "\n"
            "📊 系統性能摘要\n"
            "-"*80 + "\n"
            f"  查詢統計:\n"
            f"    總數:       {stats['queries']['total']}\n"
            f"    成功:       {stats['queries']['successful']}\n"
            f"    失敗:       {stats['queries']['failed']}\n"
            f"    成功率:     {stats['queries']['success_rate']:.1f}%\n"
            f"    慢查詢:     {stats['queries']['slow']}\n"
            f"\n  延遲 (Genie API):\n"
            f"    P50:        {stats['queries']['genie_latency']['p50']:.0f}ms\n"
            f"    P95:        {stats['queries']['genie_latency']['p95']:.0f}ms\n"
            f"    P99:        {stats['queries']['genie_latency']['p99']:.0f}ms\n"
            f"    Max:        {stats['queries']['genie_latency']['max']:.0f}ms\n"
            f"\n  會話:\n"
            f"    活躍:       {stats['sessions']['active']}\n"
            f"    已建立:     {stats['sessions']['created_total']}\n"
            + "="*80 + "\n"
        )

# 全域實例
monitoring = MonitoringService(enable_json_logging=True)
```

### 在 `app.py` 中使用

在 `on_message_activity` 方法中添加：

```python
async def on_message_activity(self, turn_context: TurnContext):
    start_time = time.time()
    query_duration = None
    user_session = None
    
    try:
        user_session = await self.get_or_create_user_session(turn_context)
        # ... 現有邏輯 ...
        
        # 在進行 Genie 查詢前
        query_start = time.time()
        answer = await self.genie_service.ask_genie(question, conversation_id)
        query_duration = (time.time() - query_start) * 1000
        
        # 記錄性能指標
        monitoring.record_genie_query(
            duration_ms=query_duration,
            user_id=user_session.user_id,
            success=True
        )
        
        # ... 發送回應 ...
    
    except Exception as e:
        if query_duration is None:
            query_duration = (time.time() - start_time) * 1000
        
        monitoring.record_genie_query(
            duration_ms=query_duration,
            user_id=user_session.user_id if user_session else "unknown",
            success=False
        )
        
        monitoring.log_event(
            component="MessageHandler",
            event="query_error",
            level=LogLevel.ERROR,
            user_id=user_session.user_id if user_session else None,
            duration_ms=query_duration,
            error_message=str(e)
        )
```

### 添加詳細健康檢查端點

在 `health_check.py` 中添加：

```python
@web.get('/api/health/detailed')
async def health_check_detailed(request: web.Request):
    """詳細健康檢查端點"""
    try:
        bot = request.app['BOT']
        
        detailed_metrics = monitoring.get_metrics_summary(
            active_sessions=len(bot.user_sessions)
        )
        
        return web.json_response({
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'metrics': detailed_metrics,
            'uptime_seconds': (datetime.now(timezone.utc) - bot.startup_time).total_seconds(),
        }, status=200)
    
    except Exception as e:
        logger.error(f"詳細健康檢查失敗: {e}")
        return web.json_response({
            'status': 'unhealthy',
            'error': str(e)
        }, status=503)
```

---

## 🚀 改善 3：API 重試邏輯 (可靠性)

### 檔案位置: `genie_service.py`

在文件開始添加：

```python
import asyncio
from typing import TypeVar, Callable, Any

T = TypeVar('T')

async def retry_with_backoff(
    func: Callable[..., Any],
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 32.0
) -> Any:
    """
    使用指數退避的重試邏輯
    
    參數:
        func: 異步函數
        max_retries: 最大重試次數
        initial_delay: 初始延遲秒數
        backoff_factor: 退避倍數 (每次重試延遲翻倍)
        max_delay: 最大延遲秒數
    
    流程:
        1. 嘗試執行函數
        2. 失敗時等待 initial_delay 秒
        3. 第二次重試時等待 initial_delay * 2 秒
        4. 依此類推...
        5. 達到 max_retries 後放棄並拋出異常
    
    範例:
        result = await retry_with_backoff(
            lambda: api.call(),
            max_retries=2
        )
    """
    delay = initial_delay
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return await func()
        
        except Exception as e:
            last_exception = e
            
            if attempt < max_retries:
                # 計算延遲
                delay = min(delay, max_delay)
                
                logger.warning(
                    f"⚠️ API 呼叫失敗 (嘗試 {attempt + 1}/{max_retries + 1}), "
                    f"延遲 {delay:.2f}s 後重試\n"
                    f"   錯誤: {str(e)[:100]}"
                )
                
                await asyncio.sleep(delay)
                delay *= backoff_factor
            else:
                logger.error(
                    f"❌ API 呼叫在 {max_retries} 次重試後失敗: {e}"
                )
    
    raise last_exception

class GenieService:
    # ... 現有代碼 ...
    
    async def ask_genie_with_retry(
        self,
        question: str,
        conversation_id: Optional[str] = None
    ) -> str:
        """
        帶自動重試的 Genie 查詢
        
        自動重試邏輯:
        - 第1次失敗: 等待1秒後重試
        - 第2次失敗: 等待2秒後重試
        - 第3次失敗: 等待4秒後重試
        - 第4次失敗: 放棄並報告錯誤
        """
        
        async def _query():
            return await self.ask_genie(question, conversation_id)
        
        return await retry_with_backoff(
            _query,
            max_retries=3,
            initial_delay=1.0,
            backoff_factor=2.0,
            max_delay=10.0
        )
```

### 在 `app.py` 中使用重試

修改 `on_message_activity` 方法：

```python
# 更改這一行:
# answer = await self.genie_service.ask_genie(question, conversation_id)

# 改為:
answer = await self.genie_service.ask_genie_with_retry(question, conversation_id)
```

---

## 📊 驗證改善成果

### 檢查清單

運行以下命令確認改善已應用：

```bash
# 1. 檢查日誌中的清理信息
tail -f logs/app.log | grep "清理"

# 2. 檢查性能指標
curl http://localhost:8000/api/health/detailed

# 3. 運行負載測試
# (可選) 使用 locust 或類似工具進行負載測試

# 4. 監控內存使用
# 啟動機器人並觀察 24 小時，檢查內存是否穩定
```

### 預期結果

**會話清理:**
```
✅ 清理完成: 5 個過期會話, 23 條舊反饋, 當前活躍會話: 12
估計內存使用: ~24KB
```

**監控日誌:**
```json
{
  "timestamp": "2026-01-05T10:30:45.123456+00:00",
  "queries": {
    "total": 150,
    "successful": 147,
    "failed": 3,
    "success_rate": 98.0,
    "genie_latency": {
      "p50": 1200,
      "p95": 2800,
      "p99": 3500
    }
  }
}
```

**重試邏輯:**
```
⚠️ API 呼叫失敗 (嘗試 1/4), 延遲 1.00s 後重試
   錯誤: Connection timeout
✅ 重試成功: 在第2次嘗試時返回結果
```

---

## 🎯 下一步

1. **部署這3個改善** 到測試環境
2. **監控性能變化** 使用新的監控面板
3. **根據數據優化** (例如: 調整清理間隔)
4. **規劃中優先級改善** (會話持久化、速率限制等)

詳見 [ARCHITECTURE_OPTIMIZATION_GUIDE.md](ARCHITECTURE_OPTIMIZATION_GUIDE.md) 的完整改善路線圖。
