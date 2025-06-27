"""
キャッシュマネージャーのテスト
"""

import time
import unittest

from msx_serial.common.cache_manager import (
    CacheEntry,
    CacheManager,
    CacheStrategy,
    FunctionCache,
    cached,
    get_global_cache,
)


class TestCacheEntry(unittest.TestCase):
    """CacheEntryのテスト"""

    def test_is_expired_with_ttl(self):
        """TTL付きエントリの期限切れテスト"""
        entry = CacheEntry(
            key="test",
            value="value",
            created_at=time.time() - 10,
            last_accessed=time.time(),
            ttl=5.0,
        )
        self.assertTrue(entry.is_expired())

    def test_is_expired_without_ttl(self):
        """TTLなしエントリの期限切れテスト"""
        entry = CacheEntry(
            key="test",
            value="value",
            created_at=time.time(),
            last_accessed=time.time(),
            ttl=None,
        )
        self.assertFalse(entry.is_expired())

    def test_touch(self):
        """touchメソッドのテスト"""
        entry = CacheEntry(
            key="test", value="value", created_at=time.time(), last_accessed=time.time()
        )
        original_access_count = entry.access_count
        original_last_accessed = entry.last_accessed

        time.sleep(0.01)  # 少し待機
        entry.touch()

        self.assertEqual(entry.access_count, original_access_count + 1)
        self.assertGreater(entry.last_accessed, original_last_accessed)


