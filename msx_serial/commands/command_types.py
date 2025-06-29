"""Command types for MSX terminal"""

from enum import Enum
from typing import Optional


class CommandType(Enum):
    """Special command types"""

    HELP = ("@help", "ヘルプを表示します")
    EXIT = ("@exit", "プログラムを終了します")
    PASTE = ("@paste", "ファイルをBASICプログラムとして貼り付けます")
    UPLOAD = ("@upload", "ファイルをBASICプログラムとしてアップロードします")
    MODE = ("@mode", "MSXモードを表示/変更します")
    ENCODE = ("@encode", "テキストエンコーディングを設定します")
    PERF = ("@perf", "パフォーマンス統計を表示します")
    CD = ("@cd", "現在のディレクトリを変更します")
    CONFIG = ("@config", "設定を管理します")

    def __init__(self, command: str, description: str):
        self.command = command
        self.description = description

    @property
    def value(self) -> tuple[str, str]:  # type: ignore[override]
        """コマンド情報のタプルを返す"""
        return (self.command, self.description)

    @property
    def command_str(self) -> str:
        """コマンド文字列を返す"""
        return self.command

    @classmethod
    def from_input(cls, user_input: str) -> Optional["CommandType"]:
        """ユーザー入力からコマンドタイプを取得"""
        for cmd in cls:
            if user_input.startswith(cmd.command):
                return cmd
        return None
