"""
DOSコマンド補完機能
"""

from pathlib import Path
from typing import Iterator
from prompt_toolkit.completion import Completion, CompleteEvent
from prompt_toolkit.document import Document
import yaml

from .base import BaseCompleter, CompletionContext


class DOSCompleter(BaseCompleter):
    """DOSコマンド補完を提供するクラス"""

    def __init__(self) -> None:
        super().__init__()
        self.dos_commands = self._load_dos_commands()

    def _load_dos_commands(self) -> list:
        """YAMLファイルからDOSコマンドを読み込み

        Returns:
            DOSコマンドのリスト
        """
        try:
            # パッケージのデータディレクトリを取得
            package_dir = Path(__file__).parent.parent.parent
            yaml_path = package_dir / "data" / "dos_commands.yml"

            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            return [(cmd["name"], cmd["description"]) for cmd in data["dos_commands"]]
        except Exception as e:
            # ファイル読み込みに失敗した場合は基本的なコマンドのみ
            print(f"DOSコマンドファイルの読み込みに失敗: {e}")
            return [
                ("BASIC", "MSX-BASICを起動"),
                ("DIR", "ディレクトリの内容を表示"),
                ("COPY", "ファイルをコピー"),
                ("DEL", "ファイルを削除"),
                ("REN", "ファイル名を変更"),
                ("TYPE", "ファイルの内容を表示"),
                ("CD", "ディレクトリを変更"),
                ("MD", "ディレクトリを作成"),
                ("RD", "ディレクトリを削除"),
                ("FORMAT", "ディスクをフォーマット"),
                ("CHKDSK", "ディスクの状態をチェック"),
                ("SYS", "システムファイルを転送"),
                ("DATE", "日付を設定"),
                ("TIME", "時刻を設定"),
                ("VER", "バージョンを表示"),
                ("CLS", "画面をクリア"),
                ("PROMPT", "プロンプトを設定"),
                ("PATH", "パスを設定"),
                ("SET", "環境変数を設定"),
                ("ECHO", "メッセージを表示"),
                ("PAUSE", "一時停止"),
                ("REM", "コメント"),
                ("BATCH", "バッチファイルを実行"),
                ("EXIT", "DOSを終了"),
                ("HELP", "ヘルプを表示"),
            ]

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterator[Completion]:
        context = CompletionContext(
            document.text_before_cursor,
            document.get_word_before_cursor(),
        )

        word = context.word.upper()

        for command, description in self.dos_commands:
            if command.startswith(word):
                yield Completion(
                    command,
                    start_position=-len(context.word),
                    display=command,
                    display_meta=description,
                )