class TestCacheManager(unittest.TestCase):
    """キャッシュマネージャーのテスト"""

    def setUp(self):
        """テストセットアップ"""
        self.cache = CacheManager[str](max_size=3, strategy=CacheStrategy.LRU)

    def test_basic_operations(self):
        """基本操作のテスト"""
        # 存在しないキー
        self.assertIsNone(self.cache.get("key1"))
        self.assertFalse(self.cache.exists("key1"))

        # 値の設定と取得
        self.cache.put("key1", "value1")
        self.assertEqual(self.cache.get("key1"), "value1")
        self.assertTrue(self.cache.exists("key1"))
        self.assertEqual(self.cache.size(), 1)

    def test_put_existing_entry_update(self):
        """既存エントリの更新テスト"""
        # 最初にエントリを追加
        self.cache.put("key1", "value1")
        self.assertEqual(self.cache.get("key1"), "value1")

        # 同じキーで値を更新
        self.cache.put("key1", "updated_value")
        self.assertEqual(self.cache.get("key1"), "updated_value")
        self.assertEqual(self.cache.size(), 1)  # サイズは変わらない

    def test_lru_eviction(self):
        """LRU削除のテスト"""
        # 容量を超えて追加
        self.cache.put("key1", "value1")
        self.cache.put("key2", "value2")
        self.cache.put("key3", "value3")
        self.cache.put("key4", "value4")  # key1が削除される

        self.assertIsNone(self.cache.get("key1"))
        self.assertEqual(self.cache.get("key2"), "value2")
        self.assertEqual(self.cache.size(), 3)

    def test_lru_access_order(self):
        """LRUアクセス順序のテスト"""
        self.cache.put("key1", "value1")
        self.cache.put("key2", "value2")
        self.cache.put("key3", "value3")

        # key1にアクセスして最新にする
        self.cache.get("key1")

        # 新しいキーを追加（key2が削除される）
        self.cache.put("key4", "value4")

        self.assertEqual(self.cache.get("key1"), "value1")
        self.assertIsNone(self.cache.get("key2"))
        self.assertEqual(self.cache.get("key3"), "value3")
        self.assertEqual(self.cache.get("key4"), "value4")

    def test_fifo_eviction_strategy(self):
        """FIFO削除戦略のテスト"""
        cache = CacheManager[str](max_size=2, strategy=CacheStrategy.FIFO)

        cache.put("key1", "value1")
        time.sleep(0.01)  # 作成時刻を異なるものにする
        cache.put("key2", "value2")

        # 新しいエントリを追加（key1が最初に作成されたので削除される）
        cache.put("key3", "value3")

        self.assertIsNone(cache.get("key1"))  # 最初に作成されたので削除
        self.assertEqual(cache.get("key2"), "value2")
        self.assertEqual(cache.get("key3"), "value3")

    def test_ttl_eviction_strategy(self):
        """TTL削除戦略のテスト"""
        cache = CacheManager[str](max_size=2, strategy=CacheStrategy.TTL, default_ttl=0.1)

        cache.put("key1", "value1", ttl=0.05)  # 短いTTL
        cache.put("key2", "value2", ttl=1.0)  # 長いTTL

        time.sleep(0.06)  # key1のTTLが切れる

        # 新しいエントリを追加（期限切れのkey1が削除される）
        cache.put("key3", "value3")

        self.assertIsNone(cache.get("key1"))  # 期限切れで削除
        self.assertEqual(cache.get("key2"), "value2")
        self.assertEqual(cache.get("key3"), "value3")

    def test_ttl_eviction_no_expired(self):
        """TTL戦略で期限切れがない場合のテスト"""
        cache = CacheManager[str](max_size=2, strategy=CacheStrategy.TTL)

        cache.put("key1", "value1")
        cache.put("key2", "value2")

        # 期限切れがない場合は最初のエントリが削除される
        cache.put("key3", "value3")

        self.assertEqual(cache.size(), 2)

    def test_ttl_expiration(self):
        """TTL期限切れのテスト"""
        cache = CacheManager[str](default_ttl=0.1)

        cache.put("key1", "value1")
        self.assertEqual(cache.get("key1"), "value1")

        # TTL経過後
        time.sleep(0.15)
        self.assertIsNone(cache.get("key1"))
        self.assertFalse(cache.exists("key1"))

    def test_exists_with_expired_entry(self):
        """期限切れエントリのexistsテスト"""
        cache = CacheManager[str](default_ttl=0.05)

        cache.put("key1", "value1")
        self.assertTrue(cache.exists("key1"))

        time.sleep(0.06)  # TTLが切れる

        # 期限切れの場合はFalseを返し、エントリが削除される
        self.assertFalse(cache.exists("key1"))
        self.assertEqual(cache.size(), 0)

    def test_cleanup_expired(self):
        """期限切れクリーンアップのテスト"""
        cache = CacheManager[str](default_ttl=0.05)

        cache.put("key1", "value1")
        cache.put("key2", "value2", ttl=1.0)  # 長いTTL

        time.sleep(0.06)  # key1のTTLが切れる

        # クリーンアップを実行
        cleaned_count = cache.cleanup_expired()

        self.assertEqual(cleaned_count, 1)  # 1つのエントリがクリーンアップされた
        self.assertEqual(cache.size(), 1)  # key2のみ残る
        self.assertIsNone(cache.get("key1"))
        self.assertEqual(cache.get("key2"), "value2")

    def test_delete_and_clear(self):
        """削除とクリアのテスト"""
        self.cache.put("key1", "value1")
        self.cache.put("key2", "value2")

        # 単一削除
        self.assertTrue(self.cache.delete("key1"))
        self.assertFalse(self.cache.delete("key1"))  # 存在しないキー
        self.assertEqual(self.cache.size(), 1)

        # 全クリア
        self.cache.clear()
        self.assertEqual(self.cache.size(), 0)
        self.assertIsNone(self.cache.get("key2"))

    def test_delete_with_access_order(self):
        """アクセス順序があるエントリの削除テスト"""
        self.cache.put("key1", "value1")
        self.cache.get("key1")  # アクセス順序に追加

        result = self.cache.delete("key1")

        self.assertTrue(result)
        self.assertEqual(self.cache.size(), 0)
        self.assertIsNone(self.cache.get("key1"))

    def test_clear_resets_stats(self):
        """clearがstatsをリセットするかテスト"""
        self.cache.put("key1", "value1")
        self.cache.get("key1")  # ヒット
        self.cache.get("nonexistent")  # ミス

        stats_before = self.cache.get_stats()
        self.assertGreater(stats_before["hits"], 0)
        self.assertGreater(stats_before["misses"], 0)

        self.cache.clear()

        stats_after = self.cache.get_stats()
        self.assertEqual(stats_after["hits"], 0)
        self.assertEqual(stats_after["misses"], 0)
        self.assertEqual(stats_after["evictions"], 0)
        self.assertEqual(stats_after["expired"], 0)

    def test_evict_empty_cache(self):
        """空のキャッシュでの削除テスト"""
        # 空のキャッシュで_evictを呼んでもエラーにならない
        self.cache._evict()
        self.assertEqual(self.cache.size(), 0)

    def test_stats(self):
        """統計情報のテスト"""
        self.cache.put("key1", "value1")

        # ヒット
        self.cache.get("key1")

        # ミス
        self.cache.get("nonexistent")

        stats = self.cache.get_stats()
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 1)
        self.assertEqual(stats["total_requests"], 2)
        self.assertEqual(stats["hit_rate"], 50.0)

    def test_lfu_strategy(self):
        """LFU戦略のテスト"""
        cache = CacheManager[str](max_size=2, strategy=CacheStrategy.LFU)

        cache.put("key1", "value1")
        cache.put("key2", "value2")

        # key1を複数回アクセス
        cache.get("key1")
        cache.get("key1")
        cache.get("key2")  # 1回だけ

        # 新しいキーを追加（key2が削除される）
        cache.put("key3", "value3")

        self.assertEqual(cache.get("key1"), "value1")
        self.assertIsNone(cache.get("key2"))
        self.assertEqual(cache.get("key3"), "value3")


