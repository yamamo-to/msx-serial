from enum import Enum
from typing import Optional


class CommandType(Enum):
    """特殊コマンドの種類"""

    CD = ("@cd", "カレントディレクトリを変更します")
    ENCODE = ("@encode", "送受信時の文字コードを指定します")
    EXIT = ("@exit", "プログラムを終了します")
    HELP = ("@help", "コマンドのヘルプを表示します")
    PASTE = ("@paste", "ファイルを読み込んで送信します")
    UPLOAD = ("@upload", "ファイルをアップロードします")

    def __init__(self, value: tuple[str, str], description: str):
        self._value_ = value  # Enumのvalueとして使われる値
        self.description = description  # 説明テキストを属性として保持

    @classmethod
    def from_input(cls, user_input: str) -> Optional["CommandType"]:
        """ユーザー入力からコマンドタイプを取得"""
        for cmd in cls:
            if user_input.startswith(cmd.value):
                return cmd
        return None
