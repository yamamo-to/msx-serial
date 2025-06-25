"""
Test for msx_serial/_version.py
"""

import unittest
from typing import TYPE_CHECKING


class TestVersion(unittest.TestCase):
    """_version.pyのテスト"""

    def test_version_string_format(self):
        """バージョン文字列の形式をテスト"""
        from msx_serial._version import version
        # セマンティックバージョニング形式であることを確認
        parts = version.split('.')
        self.assertGreaterEqual(len(parts), 3)
        for part in parts[:3]:  # メジャー、マイナー、パッチ
            if part.isdigit():
                self.assertTrue(part.isdigit())

    def test_version_tuple_format(self):
        """バージョンタプルの形式をテスト"""
        from msx_serial._version import version_tuple
        self.assertIsInstance(version_tuple, tuple)
        self.assertGreaterEqual(len(version_tuple), 3)
        # 最初の3つの要素は整数であることを確認
        for i in range(min(3, len(version_tuple))):
            self.assertIsInstance(version_tuple[i], int)

    def test_version_consistency(self):
        """バージョン文字列とタプルの一貫性をテスト"""
        from msx_serial._version import version, version_tuple
        version_parts = version.split('.')
        
        # 最初の3つの要素が一致することを確認
        for i in range(min(3, len(version_tuple), len(version_parts))):
            if version_parts[i].isdigit():
                self.assertEqual(int(version_parts[i]), version_tuple[i])

    def test_all_exports(self):
        """__all__に含まれる全ての要素がエクスポートされることをテスト"""
        import msx_serial._version as version_module
        for item in version_module.__all__:
            self.assertTrue(hasattr(version_module, item))

    def test_double_underscore_aliases(self):
        """__で始まるエイリアスが正しく設定されていることをテスト"""
        from msx_serial._version import version, __version__, version_tuple, __version_tuple__
        self.assertEqual(version, __version__)
        self.assertEqual(version_tuple, __version_tuple__)

    def test_type_checking_flag(self):
        """TYPE_CHECKING フラグの動作をテスト"""
        from msx_serial._version import TYPE_CHECKING
        # TYPE_CHECKINGはランタイムではFalseであることを確認
        self.assertFalse(TYPE_CHECKING)

    def test_version_tuple_type(self):
        """VERSION_TUPLE型の動作をテスト"""
        from msx_serial._version import VERSION_TUPLE
        # ランタイムではobjectクラスであることを確認
        self.assertEqual(VERSION_TUPLE, object)


if __name__ == "__main__":
    unittest.main()
