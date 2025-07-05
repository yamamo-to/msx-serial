"""
ConfigManagerのテスト
"""

import tempfile
import unittest
from pathlib import Path
from typing import Any

from msx_serial.common.config_manager import (ConfigManager, ConfigSchema,
                                              get_config, get_setting,
                                              set_setting)


class TestConfigSchema(unittest.TestCase):
    """ConfigSchemaのテスト"""

    def test_init(self):
        schema = ConfigSchema(
            key="test.key",
            default_value="default",
            description="Test description",
            value_type=str,
        )

        self.assertEqual(schema.key, "test.key")
        self.assertEqual(schema.default_value, "default")
        self.assertEqual(schema.description, "Test description")
        self.assertEqual(schema.value_type, str)
        self.assertFalse(schema.required)
        self.assertIsNone(schema.choices)
        self.assertIsNone(schema.min_value)
        self.assertIsNone(schema.max_value)

    def test_validate_required_field(self):
        # 必須フィールドのテスト
        required_schema = ConfigSchema(
            key="required.key",
            default_value="default",
            description="Required field",
            value_type=str,
            required=True,
        )

        self.assertFalse(required_schema.validate(None))
        self.assertTrue(required_schema.validate("value"))

    def test_validate_type_conversion(self):
        # 型変換のテスト
        int_schema = ConfigSchema(
            key="int.key", default_value=42, description="Integer field", value_type=int
        )

        self.assertTrue(int_schema.validate(42))
        self.assertTrue(int_schema.validate("42"))  # 文字列から変換
        self.assertFalse(int_schema.validate("invalid"))

    def test_validate_choices(self):
        # 選択肢のテスト
        choice_schema = ConfigSchema(
            key="choice.key",
            default_value="option1",
            description="Choice field",
            value_type=str,
            choices=["option1", "option2", "option3"],
        )

        self.assertTrue(choice_schema.validate("option1"))
        self.assertTrue(choice_schema.validate("option2"))
        self.assertFalse(choice_schema.validate("invalid_option"))

    def test_validate_range(self):
        # 範囲のテスト
        range_schema = ConfigSchema(
            key="range.key",
            default_value=5,
            description="Range field",
            value_type=int,
            min_value=1,
            max_value=10,
        )

        self.assertTrue(range_schema.validate(5))
        self.assertTrue(range_schema.validate(1))  # 最小値
        self.assertTrue(range_schema.validate(10))  # 最大値
        self.assertFalse(range_schema.validate(0))  # 最小値未満
        self.assertFalse(range_schema.validate(11))  # 最大値超過


