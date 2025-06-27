"""
高度なキャッシュシステム
"""

import hashlib
import logging
import pickle
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Generic, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CacheStrategy(Enum):
    """キャッシュ戦略"""

    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    FIFO = "fifo"  # First In First Out
    TTL = "ttl"  # Time To Live


@dataclass
class CacheEntry:
    """キャッシュエントリ"""

    key: str
    value: Any
    created_at: float
    last_accessed: float
    access_count: int = 0
    ttl: Optional[float] = None

    def is_expired(self) -> bool:
        """期限切れかどうかを判定"""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl

    def touch(self) -> None:
        """アクセス時刻と回数を更新"""
        self.last_accessed = time.time()
        self.access_count += 1


class CacheManager(Generic[T]):
    """高度なキャッシュマネージャー"""

    def __init__(
        self,
        max_size: int = 1000,
        strategy: CacheStrategy = CacheStrategy.LRU,
        default_ttl: Optional[float] = None,
    ):
        self.max_size = max_size
        self.strategy = strategy
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order: OrderedDict = OrderedDict()
        self._lock = threading.RLock()
        self.stats = {"hits": 0, "misses": 0, "evictions": 0, "expired": 0}

    def get(self, key: str) -> Optional[T]:
        """キャッシュから値を取得"""
        with self._lock:
            if key not in self.cache:
                self.stats["misses"] += 1
                return None

            entry = self.cache[key]

            # 期限切れチェック
            if entry.is_expired():
                del self.cache[key]
                if key in self.access_order:
                    del self.access_order[key]
                self.stats["expired"] += 1
                self.stats["misses"] += 1
                return None

            # アクセス情報更新
            entry.touch()
            self._update_access_order(key)
            self.stats["hits"] += 1
            return entry.value  # type: ignore

    def put(self, key: str, value: T, ttl: Optional[float] = None) -> None:
        """キャッシュに値を設定"""
        with self._lock:
            current_time = time.time()
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=current_time,
                last_accessed=current_time,
                ttl=ttl or self.default_ttl,
            )

            # 既存エントリの更新
            if key in self.cache:
                self.cache[key] = entry
                self._update_access_order(key)
                return

            # 容量チェックと削除
            if len(self.cache) >= self.max_size:
                self._evict()

            self.cache[key] = entry
            self.access_order[key] = current_time

    def delete(self, key: str) -> bool:
        """キャッシュから削除"""
        with self._lock:
            if key in self.cache:
                del self.cache[key]
                if key in self.access_order:
                    del self.access_order[key]
                return True
            return False

    def clear(self) -> None:
        """キャッシュをクリア"""
        with self._lock:
            self.cache.clear()
            self.access_order.clear()
            self.stats = {"hits": 0, "misses": 0, "evictions": 0, "expired": 0}

    def exists(self, key: str) -> bool:
        """キーが存在するかチェック"""
        with self._lock:
            if key not in self.cache:
                return False

            entry = self.cache[key]
            if entry.is_expired():
                del self.cache[key]
                if key in self.access_order:
                    del self.access_order[key]
                self.stats["expired"] += 1
                return False

            return True

    def size(self) -> int:
        """現在のキャッシュサイズ"""
        return len(self.cache)

    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        with self._lock:
            total_requests = self.stats["hits"] + self.stats["misses"]
            hit_rate = (
                (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
            )

            return {
                **self.stats,
                "total_requests": total_requests,
                "hit_rate": hit_rate,
                "current_size": len(self.cache),
                "max_size": self.max_size,
                "strategy": self.strategy.value,
            }

    def _update_access_order(self, key: str) -> None:
        """アクセス順序を更新"""
        if self.strategy == CacheStrategy.LRU:
            if key in self.access_order:
                del self.access_order[key]
            self.access_order[key] = time.time()

    def _evict(self) -> None:
        """削除戦略に基づいてエントリを削除"""
        if not self.cache:
            return

        key_to_evict = None

        if self.strategy == CacheStrategy.LRU:
            key_to_evict = next(iter(self.access_order))
        elif self.strategy == CacheStrategy.LFU:
            key_to_evict = min(
                self.cache.keys(), key=lambda k: self.cache[k].access_count
            )
        elif self.strategy == CacheStrategy.FIFO:
            key_to_evict = min(
                self.cache.keys(), key=lambda k: self.cache[k].created_at
            )
        elif self.strategy == CacheStrategy.TTL:
            # 期限切れのものを優先的に削除
            expired_keys = [k for k, v in self.cache.items() if v.is_expired()]
            if expired_keys:
                key_to_evict = expired_keys[0]
            else:
                key_to_evict = next(iter(self.cache))

        if key_to_evict:
            del self.cache[key_to_evict]
            if key_to_evict in self.access_order:
                del self.access_order[key_to_evict]
            self.stats["evictions"] += 1

    def cleanup_expired(self) -> int:
        """期限切れエントリをクリーンアップ"""
        with self._lock:
            expired_keys = [
                key for key, entry in self.cache.items() if entry.is_expired()
            ]

            for key in expired_keys:
                del self.cache[key]
                if key in self.access_order:
                    del self.access_order[key]

            self.stats["expired"] += len(expired_keys)
            return len(expired_keys)


class FunctionCache:
    """関数結果キャッシュデコレーター"""

    def __init__(
        self,
        max_size: int = 128,
        ttl: Optional[float] = None,
        strategy: CacheStrategy = CacheStrategy.LRU,
    ):
        self.cache_manager = CacheManager[Any](max_size, strategy, ttl)

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # キーを生成
            key = self._generate_key(func, args, kwargs)

            # キャッシュから取得を試行
            result = self.cache_manager.get(key)
            if result is not None:
                return result

            # 関数を実行してキャッシュに保存
            result = func(*args, **kwargs)
            self.cache_manager.put(key, result)
            return result

        # キャッシュ操作メソッドを追加
        wrapper.cache_clear = self.cache_manager.clear  # type: ignore
        wrapper.cache_stats = self.cache_manager.get_stats  # type: ignore
        wrapper.cache_info = lambda: f"Cache: {self.cache_manager.get_stats()}"  # type: ignore

        return wrapper

    def _generate_key(self, func: Callable, args: tuple, kwargs: dict) -> str:
        """関数とパラメータからキーを生成"""
        key_data = {
            "func": f"{func.__module__}.{func.__qualname__}",
            "args": args,
            "kwargs": sorted(kwargs.items()),
        }

        # ハッシュ化（セキュリティ上安全なSHA256を使用）
        serialized = pickle.dumps(key_data, protocol=pickle.HIGHEST_PROTOCOL)
        return hashlib.sha256(serialized).hexdigest()


# グローバルキャッシュインスタンス
_global_cache = CacheManager[Any]()


def cached(
    max_size: int = 128,
    ttl: Optional[float] = None,
    strategy: CacheStrategy = CacheStrategy.LRU,
) -> FunctionCache:
    """関数キャッシュデコレーター"""
    return FunctionCache(max_size, ttl, strategy)


def get_global_cache() -> CacheManager[Any]:
    """グローバルキャッシュを取得"""
    return _global_cache
