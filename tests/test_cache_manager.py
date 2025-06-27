"""
キャッシュマネージャーのテスト
"""

import time
import unittest

from msx_serial.common.cache_manager import (CacheManager, CacheStrategy,
                                             cached, get_global_cache)


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

    def test_ttl_expiration(self):
        """TTL期限切れのテスト"""
        cache = CacheManager[str](default_ttl=0.1)

        cache.put("key1", "value1")
        self.assertEqual(cache.get("key1"), "value1")

        # TTL経過後
        time.sleep(0.15)
        self.assertIsNone(cache.get("key1"))
        self.assertFalse(cache.exists("key1"))

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


class TestGlobalCache(unittest.TestCase):
    """グローバルキャッシュのテスト"""

    def setUp(self):
        """テストセットアップ"""
        get_global_cache().clear()

    def test_global_cache_access(self):
        """グローバルキャッシュアクセスのテスト"""
        cache = get_global_cache()

        cache.put("global_key", "global_value")
        self.assertEqual(cache.get("global_key"), "global_value")


if __name__ == "__main__":
    unittest.main()