class TestConfigManager(unittest.TestCase):
    """ConfigManagerのテスト"""

    def setUp(self):
        """テスト前の準備"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_manager = ConfigManager(self.temp_dir)

    def tearDown(self):
        """テスト後のクリーンアップ"""
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_init(self):
        """ConfigManagerの初期化テスト"""
        self.assertEqual(self.config_manager.config_dir, self.temp_dir)
        self.assertIsNotNone(self.config_manager.schema)
        self.assertIsInstance(self.config_manager.config_data, dict)

    def test_register_schema(self):
        """スキーマ登録のテスト"""
        test_schema = ConfigSchema(
            key="test.new_setting",
            default_value="test_value",
            description="Test setting",
            value_type=str,
        )

        self.config_manager.register_schema(test_schema)
        self.assertIn("test.new_setting", self.config_manager.schema)
        self.assertEqual(self.config_manager.get("test.new_setting"), "test_value")

    def test_get_set_basic(self):
        """基本的な設定の取得・設定テスト"""
        # 設定の取得
        value = self.config_manager.get("display.theme")
        self.assertIsNotNone(value)

        # 設定の変更（有効な選択肢を使用）
        result = self.config_manager.set("display.theme", "matrix")
        self.assertTrue(result)
        self.assertEqual(self.config_manager.get("display.theme"), "matrix")

    def test_get_with_default(self):
        """デフォルト値付き取得のテスト"""
        # 存在しないキーの場合
        value = self.config_manager.get("nonexistent.key", "default_value")
        self.assertEqual(value, "default_value")

    def test_set_invalid_value(self):
        """無効な値の設定テスト"""
        # 選択肢にない値を設定
        result = self.config_manager.set("display.theme", "invalid_theme")
        self.assertFalse(result)

    def test_get_nested(self):
        """ネストした設定の取得テスト"""
        # ネストした設定をテスト用に追加
        nested_schema = ConfigSchema(
            key="nested.deep.setting",
            default_value="nested_value",
            description="Nested setting",
            value_type=str,
        )
        self.config_manager.register_schema(nested_schema)

        value = self.config_manager.get_nested("nested.deep.setting")
        self.assertEqual(value, "nested_value")

    def test_set_nested(self):
        """ネストした設定の設定テスト"""
        # ネストした設定をテスト用に追加
        nested_schema = ConfigSchema(
            key="nested.test.setting",
            default_value="original",
            description="Nested test setting",
            value_type=str,
        )
        self.config_manager.register_schema(nested_schema)

        result = self.config_manager.set_nested("nested.test.setting", "new_value")
        self.assertTrue(result)
        self.assertEqual(
            self.config_manager.get_nested("nested.test.setting"), "new_value"
        )

    def test_load_config_file_not_found(self):
        """存在しない設定ファイルの読み込みテスト"""
        nonexistent_file = self.temp_dir / "nonexistent.yaml"
        result = self.config_manager.load_config(nonexistent_file)
        self.assertFalse(result)

    def test_save_load_config(self):
        """設定の保存・読み込みテスト"""
        # 設定を変更（有効な選択肢を使用）
        self.config_manager.set("display.theme", "matrix")

        # 設定を保存
        config_file = self.temp_dir / "test_config.yaml"
        result = self.config_manager.save_config(config_file)
        self.assertTrue(result)
        self.assertTrue(config_file.exists())

        # 新しいConfigManagerで読み込み
        new_manager = ConfigManager(self.temp_dir)
        result = new_manager.load_config(config_file)
        self.assertTrue(result)
        self.assertEqual(new_manager.get("display.theme"), "matrix")

    def test_reset_to_defaults(self):
        """デフォルト値へのリセットテスト"""
        # 設定を変更
        original_theme = self.config_manager.get("display.theme")
        self.config_manager.set("display.theme", "matrix")

        # デフォルトにリセット
        self.config_manager.reset_to_defaults()

        # デフォルト値に戻っていることを確認
        reset_theme = self.config_manager.get("display.theme")
        self.assertEqual(reset_theme, original_theme)

    def test_validate_all(self):
        """全設定検証のテスト"""
        # 正常な状態での検証
        errors = self.config_manager.validate_all()
        self.assertEqual(len(errors), 0)

    def test_save_config_default_path(self):
        """デフォルトパスでの設定保存テスト"""
        self.config_manager.set("display.theme", "matrix")

        result = self.config_manager.save_config()
        self.assertTrue(result)

    def test_load_config_default_path(self):
        """デフォルトパスでの設定読み込みテスト"""
        # まず設定を保存
        self.config_manager.set("display.theme", "matrix")
        self.config_manager.save_config()

        # 設定をリセット
        self.config_manager.reset_to_defaults()

        # デフォルトパスから読み込み
        result = self.config_manager.load_config()
        self.assertTrue(result)

    def test_generate_sample_config_default_path(self):
        """サンプル設定ファイル生成（デフォルトパス）のテスト"""
        result = self.config_manager.generate_sample_config()
        assert result is True

        sample_file = self.temp_dir / "config.sample.yaml"
        assert sample_file.exists()

        content = sample_file.read_text()
        assert "MSX Serial Terminal Configuration" in content
        assert "display:" in content
        assert "performance:" in content

    def test_generate_sample_config_custom_path(self):
        """サンプル設定ファイル生成（カスタムパス）のテスト"""
        custom_path = self.temp_dir / "custom_sample.yaml"

        result = self.config_manager.generate_sample_config(custom_path)
        assert result is True
        assert custom_path.exists()

    def test_generate_sample_config_failure(self):
        """サンプル設定ファイル生成失敗のテスト"""
        # 存在しないディレクトリに出力しようとする
        invalid_path = self.temp_dir / "nonexistent" / "config.sample.yaml"

        result = self.config_manager.generate_sample_config(invalid_path)
        assert result is False

    def test_export_current_config_default_path(self):
        """現在の設定エクスポート（デフォルトパス）のテスト"""
        self.config_manager.set("display.theme", "matrix")

        result = self.config_manager.export_current_config()
        assert result is True

        export_file = self.temp_dir / "config.export.yaml"
        assert export_file.exists()

    def test_export_current_config_custom_path(self):
        """現在の設定エクスポート（カスタムパス）のテスト"""
        custom_path = self.temp_dir / "custom_export.yaml"

        result = self.config_manager.export_current_config(custom_path)
        assert result is True
        assert custom_path.exists()

    def test_export_current_config_failure(self):
        """現在の設定エクスポート失敗のテスト"""
        # 存在しないディレクトリに出力しようとする
        invalid_path = self.temp_dir / "nonexistent" / "config.export.yaml"

        result = self.config_manager.export_current_config(invalid_path)
        assert result is False

    def test_list_settings(self):
        """設定項目一覧のテスト"""
        settings = self.config_manager.list_settings()

        assert isinstance(settings, dict)
        assert "display" in settings
        assert "performance" in settings

        # 各カテゴリに設定項目が含まれている
        for category, items in settings.items():
            assert len(items) > 0
            for key, info in items.items():
                assert "value" in info
                assert "type" in info
                assert "description" in info
                assert "default" in info

    def test_export_config_exclude_defaults(self):
        """設定エクスポート（デフォルト値除外）のテスト"""
        self.config_manager.set("display.theme", "matrix")  # デフォルトから変更

        # デフォルト値を除外してエクスポート
        export_data = self.config_manager.export_config(include_defaults=False)

        assert "display.theme" in export_data
        assert export_data["display.theme"] == "matrix"

        # デフォルト値のまま変更していない設定は含まれないことを確認
        unchanged_keys = [
            k
            for k, v in export_data.items()
            if v == self.config_manager.schema[k].default_value
        ]
        # 変更していない設定がエクスポートに含まれていないことを確認
        assert len(unchanged_keys) == 0 or all(
            self.config_manager.get(k) != self.config_manager.schema[k].default_value
            for k in unchanged_keys
        )

    def test_export_config_include_defaults(self):
        """設定エクスポート（デフォルト値含む）のテスト"""
        # デフォルト値も含めてエクスポート
        export_data = self.config_manager.export_config(include_defaults=True)

        # 全ての設定項目が含まれている
        assert len(export_data) == len(self.config_manager.schema)

        for key in self.config_manager.schema:
            assert key in export_data

    def test_watchers_functionality(self):
        """設定変更監視機能のテスト"""
        # 監視コールバックの結果を記録
        watcher_calls = []

        def test_watcher(key: str, old_value: Any, new_value: Any):
            watcher_calls.append((key, old_value, new_value))

        # 監視者を追加
        self.config_manager.add_watcher(test_watcher)

        # 設定を変更
        self.config_manager.set("display.theme", "matrix")

        # 監視者が呼ばれたことを確認
        assert len(watcher_calls) == 1
        # old_valueの値に関わらず、変更が通知されたことを確認
        key, old_val, new_val = watcher_calls[0]
        assert key == "display.theme"
        assert new_val == "matrix"

        # 監視者を削除
        self.config_manager.remove_watcher(test_watcher)

        # 設定を変更しても監視者が呼ばれないことを確認
        self.config_manager.set("display.theme", "classic")
        assert len(watcher_calls) == 1  # 変化なし

    def test_watcher_error_handling(self):
        """監視者エラーハンドリングのテスト"""

        def error_watcher(key: str, old_value: Any, new_value: Any):
            raise ValueError("Test error")

        self.config_manager.add_watcher(error_watcher)

        # エラーが発生しても設定変更は成功する
        result = self.config_manager.set("display.theme", "matrix")
        assert result is True

    def test_validate_all_with_errors(self):
        """エラーありの全設定検証のテスト"""
        # 正常な設定の場合
        errors = self.config_manager.validate_all()
        assert len(errors) == 0

        # 無効な値を直接設定
        self.config_manager.config_data["display.theme"] = "invalid_theme"

        errors = self.config_manager.validate_all()
        assert len(errors) > 0
        assert "display.theme" in errors

    def test_get_schema_info_complete(self):
        """スキーマ情報取得の完全テスト"""
        schema_info = self.config_manager.get_schema_info()

        # 全ての登録されたスキーマの情報が含まれている
        assert len(schema_info) == len(self.config_manager.schema)

        for key, info in schema_info.items():
            assert "description" in info
            assert "type" in info
            assert "default" in info
            assert "required" in info
            assert "choices" in info
            assert "min_value" in info
            assert "max_value" in info
            assert "current_value" in info

            # 現在の値が正しく取得されている
            assert info["current_value"] == self.config_manager.get(key)

    def test_remove_nonexistent_watcher(self):
        """存在しない監視者の削除テスト"""

        def dummy_watcher(key: str, old_value: Any, new_value: Any):
            pass

        # 存在しない監視者を削除してもエラーにならない
        self.config_manager.remove_watcher(dummy_watcher)

        # 正常に動作することを確認
        self.config_manager.set("display.theme", "matrix")

    def test_schema_info_with_constraints(self):
        """制約付きスキーマ情報のテスト"""
        # 制約付きのスキーマを追加
        test_schema = ConfigSchema(
            key="test.constrained",
            default_value=5,
            description="Test constrained value",
            value_type=int,
            choices=[1, 5, 10],
            min_value=1,
            max_value=10,
        )
        self.config_manager.register_schema(test_schema)

        schema_info = self.config_manager.get_schema_info()
        constrained_info = schema_info["test.constrained"]

        assert constrained_info["choices"] == [1, 5, 10]
        assert constrained_info["min_value"] == 1
        assert constrained_info["max_value"] == 10


class TestModuleFunctions(unittest.TestCase):
    """モジュールレベルの関数のテスト"""

    def test_get_config(self):
        """get_config関数のテスト"""
        config = get_config()
        self.assertIsInstance(config, ConfigManager)

    def test_get_setting(self):
        """get_setting関数のテスト"""
        # 存在する設定
        value = get_setting("display.theme")
        self.assertIsNotNone(value)

        # 存在しない設定（デフォルト値あり）
        value = get_setting("nonexistent.key", "default")
        self.assertEqual(value, "default")

    def test_set_setting(self):
        """set_setting関数のテスト"""
        original_value = get_setting("display.theme")

        # 設定を変更（有効な選択肢を使用）
        result = set_setting("display.theme", "matrix")
        self.assertTrue(result)
        self.assertEqual(get_setting("display.theme"), "matrix")

        # 元に戻す
        set_setting("display.theme", original_value)

    def test_load_config_json_file(self):
        """Test loading JSON config file"""
        config_manager = ConfigManager()

        # 一時的なJSONファイルを作成
        import json
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"test.key": "test_value"}, f)
            temp_file = f.name

        try:
            result = config_manager.load_config(Path(temp_file))
            assert result is True
            assert config_manager.get("test.key") == "test_value"
        finally:
            Path(temp_file).unlink()

    def test_load_config_file_not_found(self):
        """Test loading config when file doesn't exist"""
        config_manager = ConfigManager()

        result = config_manager.load_config(Path("/nonexistent/config.yaml"))
        assert result is False

    def test_load_config_exception(self):
        """Test loading config with exception"""
        config_manager = ConfigManager()

        # 無効なYAMLファイルを作成
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_file = f.name

        try:
            result = config_manager.load_config(Path(temp_file))
            assert result is False
        finally:
            Path(temp_file).unlink()

    def test_save_config_exception(self):
        """Test saving config with exception"""
        config_manager = ConfigManager()

        # 読み取り専用ディレクトリに保存を試行
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            # ディレクトリを読み取り専用にする
            os.chmod(temp_dir, 0o444)

            try:
                result = config_manager.save_config(Path(temp_dir) / "config.yaml")
                assert result is False
            finally:
                # 権限を戻す
                os.chmod(temp_dir, 0o755)

    def test_remove_watcher_not_found(self):
        """Test removing watcher that doesn't exist"""
        config_manager = ConfigManager()

        def dummy_watcher(key, old_value, new_value):
            pass

        # 存在しないwatcherを削除しても例外が発生しないことを確認
        config_manager.remove_watcher(dummy_watcher)

    def test_notify_watchers_exception(self):
        """Test notifying watchers with exception"""
        config_manager = ConfigManager()

        def failing_watcher(key, old_value, new_value):
            raise Exception("Test error")

        config_manager.add_watcher(failing_watcher)

        # 例外が発生しても他の処理に影響しないことを確認
        config_manager._notify_watchers("test.key", "old", "new")

    def test_generate_sample_config_exception(self):
        """Test generating sample config with exception"""
        config_manager = ConfigManager()

        # 読み取り専用ディレクトリに保存を試行
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            # ディレクトリを読み取り専用にする
            os.chmod(temp_dir, 0o444)

            try:
                result = config_manager.generate_sample_config(
                    Path(temp_dir) / "sample.yaml"
                )
                assert result is False
            finally:
                # 権限を戻す
                os.chmod(temp_dir, 0o755)

    def test_export_current_config_exception(self):
        """Test exporting current config with exception"""
        config_manager = ConfigManager()

        # 読み取り専用ディレクトリに保存を試行
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            # ディレクトリを読み取り専用にする
            os.chmod(temp_dir, 0o444)

            try:
                result = config_manager.export_current_config(
                    Path(temp_dir) / "export.yaml"
                )
                assert result is False
            finally:
                # 権限を戻す
                os.chmod(temp_dir, 0o755)


if __name__ == "__main__":
    unittest.main()
