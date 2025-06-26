"""
高度な設定管理システム
"""

import json
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import yaml

logger = logging.getLogger(__name__)


class ConfigFormat(Enum):
    """設定ファイル形式"""

    JSON = "json"
    YAML = "yaml"
    TOML = "toml"


@dataclass
class ConfigSchema:
    """設定スキーマ定義"""

    key: str
    default_value: Any
    description: str
    value_type: type
    required: bool = False
    choices: Optional[List[Any]] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None

    def validate(self, value: Any) -> bool:
        """値の妥当性を検証"""
        if value is None and self.required:
            return False

        if value is not None:
            # 型チェック
            if not isinstance(value, self.value_type):
                try:
                    value = self.value_type(value)
                except (ValueError, TypeError):
                    return False

            # 選択肢チェック
            if self.choices and value not in self.choices:
                return False

            # 範囲チェック
            if isinstance(value, (int, float)):
                if self.min_value is not None and value < self.min_value:
                    return False
                if self.max_value is not None and value > self.max_value:
                    return False

        return True


class ConfigManager:
    """高度な設定管理クラス"""

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.home() / ".msx-serial"
        self.config_dir.mkdir(exist_ok=True)

        self.config_file = self.config_dir / "config.yaml"
        self.schema: Dict[str, ConfigSchema] = {}
        self.config_data: Dict[str, Any] = {}
        self.watchers: List[Callable] = []

        # デフォルトスキーマを定義
        self._define_default_schema()

        # 設定を読み込み
        self.load_config()

    def _define_default_schema(self) -> None:
        """デフォルトスキーマを定義"""
        schemas = [
            ConfigSchema(
                "connection.timeout",
                30,
                "接続タイムアウト（秒）",
                int,
                min_value=1,
                max_value=300,
            ),
            ConfigSchema(
                "connection.retry_count",
                3,
                "接続リトライ回数",
                int,
                min_value=0,
                max_value=10,
            ),
            ConfigSchema("display.color_enabled", True, "カラー表示を有効化", bool),
            ConfigSchema("display.optimization", True, "表示最適化を有効化", bool),
            ConfigSchema(
                "display.buffer_size",
                8192,
                "表示バッファサイズ",
                int,
                min_value=1024,
                max_value=65536,
            ),
            ConfigSchema(
                "performance.profiling_enabled", False, "プロファイリングを有効化", bool
            ),
            ConfigSchema(
                "performance.max_history",
                1000,
                "パフォーマンス履歴の最大数",
                int,
                min_value=100,
                max_value=10000,
            ),
            ConfigSchema(
                "logging.level",
                "INFO",
                "ログレベル",
                str,
                choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            ),
            ConfigSchema("logging.file_enabled", False, "ファイルログを有効化", bool),
            ConfigSchema(
                "completion.cache_enabled", True, "補完キャッシュを有効化", bool
            ),
            ConfigSchema(
                "completion.cache_size",
                1000,
                "補完キャッシュサイズ",
                int,
                min_value=100,
                max_value=10000,
            ),
            ConfigSchema(
                "transfer.chunk_size",
                1024,
                "転送チャンクサイズ",
                int,
                min_value=256,
                max_value=8192,
            ),
            ConfigSchema(
                "transfer.progress_enabled", True, "転送進捗表示を有効化", bool
            ),
        ]

        for schema in schemas:
            self.register_schema(schema)

    def register_schema(self, schema: ConfigSchema) -> None:
        """スキーマを登録"""
        self.schema[schema.key] = schema

    def get(self, key: str, default: Any = None) -> Any:
        """設定値を取得"""
        if key in self.config_data:
            return self.config_data[key]

        if key in self.schema:
            return self.schema[key].default_value

        return default

    def set(self, key: str, value: Any, save: bool = True) -> bool:
        """設定値を設定"""
        if key in self.schema:
            if not self.schema[key].validate(value):
                logger.warning(f"Invalid value for {key}: {value}")
                return False

        old_value = self.config_data.get(key)
        self.config_data[key] = value

        if save:
            self.save_config()

        # 変更通知
        self._notify_watchers(key, old_value, value)
        return True

    def get_nested(self, key: str, default: Any = None) -> Any:
        """ネストされたキーで設定値を取得（例: "connection.timeout"）"""
        keys = key.split(".")
        value = self.config_data

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return self.get(key, default)

        return value

    def set_nested(self, key: str, value: Any, save: bool = True) -> bool:
        """ネストされたキーで設定値を設定"""
        keys = key.split(".")
        config = self.config_data

        # ネストされた辞書を作成
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        return self.set(key, value, save)

    def load_config(self, config_file: Optional[Path] = None) -> bool:
        """設定ファイルを読み込み"""
        file_path = config_file or self.config_file

        if not file_path.exists():
            logger.info(f"Config file not found: {file_path}")
            return False

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                if file_path.suffix.lower() == ".json":
                    self.config_data = json.load(f)
                else:
                    self.config_data = yaml.safe_load(f) or {}

            logger.info(f"Config loaded from: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return False

    def save_config(self, config_file: Optional[Path] = None) -> bool:
        """設定ファイルを保存"""
        file_path = config_file or self.config_file

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    self.config_data, f, default_flow_style=False, allow_unicode=True
                )

            logger.info(f"Config saved to: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False

    def reset_to_defaults(self) -> None:
        """設定をデフォルト値にリセット"""
        self.config_data.clear()
        for key, schema in self.schema.items():
            if schema.default_value is not None:
                self.config_data[key] = schema.default_value

    def validate_all(self) -> Dict[str, List[str]]:
        """全設定の妥当性を検証"""
        errors: Dict[str, List[str]] = {}

        for key, schema in self.schema.items():
            value = self.get(key)
            if not schema.validate(value):
                if key not in errors:
                    errors[key] = []
                errors[key].append(f"Invalid value: {value}")

        return errors

    def add_watcher(self, callback: Callable) -> None:
        """設定変更の監視コールバックを追加"""
        self.watchers.append(callback)

    def remove_watcher(self, callback: Callable) -> None:
        """設定変更の監視コールバックを削除"""
        if callback in self.watchers:
            self.watchers.remove(callback)

    def _notify_watchers(self, key: str, old_value: Any, new_value: Any) -> None:
        """設定変更を監視者に通知"""
        for watcher in self.watchers:
            try:
                watcher(key, old_value, new_value)
            except Exception as e:
                logger.error(f"Watcher error: {e}")

    def get_schema_info(self) -> Dict[str, Dict[str, Any]]:
        """スキーマ情報を取得"""
        info = {}
        for key, schema in self.schema.items():
            info[key] = {
                "description": schema.description,
                "type": schema.value_type.__name__,
                "default": schema.default_value,
                "required": schema.required,
                "choices": schema.choices,
                "min_value": schema.min_value,
                "max_value": schema.max_value,
                "current_value": self.get(key),
            }
        return info


# グローバル設定マネージャー
_global_config = ConfigManager()


def get_config() -> ConfigManager:
    """グローバル設定マネージャーを取得"""
    return _global_config


def get_setting(key: str, default: Any = None) -> Any:
    """設定値を取得（簡易版）"""
    return _global_config.get(key, default)


def set_setting(key: str, value: Any, save: bool = True) -> bool:
    """設定値を設定（簡易版）"""
    return _global_config.set(key, value, save)
