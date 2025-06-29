"""Command types for MSX terminal"""

from enum import Enum
from typing import Optional


class CommandType(Enum):
    """特殊コマンドの種類"""

    CD = ("@cd", "カレントディレクトリを変更します")
    ENCODE = ("@encode", "送受信時の文字コードを指定します")
    EXIT = ("@exit", "プログラムを終了します")
    HELP = ("@help", "コマンドのヘルプを表示します")
    MODE = ("@mode", "MSXモードを表示または強制変更します")
    PASTE = ("@paste", "ファイルを読み込んで送信します")
    UPLOAD = ("@upload", "ファイルをアップロードします")
    CONFIG = ("@config", "設定を表示・変更します")  # 新しい設定管理コマンド
    REFRESH = ("@refresh", "DOSファイル補完キャッシュを更新します")

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