class TestFunctionCache(unittest.TestCase):
    """FunctionCacheの詳細テスト"""

    def test_function_cache_with_kwargs(self):
        """キーワード引数ありのFunctionCacheテスト"""

        @cached()
        def test_function(x: int, y: int = 1) -> int:
            return x + y

        result1 = test_function(5, y=2)
        result2 = test_function(5, y=2)
        result3 = test_function(x=5, y=2)

        self.assertEqual(result1, 7)
        self.assertEqual(result2, 7)
        self.assertEqual(result3, 7)

    def test_function_cache_info(self):
        """FunctionCacheのinfo表示テスト"""

        @cached()
        def test_function(x: int) -> int:
            return x * 2

        test_function(5)
        info = test_function.cache_info()

        self.assertIsInstance(info, str)
        self.assertIn("Cache:", info)

    def test_generate_key_consistency(self):
        """キー生成の一貫性テスト"""
        cache = FunctionCache()

        def test_func(a, b=1):
            return a + b

        key1 = cache._generate_key(test_func, (5,), {"b": 2})
        key2 = cache._generate_key(test_func, (5,), {"b": 2})
        key3 = cache._generate_key(test_func, (5,), {"b": 3})

        self.assertEqual(key1, key2)  # 同じ引数なら同じキー
        self.assertNotEqual(key1, key3)  # 異なる引数なら異なるキー


class TestCachedDecorator(unittest.TestCase):
    """キャッシュデコレーターのテスト"""

    def test_function_caching(self):
        """関数キャッシュのテスト"""
        call_count = 0

        @cached(max_size=10)
        def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y

        # 初回呼び出し
        result1 = expensive_function(1, 2)
        self.assertEqual(result1, 3)
        self.assertEqual(call_count, 1)

        # キャッシュされた結果
        result2 = expensive_function(1, 2)
        self.assertEqual(result2, 3)
        self.assertEqual(call_count, 1)  # 関数は呼ばれない

        # 異なる引数
        result3 = expensive_function(2, 3)
        self.assertEqual(result3, 5)
        self.assertEqual(call_count, 2)

    def test_cache_clear(self):
        """キャッシュクリアのテスト"""
        call_count = 0

        @cached(max_size=10)
        def test_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        test_function(5)
        self.assertEqual(call_count, 1)

        test_function(5)  # キャッシュヒット
        self.assertEqual(call_count, 1)

        test_function.cache_clear()

        test_function(5)  # キャッシュクリア後
        self.assertEqual(call_count, 2)

    def test_cache_with_ttl(self):
        """TTL付きキャッシュのテスト"""
        call_count = 0

        @cached(max_size=10, ttl=0.1)
        def test_function(x):
            nonlocal call_count
            call_count += 1
            return x * 3

        result1 = test_function(2)
        self.assertEqual(result1, 6)
        self.assertEqual(call_count, 1)

        # TTL内の再呼び出し
        result2 = test_function(2)
        self.assertEqual(result2, 6)
        self.assertEqual(call_count, 1)

        # TTL経過後
        time.sleep(0.15)
        result3 = test_function(2)
        self.assertEqual(result3, 6)
        self.assertEqual(call_count, 2)

    def test_cached_decorator_function(self):
        """cachedデコレーター関数のテスト"""
        decorator = cached(max_size=10, ttl=1.0, strategy=CacheStrategy.LFU)
        self.assertIsInstance(decorator, FunctionCache)


class TestGlobalCache(unittest.TestCase):
    """グローバルキャッシュのテスト"""

    def test_global_cache_access(self):
        """グローバルキャッシュアクセスのテスト"""
        cache = get_global_cache()
        self.assertIsInstance(cache, CacheManager)

        # 同じインスタンスが返されることを確認
        cache2 = get_global_cache()
        self.assertIs(cache, cache2)


if __name__ == "__main__":
    unittest.main()
