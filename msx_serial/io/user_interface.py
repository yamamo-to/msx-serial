"""
User interface coordinator for MSX terminal
"""

import logging
import threading
from typing import TYPE_CHECKING, Any, List, Optional, Protocol

from msx_serial.common.config_manager import ConfigManager

from ..commands.handler import CommandHandler
from ..connection.base import Connection
from ..display.basic_display import TerminalDisplay
from .data_sender import DataSender
from .input_session import InputSession

if TYPE_CHECKING:
    from ..transfer.file_transfer import FileTransferManager

logger = logging.getLogger(__name__)


class DataProcessor(Protocol):
    """データプロセッサーのプロトコル"""

    def set_last_command(self, command: str) -> None: ...


class Completer(Protocol):
    """補完機能のプロトコル"""

    def set_connection(self, connection: Connection) -> None: ...

    def set_current_directory(self, directory: str) -> None: ...

    @property
    def current_mode(self) -> str: ...

    @property
    def dos_completer(self) -> Any: ...


class DOSCompletionDebugger:
    """DOS補完機能のデバッグ用クラス"""

    def __init__(self, user_interface: "UserInterface") -> None:
        self.ui = user_interface

    def debug_completion(self, test_input: str) -> List:
        """DOSファイル補完のデバッグ"""
        from prompt_toolkit.completion import CompleteEvent
        from prompt_toolkit.document import Document

        self.ui.update_mode("dos")
        self.ui.update_dos_directory("A:\\")
        self._setup_test_files()

        completer = self.ui.input_session.completer
        self._log_debug_info(completer, test_input)

        document = Document(test_input)
        event = CompleteEvent()
        completions = list(completer.get_completions(document, event))

        logger.info(f"補完候補数: {len(completions)}")
        for comp in completions:
            logger.debug(f"  - {comp.text} ({comp.display_meta})")

        return completions

    def _setup_test_files(self) -> None:
        """テスト用ファイル情報を設定"""
        from ..completion.dos_filesystem import DOSFileInfo

        test_files = {
            "TEST.BAS": DOSFileInfo("TEST.BAS", False, 1024),
            "TEMP.TXT": DOSFileInfo("TEMP.TXT", False, 512),
            "TOOL.COM": DOSFileInfo("TOOL.COM", False, 2048),
            "GAMES": DOSFileInfo("GAMES", True),
            "UTILS": DOSFileInfo("UTILS", True),
        }
        self.ui.input_session.completer.dos_completer.filesystem_manager.set_test_files(
            "A:\\", test_files
        )

    def _log_debug_info(self, completer: Completer, test_input: str) -> None:
        """デバッグ情報をログ出力"""
        logger.debug(f"現在のモード: {self.ui.current_mode}")
        logger.debug(f"Completerの現在モード: {completer.current_mode}")
        logger.debug(
            f"DOSCompleterの接続: {completer.dos_completer.filesystem_manager.connection}"
        )
        logger.debug(
            f"DOSCompleterの現在ディレクトリ: {completer.dos_completer.filesystem_manager.current_directory}"
        )

        command_line = test_input.strip()
        command, args, arg_position = (
            completer.dos_completer.filesystem_manager.parse_dos_command_line(
                command_line
            )
        )
        ends_with_space = test_input.endswith(" ")

        logger.debug(f'入力: "{test_input}"')
        logger.debug(f'解析結果: command="{command}", args={args}, pos={arg_position}')
        logger.debug(f"末尾スペース: {ends_with_space}")


class UserInterface:
    """Coordinate user input, display, and command handling"""

    def __init__(
        self,
        prompt_style: str,
        connection: Connection,
        encoding: Optional[str] = None,
    ):
        """Initialize user interface components

        Args:
            prompt_style: Style for prompts
            connection: Connection to MSX
            encoding: Text encoding
        """
        self.encoding = encoding or ConfigManager().get("connection.encoding", "msx-jp")
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
        self.data_sender = DataSender(connection, self.encoding)
        self.debugger = DOSCompletionDebugger(self)

    def prompt(self) -> str:
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

        if self._has_completer():
            self.input_session.completer.set_connection(self.connection)

    def update_dos_directory(self, directory: str) -> None:
        """Update current DOS directory for completion

        Args:
            directory: Current DOS directory path
        """
        if self._has_completer():
            self.input_session.completer.set_current_directory(directory)

    def _has_completer(self) -> bool:
        """Completerが利用可能かチェック"""
        return (
            hasattr(self.input_session, "completer")
            and self.input_session.completer is not None
        )

    def _update_completer_mode(self) -> None:
        """Update completer mode (for compatibility)"""
        self.update_mode(self.current_mode)

    def set_data_processor(self, processor: DataProcessor) -> None:
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
            logger.info("DOSモードでない場合はファイルキャッシュ更新をスキップします")
            return False

        if not self._has_completer():
            logger.warning("Completerが初期化されていません")
            return False

        logger.info("DOSファイルキャッシュを更新中...")

        filesystem_manager = (
            self.input_session.completer.dos_completer.filesystem_manager
        )
        success = filesystem_manager.refresh_directory_cache_sync()

        if success:
            logger.info("DOSファイルキャッシュの更新が完了しました")
        else:
            logger.error("DOSファイルキャッシュの更新に失敗しました")

        return success

    def debug_dos_completion(self, test_input: str) -> List:
        """DOSファイル補完のデバッグ"""
        return self.debugger.debug_completion(test_input)
