"""
プロファイラーのテスト
"""

import time
import unittest

from msx_serial.common.profiler import (
    PerformanceProfiler,
    disable_profiling,
    enable_profiling,
    get_profiler,
    profile_context,
    profile_function,
)


class TestPerformanceProfiler(unittest.TestCase):
    """パフォーマンスプロファイラーのテスト"""

    def setUp(self):
        """テストセットアップ"""
        self.profiler = PerformanceProfiler(max_history=100)

    def test_profiler_disabled_by_default(self):
        """デフォルトで無効化されていることをテスト"""
        self.assertFalse(self.profiler.enabled)

    def test_enable_disable_profiling(self):
        """プロファイリングの有効化・無効化をテスト"""
        self.profiler.enable()
        self.assertTrue(self.profiler.enabled)

        self.profiler.disable()
        self.assertFalse(self.profiler.enabled)

    def test_profile_context_disabled(self):
        """無効時のプロファイルコンテキストをテスト"""
        with self.profiler.profile("test_function"):
            time.sleep(0.01)

        stats = self.profiler.get_statistics()
        self.assertEqual(len(stats), 0)

    def test_profile_context_enabled(self):
        """有効時のプロファイルコンテキストをテスト"""
        self.profiler.enable()

        with self.profiler.profile("test_function"):
            time.sleep(0.01)

        stats = self.profiler.get_statistics()
        self.assertIn("test_function", stats)
        self.assertEqual(stats["test_function"]["call_count"], 1)
        self.assertGreater(stats["test_function"]["total_time"], 0.005)

    def test_multiple_calls(self):
        """複数回呼び出しのテスト"""
        self.profiler.enable()

        for i in range(3):
            with self.profiler.profile("test_function"):
                time.sleep(0.005)

        stats = self.profiler.get_statistics()
        self.assertEqual(stats["test_function"]["call_count"], 3)
        self.assertGreater(stats["test_function"]["avg_time"], 0.003)

    def test_slowest_functions(self):
        """最も遅い関数の取得をテスト"""
        self.profiler.enable()

        with self.profiler.profile("fast_function"):
            time.sleep(0.001)

        with self.profiler.profile("slow_function"):
            time.sleep(0.01)

        slowest = self.profiler.get_slowest_functions(limit=2)
        self.assertEqual(len(slowest), 2)
        self.assertEqual(slowest[0]["function"], "slow_function")
        self.assertEqual(slowest[1]["function"], "fast_function")

    def test_clear_metrics(self):
        """メトリクスクリアのテスト"""
        self.profiler.enable()

        with self.profiler.profile("test_function"):
            time.sleep(0.001)

        self.profiler.clear()
        stats = self.profiler.get_statistics()
        self.assertEqual(len(stats), 0)


class TestProfileDecorator(unittest.TestCase):
    """プロファイルデコレーターのテスト"""

    def setUp(self):
        """テストセットアップ"""
        enable_profiling()

    def tearDown(self):
        """テストクリーンアップ"""
        disable_profiling()
        get_profiler().clear()

    def test_profile_function_decorator(self):
        """関数デコレーターのテスト"""

        @profile_function
        def test_function(x, y):
            time.sleep(0.001)
            return x + y

        result = test_function(1, 2)
        self.assertEqual(result, 3)

        stats = get_profiler().get_statistics()
        # 実際のキー名を確認
        expected_key = "tests.test_profiler.TestProfileDecorator.test_profile_function_decorator.<locals>.test_function"
        self.assertIn(expected_key, stats)

    def test_global_profiler_context(self):
        """グローバルプロファイラーコンテキストのテスト"""
        with profile_context("global_test"):
            time.sleep(0.001)

        stats = get_profiler().get_statistics()
        self.assertIn("global_test", stats)


if __name__ == "__main__":
    unittest.main()
