"""
ConfigManagerのテスト
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from msx_serial.common.config_manager import (
    ConfigManager,
    ConfigSchema,
    get_config,
    get_setting,
    set_setting,
)


class TestConfigSchema(unittest.TestCase):
    """ConfigSchemaのテスト"""

    def test_validate_valid_value(self):
        """有効な値の検証"""
        schema = ConfigSchema("test", 10, "Test", int, min_value=5, max_value=15)
        self.assertTrue(schema.validate(10))
        self.assertTrue(schema.validate(5))
        self.assertTrue(schema.validate(15))

    def test_validate_invalid_type(self):
        """無効な型の検証"""
        schema = ConfigSchema("test", 10, "Test", int)
        self.assertFalse(schema.validate("invalid"))

    def test_validate_type_conversion(self):
        """型変換の検証"""
        schema = ConfigSchema("test", 10, "Test", int)
        self.assertTrue(schema.validate("10"))

    def test_validate_required_missing(self):
        """必須項目の欠如検証"""
        schema = ConfigSchema("test", None, "Test", str, required=True)
        self.assertFalse(schema.validate(None))

    def test_validate_choices(self):
        """選択肢の検証"""
        schema = ConfigSchema("test", "a", "Test", str, choices=["a", "b", "c"])
        self.assertTrue(schema.validate("a"))
        self.assertFalse(schema.validate("d"))

    def test_validate_range(self):
        """範囲の検証"""
        schema = ConfigSchema("test", 10, "Test", int, min_value=5, max_value=15)
        self.assertFalse(schema.validate(4))
        self.assertFalse(schema.validate(16))

    def test_validate_float_range(self):
        """浮動小数点の範囲検証"""
        schema = ConfigSchema("test", 10.0, "Test", float, min_value=5.0, max_value=15.0)
        self.assertTrue(schema.validate(10.5))
        self.assertFalse(schema.validate(4.9))


class TestConfigManager(unittest.TestCase):
    """ConfigManagerのテスト"""

    def setUp(self):
        """テスト準備"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_manager = ConfigManager(self.temp_dir)

    def tearDown(self):
        """テスト後処理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init_creates_directory(self):
        """初期化時のディレクトリ作成"""
        self.assertTrue(self.temp_dir.exists())

    def test_register_schema(self):
        """スキーマ登録"""
        schema = ConfigSchema("test.key", "default", "Test", str)
        self.config_manager.register_schema(schema)
        self.assertIn("test.key", self.config_manager.schema)

    def test_get_default_value(self):
        """デフォルト値の取得"""
        value = self.config_manager.get("connection.timeout")
        self.assertEqual(value, 30)

    def test_get_custom_default(self):
        """カスタムデフォルト値の取得"""
        value = self.config_manager.get("nonexistent.key", "custom_default")
        self.assertEqual(value, "custom_default")

    def test_set_valid_value(self):
        """有効な値の設定"""
        result = self.config_manager.set("connection.timeout", 60, save=False)
        self.assertTrue(result)
        self.assertEqual(self.config_manager.get("connection.timeout"), 60)

    def test_set_invalid_value(self):
        """無効な値の設定"""
        result = self.config_manager.set("connection.timeout", -10, save=False)
        self.assertFalse(result)
        # 元の値が保持される
        self.assertEqual(self.config_manager.get("connection.timeout"), 30)

    def test_get_nested(self):
        """ネストされたキーの取得"""
        self.config_manager.config_data = {
            "connection": {"timeout": 45, "retry": 5}
        }
        value = self.config_manager.get_nested("connection.timeout")
        self.assertEqual(value, 45)

    def test_set_nested(self):
        """ネストされたキーの設定"""
        result = self.config_manager.set_nested("connection.timeout", 90, save=False)
        self.assertTrue(result)
        self.assertEqual(self.config_manager.get_nested("connection.timeout"), 90)

    def test_save_and_load_config(self):
        """設定の保存と読み込み"""
        # 設定値を変更
        self.config_manager.set("connection.timeout", 120, save=True)
        
        # 新しいインスタンスで読み込み
        new_manager = ConfigManager(self.temp_dir)
        self.assertEqual(new_manager.get("connection.timeout"), 120)

    def test_load_invalid_config_file(self):
        """無効な設定ファイルの読み込み"""
        # 無効なYAMLを書き込み
        config_file = self.temp_dir / "config.yaml"
        config_file.write_text("invalid: yaml: content: [")
        
        # エラーが発生しても続行する
        result = self.config_manager.load_config()
        self.assertFalse(result)

    def test_reset_to_defaults(self):
        """デフォルト値へのリセット"""
        self.config_manager.set("connection.timeout", 120, save=False)
        self.config_manager.reset_to_defaults()
        self.assertEqual(self.config_manager.get("connection.timeout"), 30)

    def test_validate_all(self):
        """全設定の検証"""
        self.config_manager.config_data["connection.timeout"] = -10  # 無効な値
        errors = self.config_manager.validate_all()
        self.assertIn("connection.timeout", errors)

    def test_add_remove_watcher(self):
        """ウォッチャーの追加と削除"""
        called = []
        
        def watcher(key, old_value, new_value):
            called.append((key, old_value, new_value))
        
        self.config_manager.add_watcher(watcher)
        self.config_manager.set("connection.timeout", 60, save=False)
        
        self.assertEqual(len(called), 1)
        self.assertEqual(called[0][0], "connection.timeout")
        
        # ウォッチャーを削除
        self.config_manager.remove_watcher(watcher)
        self.config_manager.set("connection.timeout", 90, save=False)
        
        # 追加の呼び出しなし
        self.assertEqual(len(called), 1)

    def test_get_schema_info(self):
        """スキーマ情報の取得"""
        info = self.config_manager.get_schema_info()
        self.assertIn("connection.timeout", info)
        self.assertEqual(info["connection.timeout"]["default"], 30)

    def test_json_format_detection(self):
        """JSON形式の検出"""
        config_file = self.temp_dir / "config.json"
        config_data = {"connection": {"timeout": 45}}
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        result = self.config_manager.load_config(config_file)
        self.assertTrue(result)

    @patch('msx_serial.common.config_manager.logger')
    def test_logging_on_invalid_value(self, mock_logger):
        """無効な値設定時のログ出力"""
        self.config_manager.set("connection.timeout", -10, save=False)
        mock_logger.warning.assert_called_once()

    def test_watcher_exception_handling(self):
        """ウォッチャーの例外処理"""
        def failing_watcher(key, old_value, new_value):
            raise Exception("Test exception")
        
        self.config_manager.add_watcher(failing_watcher)
        # 例外が発生しても設定は正常に完了する
        result = self.config_manager.set("connection.timeout", 60, save=False)
        self.assertTrue(result)


class TestModuleFunctions(unittest.TestCase):
    """モジュール関数のテスト"""

    def test_get_config_singleton(self):
        """グローバル設定インスタンスのシングルトン"""
        config1 = get_config()
        config2 = get_config()
        self.assertIs(config1, config2)

    @patch('msx_serial.common.config_manager._global_config')
    def test_get_setting(self, mock_global_config):
        """設定値の取得関数"""
        mock_global_config.get.return_value = "test_value"
        
        result = get_setting("test.key", "default")
        self.assertEqual(result, "test_value")
        mock_global_config.get.assert_called_once_with("test.key", "default")

    @patch('msx_serial.common.config_manager._global_config')
    def test_set_setting(self, mock_global_config):
        """設定値の設定関数"""
        mock_global_config.set.return_value = True
        
        result = set_setting("test.key", "test_value", save=False)
        self.assertTrue(result)
        mock_global_config.set.assert_called_once_with("test.key", "test_value", False)


if __name__ == "__main__":
    unittest.main() 