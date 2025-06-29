"""
DOSコマンド補完機能
"""

from pathlib import Path
from typing import Iterator, Optional

import yaml
from prompt_toolkit.completion import CompleteEvent, Completion
from prompt_toolkit.document import Document

from ..dos_filesystem import DOSFileSystemManager
from .base import BaseCompleter, CompletionContext


class DOSCompleter(BaseCompleter):
    """DOSコマンド補完を提供するクラス"""

    def __init__(self, connection: Optional[object] = None) -> None:
        super().__init__()
        self.dos_commands = self._load_dos_commands()
        self.filesystem_manager = DOSFileSystemManager(connection)
        self._background_refresh_enabled = True

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
            print(f"DOS commands YAML load failed: {e}")
            print(f"Attempting to load from: {yaml_path}")
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

    def set_connection(self, connection: object) -> None:
        """接続オブジェクトを設定"""
        self.filesystem_manager.set_connection(connection)

    def set_current_directory(self, directory: str) -> None:
        """現在のディレクトリを設定"""
        self.filesystem_manager.set_current_directory(directory)

    def _trigger_background_refresh(self) -> None:
        """バックグラウンドでディレクトリキャッシュを更新"""
        # 自動的なDIRコマンド実行を無効化
        # DIRコマンド実行時に自動的にキャッシュが更新される
        pass

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterator[Completion]:
        context = CompletionContext(
            document.text_before_cursor,
            document.get_word_before_cursor(),
        )

        # DOSコマンドラインを解析
        command_line = document.text_before_cursor
        command, args, arg_position = self.filesystem_manager.parse_dos_command_line(
            command_line
        )

        # デバッグ情報（必要時のみ有効化）
        # print("DOSCompleter デバッグ:")
        # print(f"  command_line: '{command_line}'")
        # print(f"  command: '{command}'")
        # print(f"  args: {args}")
        # print(f"  arg_position: {arg_position}")

        # コマンド名の補完（引数がない場合）
        if not command or (not args and not document.text_before_cursor.endswith(" ")):
            word = context.word.upper()

            # DOSコマンドの補完
            for cmd, description in self.dos_commands:
                if cmd.startswith(word):
                    yield Completion(
                        cmd,
                        start_position=-len(context.word),
                        display=cmd,
                        display_meta=description,
                    )

            # ファイル補完も必ず呼ぶ
            self._trigger_background_refresh()
            file_completions = self.filesystem_manager.get_completions_for_command(
                "", word, 0
            )
            for completion_text, description in file_completions:
                display_text = completion_text.rstrip("\\")
                yield Completion(
                    display_text,
                    start_position=-len(context.word),
                    display=display_text,
                    display_meta=description,
                )
            return

        # ファイル名補完（引数がある場合）
        if command and (args or document.text_before_cursor.endswith(" ")):
            # バックグラウンドでキャッシュ更新を試行
            self._trigger_background_refresh()

            # ファイル補完候補を取得
            current_word = context.word if not command_line.endswith(" ") else ""
            file_completions = self.filesystem_manager.get_completions_for_command(
                command, current_word, arg_position - 1 if args else 0
            )

            for completion_text, description in file_completions:
                # ディレクトリの場合は末尾の\を除いて補完候補とする
                display_text = completion_text.rstrip("\\")
                yield Completion(
                    display_text,
                    start_position=-len(current_word),
                    display=display_text,
                    display_meta=description,
                )
