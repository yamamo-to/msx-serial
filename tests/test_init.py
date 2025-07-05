"""Test package initialization"""

import unittest

import msx_serial
from msx_serial import MSXSession, MSXTerminal, main


class TestInit(unittest.TestCase):
    """Test package initialization functionality"""

    def test_package_import(self) -> None:
        """Test basic package import"""
        self.assertIsNotNone(msx_serial)

    def test_package_has_version(self) -> None:
        """Test package has version attribute"""
        self.assertTrue(hasattr(msx_serial, "__version__"))

    def test_version_format(self) -> None:
        """Test version format is correct"""
        version = msx_serial.__version__
        self.assertIsInstance(version, str)
        self.assertGreater(len(version), 0)

    def test_package_main_module(self) -> None:
        """Test package main module can be imported"""
        self.assertIsNotNone(msx_serial.__main__)

    def test_core_components(self) -> None:
        """Test core components can be imported"""
        from msx_serial.core import data_processor, msx_session

        self.assertIsNotNone(msx_session)
        self.assertIsNotNone(data_processor)

    def test_connection_components(self) -> None:
        """Test connection components can be imported"""
        from msx_serial.connection import config_factory, connection

        self.assertIsNotNone(config_factory)
        self.assertIsNotNone(connection)


class TestMSXSerialInit(unittest.TestCase):
    """MSX Serial Terminal初期化テスト"""

    def test_version_import_success(self):
        """バージョンインポート成功テスト"""
        # 正常なバージョンインポート
        self.assertIsNotNone(msx_serial.__version__)
        self.assertTrue(hasattr(msx_serial, "__version__"))

    @unittest.skip("setuptools_scm環境では_version.pyが常に存在するためスキップ")
    def test_version_import_fallback(self):
        """バージョンインポート失敗時のフォールバックテスト"""
        # _versionモジュールが存在しない場合のテスト
        import sys

        if "msx_serial._version" in sys.modules:
            del sys.modules["msx_serial._version"]
        if "msx_serial" in sys.modules:
            del sys.modules["msx_serial"]
        import importlib

        msx_serial_reloaded = importlib.import_module("msx_serial")
        self.assertEqual(msx_serial_reloaded.__version__, "0.0.0.dev")

    def test_msx_terminal_alias(self):
        """MSXTerminalエイリアステスト"""
        # MSXTerminalがMSXSessionのエイリアスであることを確認
        self.assertIs(MSXTerminal, MSXSession)

    def test_main_function_exists(self):
        """main関数存在テスト"""
        # main関数が存在することを確認
        self.assertTrue(callable(main))

    def test_all_exports(self):
        """__all__エクスポートテスト"""
        # __all__に必要な要素が含まれていることを確認
        expected_exports = ["MSXSession", "MSXTerminal", "main"]
        for export in expected_exports:
            self.assertIn(export, msx_serial.__all__)


class TestVersionModule(unittest.TestCase):
    """バージョンモジュールテスト"""

    def test_version_attributes(self):
        """バージョン属性テスト"""
        from msx_serial import _version

        # バージョン属性が存在することを確認
        self.assertTrue(hasattr(_version, "version"))
        self.assertTrue(hasattr(_version, "__version__"))
        self.assertTrue(hasattr(_version, "__version_tuple__"))
        self.assertTrue(hasattr(_version, "version_tuple"))

    def test_version_values(self):
        """バージョン値テスト"""
        from msx_serial import _version

        # バージョン値が適切な形式であることを確認
        self.assertIsInstance(_version.version, str)
        self.assertIsInstance(_version.__version__, str)
        self.assertIsInstance(_version.__version_tuple__, tuple)
        self.assertIsInstance(_version.version_tuple, tuple)

    def test_version_consistency(self):
        """バージョン一貫性テスト"""
        from msx_serial import _version

        # バージョン値が一貫していることを確認
        self.assertEqual(_version.version, _version.__version__)
        self.assertEqual(_version.version_tuple, _version.__version_tuple__)

    def test_type_checking_import(self):
        """TYPE_CHECKINGインポートテスト"""
        from msx_serial import _version

        # TYPE_CHECKINGが適切に設定されていることを確認
        self.assertIsInstance(_version.TYPE_CHECKING, bool)

    def test_version_tuple_structure(self):
        """バージョンタプル構造テスト"""
        from msx_serial import _version

        # バージョンタプルが適切な構造であることを確認
        version_tuple = _version.version_tuple
        self.assertGreaterEqual(len(version_tuple), 3)  # 少なくともmajor.minor.patch

        # 各要素が適切な型であることを確認
        for i, component in enumerate(version_tuple):
            if i < 3:  # major, minor, patch
                self.assertIsInstance(component, int)
            else:  # 追加の要素（dev, alpha等）
                self.assertIsInstance(component, (int, str))

        # バージョン文字列とタプルの一貫性を確認
        version_str = _version.version
        self.assertIsInstance(version_str, str)
        self.assertGreater(len(version_str), 0)

        # バージョン情報の妥当性を確認
        self.assertEqual(_version.version, _version.__version__)
        self.assertEqual(_version.version_tuple, _version.__version_tuple__)

        # バージョン番号の妥当性を確認
        major, minor, patch = version_tuple[:3]
        self.assertGreaterEqual(major, 0)
        self.assertGreaterEqual(minor, 0)
        self.assertGreaterEqual(patch, 0)


if __name__ == "__main__":
    unittest.main()
