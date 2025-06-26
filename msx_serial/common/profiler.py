"""
パフォーマンス監視とプロファイリング機能
"""

import threading
import time
from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Dict, Iterator, List, Optional
from contextlib import _GeneratorContextManager


@dataclass
class PerformanceMetrics:
    """パフォーマンスメトリクス"""

    function_name: str
    execution_time: float
    memory_usage: Optional[int] = None
    call_count: int = 1
    timestamp: float = 0.0

    def __post_init__(self) -> None:
        if self.timestamp == 0.0:
            self.timestamp = time.time()


class PerformanceProfiler:
    """パフォーマンスプロファイラー"""

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.call_counts: Dict[str, int] = defaultdict(int)
        self.total_times: Dict[str, float] = defaultdict(float)
        self._lock = threading.Lock()
        self.enabled = False

    def enable(self) -> None:
        """プロファイリングを有効化"""
        self.enabled = True

    def disable(self) -> None:
        """プロファイリングを無効化"""
        self.enabled = False

    @contextmanager
    def profile(self, function_name: str) -> Iterator[None]:
        """コンテキストマネージャーでパフォーマンス測定"""
        if not self.enabled:
            yield
            return

        start_time = time.perf_counter()
        try:
            yield
        finally:
            execution_time = time.perf_counter() - start_time
            self.record_metric(function_name, execution_time)

    def record_metric(self, function_name: str, execution_time: float) -> None:
        """メトリクスを記録"""
        if not self.enabled:
            return

        with self._lock:
            metric = PerformanceMetrics(
                function_name=function_name, execution_time=execution_time
            )
            self.metrics[function_name].append(metric)
            self.call_counts[function_name] += 1
            self.total_times[function_name] += execution_time

    def get_statistics(self) -> Dict[str, Any]:
        """統計情報を取得"""
        with self._lock:
            stats = {}
            for func_name, metrics in self.metrics.items():
                if not metrics:
                    continue

                times = [m.execution_time for m in metrics]
                stats[func_name] = {
                    "call_count": self.call_counts[func_name],
                    "total_time": self.total_times[func_name],
                    "avg_time": self.total_times[func_name]
                    / self.call_counts[func_name],
                    "min_time": min(times),
                    "max_time": max(times),
                    "recent_calls": len(times),
                }
            return stats

    def get_slowest_functions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """最も遅い関数を取得"""
        stats = self.get_statistics()
        sorted_funcs = sorted(
            stats.items(), key=lambda x: x[1]["avg_time"], reverse=True
        )
        return [{"function": name, **data} for name, data in sorted_funcs[:limit]]

    def clear(self) -> None:
        """メトリクスをクリア"""
        with self._lock:
            self.metrics.clear()
            self.call_counts.clear()
            self.total_times.clear()


# グローバルプロファイラーインスタンス
_global_profiler = PerformanceProfiler()


def profile_function(func: Callable[..., Any]) -> Callable[..., Any]:
    """関数デコレーター"""

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        with _global_profiler.profile(f"{func.__module__}.{func.__qualname__}"):
            return func(*args, **kwargs)

    return wrapper


def get_profiler() -> PerformanceProfiler:
    """グローバルプロファイラーを取得"""
    return _global_profiler


def enable_profiling() -> None:
    """グローバルプロファイリングを有効化"""
    _global_profiler.enable()


def disable_profiling() -> None:
    """グローバルプロファイリングを無効化"""
    _global_profiler.disable()


def profile_context(name: str) -> _GeneratorContextManager[None]:
    """プロファイリングコンテキスト"""
    return _global_profiler.profile(name)
