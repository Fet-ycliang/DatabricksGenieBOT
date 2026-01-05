# 新增 performance_metrics.py
from collections import deque
import statistics
from datetime import datetime, timedelta

class PerformanceMetrics:
    def __init__(self):
        self.query_times = deque(maxlen=1000)
        self.error_rates = deque(maxlen=100)
    
    def record_query(self, duration, success=True):
        self.query_times.append(duration)
        if not success:
            self.error_rates.append(duration)
        
        # 計算統計
        if len(self.query_times) > 10:
            p50 = statistics.median(self.query_times)
            p95 = sorted(self.query_times)[-int(len(self.query_times)*0.95)]
            error_rate = len(self.error_rates) / len(self.query_times)
            
            logger.info(
                f"📊 P50: {p50:.2f}s, P95: {p95:.2f}s, "
                f"錯誤率: {error_rate:.1%}"
            )
    
    def get_summary(self):
        return {
            'avg_time': statistics.mean(self.query_times),
            'p95_time': sorted(self.query_times)[-int(len(self.query_times)*0.95)],
            'error_rate': len(self.error_rates) / len(self.query_times)
        }

# 全域實例
metrics = PerformanceMetrics()
