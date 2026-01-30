"""效能優化基準測試工具"""

import asyncio
import time
import statistics
import json
from typing import Dict, List
from datetime import datetime


class PerformanceBenchmark:
    """效能基準測試工具"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {}
        }
    
    async def benchmark_logging(self, iterations: int = 1000) -> Dict:
        """基準測試：日誌性能"""
        import logging
        from io import StringIO
        
        # 設置日誌
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        logger = logging.getLogger('test_logger')
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        # 測試 - 頻繁日誌
        durations = []
        for i in range(iterations):
            start = time.time()
            logger.info(f"Test message {i} with some data {{'key': 'value', 'number': {i}}}")
            durations.append(time.time() - start)
        
        result = {
            'test': 'logging_performance',
            'iterations': iterations,
            'metrics': {
                'mean_ms': statistics.mean(durations) * 1000,
                'median_ms': statistics.median(durations) * 1000,
                'p95_ms': sorted(durations)[int(iterations * 0.95)] * 1000,
                'p99_ms': sorted(durations)[int(iterations * 0.99)] * 1000,
            }
        }
        
        return result
    
    async def benchmark_json_serialization(self, iterations: int = 1000) -> Dict:
        """基準測試：JSON 序列化"""
        import json
        
        test_data = {
            'user_id': '12345',
            'message': 'This is a test message with some content',
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'tags': ['tag1', 'tag2', 'tag3'],
                'nested': {
                    'level1': {
                        'level2': {
                            'level3': 'deep value'
                        }
                    }
                }
            },
            'large_data': [{'item': i, 'value': f'item_{i}'} for i in range(100)]
        }
        
        # 測試 - 重複序列化
        durations = []
        for _ in range(iterations):
            start = time.time()
            json.dumps(test_data, indent=2)
            durations.append(time.time() - start)
        
        result = {
            'test': 'json_serialization',
            'iterations': iterations,
            'data_size_kb': len(json.dumps(test_data)) / 1024,
            'metrics': {
                'mean_us': statistics.mean(durations) * 1_000_000,
                'median_us': statistics.median(durations) * 1_000_000,
                'p95_us': sorted(durations)[int(iterations * 0.95)] * 1_000_000,
                'p99_us': sorted(durations)[int(iterations * 0.99)] * 1_000_000,
            }
        }
        
        return result
    
    async def benchmark_memory_operations(self, size: int = 10000) -> Dict:
        """基準測試：內存操作"""
        import sys
        
        # 測試 - 字典操作
        test_dict = {}
        start = time.time()
        for i in range(size):
            test_dict[f'key_{i}'] = {
                'value': i,
                'data': f'x' * 100
            }
        dict_insert_time = time.time() - start
        
        # 測試 - 查詢性能
        start = time.time()
        for i in range(size):
            _ = test_dict.get(f'key_{i}', None)
        dict_lookup_time = time.time() - start
        
        result = {
            'test': 'memory_operations',
            'size': size,
            'metrics': {
                'dict_insert_ms': dict_insert_time * 1000,
                'dict_lookup_ms': dict_lookup_time * 1000,
                'memory_kb': sys.getsizeof(test_dict) / 1024,
            }
        }
        
        return result
    
    async def benchmark_string_operations(self, iterations: int = 10000) -> Dict:
        """基準測試：字符串操作"""
        
        # 測試 - 字符串連接（低效方式）
        start = time.time()
        result = ""
        for i in range(iterations):
            result += f"Line {i}: Some text content\n"
        concat_time = time.time() - start
        
        # 測試 - 字符串連接（高效方式）
        start = time.time()
        lines = [f"Line {i}: Some text content" for i in range(iterations)]
        result = "\n".join(lines)
        join_time = time.time() - start
        
        result_data = {
            'test': 'string_operations',
            'iterations': iterations,
            'metrics': {
                'concat_ms': concat_time * 1000,
                'join_ms': join_time * 1000,
                'improvement_percent': ((concat_time - join_time) / concat_time) * 100,
            }
        }
        
        return result_data
    
    async def benchmark_list_operations(self, size: int = 10000) -> Dict:
        """基準測試：列表操作"""
        from collections import deque
        
        # 測試 1 - 列表 pop(0) - 低效
        test_list = list(range(size))
        start = time.time()
        for _ in range(100):
            if test_list:
                test_list.pop(0)
        list_pop_time = time.time() - start
        
        # 測試 2 - deque popleft - 高效
        test_deque = deque(range(size))
        start = time.time()
        for _ in range(100):
            if test_deque:
                test_deque.popleft()
        deque_pop_time = time.time() - start
        
        result = {
            'test': 'list_operations',
            'size': size,
            'metrics': {
                'list_pop_ms': list_pop_time * 1000,
                'deque_popleft_ms': deque_pop_time * 1000,
                'efficiency_improvement_percent': ((list_pop_time - deque_pop_time) / list_pop_time) * 100,
            }
        }
        
        return result
    
    async def run_all_benchmarks(self) -> Dict:
        """運行所有基準測試"""
        print("\n🚀 開始效能基準測試...\n")
        
        tests = [
            ("日誌性能", self.benchmark_logging(1000)),
            ("JSON 序列化", self.benchmark_json_serialization(1000)),
            ("內存操作", self.benchmark_memory_operations(10000)),
            ("字符串操作", self.benchmark_string_operations(10000)),
            ("列表操作", self.benchmark_list_operations(10000)),
        ]
        
        for test_name, test_coro in tests:
            print(f"⏳ 測試: {test_name}...")
            result = await test_coro
            self.results['tests'][test_name] = result
            print(f"✅ 完成: {test_name}\n")
        
        return self.results
    
    def print_summary(self) -> None:
        """打印摘要報告"""
        print("\n" + "="*80)
        print("📊 效能基準測試報告")
        print("="*80 + "\n")
        
        for test_name, test_data in self.results.get('tests', {}).items():
            print(f"\n🔍 {test_name}")
            print("-" * 80)
            
            metrics = test_data.get('metrics', {})
            for metric_name, value in metrics.items():
                if 'percent' in metric_name.lower():
                    print(f"   {metric_name}: {value:.2f}%")
                elif 'ms' in metric_name or 'us' in metric_name:
                    print(f"   {metric_name}: {value:.4f}")
                else:
                    print(f"   {metric_name}: {value}")
        
        print("\n" + "="*80)
        print("✅ 基準測試完成")
        print("="*80 + "\n")
    
    def save_results(self, filename: str = "benchmark_results.json") -> None:
        """保存結果到 JSON 文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"✅ 結果已保存到 {filename}")


async def main():
    """主函數"""
    benchmark = PerformanceBenchmark()
    
    try:
        await benchmark.run_all_benchmarks()
        benchmark.print_summary()
        benchmark.save_results()
    except Exception as e:
        print(f"❌ 基準測試出錯: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
