"""
User interface coordinator for MSX terminal
"""

import threading
from typing import TYPE_CHECKING, Any

from ..commands.handler import CommandHandler
from ..connection.base import Connection
from ..display.basic_display import TerminalDisplay
from .data_sender import DataSender
from .input_session import InputSession

if TYPE_CHECKING:
    from ..transfer.file_transfer import FileTransferManager


class UserInterface:
    """Coordinate user input, display, and command handling"""

    def __init__(
        self,
        prompt_style: str,
        encoding: str,
        connection: Connection,
    ):
        """Initialize user interface components

        Args:
            prompt_style: Style for prompts
            encoding: Text encoding
            connection: Connection to MSX
        """
        self.encoding = encoding
        self.current_mode = "unknown"
        self.prompt_detected = False
        self.terminal = None  # Reference to main terminal
        self.connection = connection  # Store connection for later use

        # Initialize components
        self.display = TerminalDisplay()
        self.input_session = InputSession(prompt_style, self.current_mode, connection)
        self.command_handler = CommandHandler(
            self.input_session.style, self.current_mode
        )
        self.data_sender = DataSender(connection, encoding)

    def prompt(self) -> Any:
        """Get user input

        Returns:
            User input
        """
        return self.input_session.prompt()

    def send(self, user_input: str) -> None:
        """Send user input to MSX

        Args:
            user_input: User input to send
        """
        self.data_sender.send(user_input)

    def print_receive(self, text: str, is_prompt: bool = False) -> None:
        """Display received data

        Args:
            text: Text to display
            is_prompt: Whether this is a prompt line
        """
        self.display.print_receive(text, is_prompt)

    def clear_screen(self) -> None:
        """Clear terminal screen"""
        self.display.clear_screen()

    def handle_special_commands(
        self,
        user_input: str,
        file_transfer: "FileTransferManager",
        stop_event: threading.Event,
    ) -> bool:
        """Handle special commands

        Args:
            user_input: User input
            file_transfer: File transfer manager
            stop_event: Stop event

        Returns:
            True if special command was processed
        """
        return self.command_handler.handle_special_commands(
            user_input, file_transfer, stop_event, terminal=self.terminal
        )

    def update_mode(self, mode: str) -> None:
        """Update current mode

        Args:
            mode: New mode
        """
        self.current_mode = mode
        self.input_session.update_mode(mode)
        self.command_handler.current_mode = mode

        # 確実にCompleterに接続オブジェクトを設定
        if hasattr(self.input_session, "completer") and self.input_session.completer:
            self.input_session.completer.set_connection(self.connection)

    def update_dos_directory(self, directory: str) -> None:
        """Update current DOS directory for completion

        Args:
            directory: Current DOS directory path
        """
        if hasattr(self.input_session, "completer") and self.input_session.completer:
            self.input_session.completer.set_current_directory(directory)

    def _update_completer_mode(self) -> None:
        """Update completer mode (for compatibility)"""
        self.update_mode(self.current_mode)

    def set_data_processor(self, processor: object) -> None:
        """Set data processor for echo detection

        Args:
            processor: DataProcessor instance
        """
        self.data_sender.set_data_processor(processor)

    def refresh_dos_cache(self) -> bool:
        """DOSファイルシステムキャッシュを手動で更新

        Returns:
            更新成功かどうか
        """
        if self.current_mode != "dos":
            print("DOSモードでない場合はファイルキャッシュ更新をスキップします")
            return False

        if (
            not hasattr(self.input_session, "completer")
            or not self.input_session.completer
        ):
            print("Completerが初期化されていません")
            return False

        print("DOSファイルキャッシュを更新中...")

        # DOSFileSystemManagerのキャッシュ更新を実行
        filesystem_manager = (
            self.input_session.completer.dos_completer.filesystem_manager
        )
        success = filesystem_manager.refresh_directory_cache_sync()

        if success:
            print("DOSファイルキャッシュの更新が完了しました")
        else:
            print("DOSファイルキャッシュの更新に失敗しました")

        return success

    def debug_dos_completion(self, test_input: str) -> list:
        """DOSファイル補完のデバッグ用メソッド

        Args:
            test_input: テスト用入力文字列

        Returns:
            補完候補のリスト
        """
        from prompt_toolkit.completion import CompleteEvent
        from prompt_toolkit.document import Document

        # DOSモードに設定
        self.update_mode("dos")

        # テスト用ダミーディレクトリ設定
        self.update_dos_directory("A:\\")

        # テスト用ファイル情報を設定
        from ..completion.dos_filesystem import DOSFileInfo

        test_files = {
            "TEST.BAS": DOSFileInfo("TEST.BAS", False, 1024),
            "TEMP.TXT": DOSFileInfo("TEMP.TXT", False, 512),
            "TOOL.COM": DOSFileInfo("TOOL.COM", False, 2048),
            "GAMES": DOSFileInfo("GAMES", True),
            "UTILS": DOSFileInfo("UTILS", True),
        }
        self.input_session.completer.dos_completer.filesystem_manager.set_test_files(
            "A:\\", test_files
        )

        # 現在の補完機能の状態をチェック
        completer = self.input_session.completer
        print("デバッグ情報:")
        print(f"  現在のモード: {self.current_mode}")
        print(f"  Completerの現在モード: {completer.current_mode}")
        print(
            f"  DOSCompleterの接続: {completer.dos_completer.filesystem_manager.connection}"
        )
        print(
            f"  DOSCompleterの現在ディレクトリ: {completer.dos_completer.filesystem_manager.current_directory}"
        )

        # DOSコマンドライン解析のテスト
        command_line = test_input.strip()
        command, args, arg_position = (
            completer.dos_completer.filesystem_manager.parse_dos_command_line(
                command_line
            )
        )
        ends_with_space = test_input.endswith(" ")
        print(f'  入力: "{test_input}"')
        print(f'  解析結果: command="{command}", args={args}, pos={arg_position}')
        print(f"  末尾スペース: {ends_with_space}")

        # 条件判断
        condition1 = not command or (not args and not ends_with_space)
        condition2 = command and (args or ends_with_space)
        print(f"  条件1（コマンド名補完）: {condition1}")
        print(f"  条件2（ファイル名補完）: {condition2}")

        # 補完テスト実行
        document = Document(test_input)
        event = CompleteEvent()

        completions = list(completer.get_completions(document, event))

        print(f"  補完候補数: {len(completions)}")
        for comp in completions:
            print(f"    - {comp.text} ({comp.display_meta})")

        return completions
