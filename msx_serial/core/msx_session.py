"""
Optimized MSX terminal session with instant response
"""

import threading
import time
from typing import Optional

import msx_charset  # noqa: F401  # type: ignore

from ..common.color_output import print_exception, print_info
from ..common.config_manager import get_setting
from ..connection.base import Connection
from ..display.enhanced_display import EnhancedTerminalDisplay
from ..io.user_interface import UserInterface
from ..protocol.msx_detector import MSXMode, MSXProtocolDetector
from ..transfer.file_transfer import FileTransferManager
from .data_processor import DataProcessor


class MSXSession:
    """高速応答最適化されたMSXターミナルセッション"""

    def __init__(
        self,
        connection: Connection,
        encoding: Optional[str] = None,
        prompt_style: Optional[str] = None,
        debug: bool = False,
        instant_mode: bool = False,
    ):
        """Initialize optimized terminal session

        Args:
            connection: Connection object
            encoding: Text encoding (None to use config default)
            prompt_style: Prompt styling (None to use config default)
            debug: Whether to enable debug mode
            instant_mode: Whether to use instant mode
        """
        # 設定から値を取得（引数が指定されていない場合）
        self.encoding = encoding or get_setting("encoding.default", "msx-jp")
        prompt_style = prompt_style or get_setting(
            "display.prompt_style", "#00ff00 bold"
        )

        self.stop_event = threading.Event()
        self.suppress_output = False
        self.prompt_detected = False
        self.last_data_time = 0.0

        # 設定から最適パフォーマンス値を取得
        self.receive_delay = get_setting("performance.receive_delay", 0.0001)
        self.batch_size = get_setting("performance.batch_size", 1)
        self.timeout_check_interval = get_setting(
            "performance.timeout_check_interval", 0.01
        )

        # コンポーネントの初期化
        self.connection = connection
        self.protocol_detector = MSXProtocolDetector()

        # 高速モードでデータプロセッサを初期化
        self.data_processor = DataProcessor(self.protocol_detector, instant_mode=True)

        # 拡張表示を使用（MSX通信用の高速モード）
        self.display = EnhancedTerminalDisplay()

        self.user_interface = UserInterface(
            prompt_style=prompt_style,
            encoding=self.encoding,
            connection=self.connection,
        )

        # Replace display with optimized version
        self.user_interface.display = self.display  # type: ignore
        self.user_interface.terminal = self  # type: ignore

        # エコー検出の設定
        self.user_interface.set_data_processor(self.data_processor)

        # DOSファイルシステムマネージャーの参照を設定（DIR自動キャッシュ用）
        self._setup_dos_filesystem_manager()

        self.file_transfer = FileTransferManager(
            connection=self.connection,
            encoding=self.encoding,
        )
        self.file_transfer.set_terminal(self)

    def _setup_dos_filesystem_manager(self) -> None:
        """DOSファイルシステムマネージャーの参照をDataProcessorに設定"""
        try:
            # UserInterfaceからDOSCompleterを取得
            if hasattr(self.user_interface, "input_session") and hasattr(
                self.user_interface.input_session, "completer"
            ):
                completer = self.user_interface.input_session.completer
                if hasattr(completer, "dos_completer"):
                    dos_filesystem_manager = completer.dos_completer.filesystem_manager
                    self.data_processor.set_dos_filesystem_manager(
                        dos_filesystem_manager
                    )
        except Exception:
            # DOSファイルシステムマネージャーの設定に失敗した場合は無視
            pass

    def run(self) -> None:
        """ターミナルセッションを開始"""
        try:
            print_info("Starting MSX Terminal Session")

            # バックグラウンド受信スレッドを開始
            threading.Thread(target=self._receive_loop, daemon=True).start()

            # メイン入力ループ
            self._input_loop()

        except KeyboardInterrupt:
            print_info("\nExiting on Ctrl+C...")
        finally:
            self.stop_event.set()
            if hasattr(self.display, "flush"):
                self.display.flush()
            self.connection.close()

    def _receive_loop(self) -> None:
        """Data receive loop with instant processing"""
        last_timeout_check = 0.0
        consecutive_empty_reads = 0

        while not self.stop_event.is_set():
            try:
                current_time = time.time()

                # Process incoming data
                had_data = self._process_incoming_data()

                # Adaptive delay based on data activity
                if had_data:
                    consecutive_empty_reads = 0
                    # No delay when data is flowing for maximum responsiveness
                    pass
                else:
                    consecutive_empty_reads += 1
                    # Stay very responsive even when idle
                    if consecutive_empty_reads < 5:
                        time.sleep(0.0001)  # Stay almost instant initially
                    else:
                        time.sleep(0.001)  # Slight slowdown after sustained inactivity

                # Check timeouts
                if current_time - last_timeout_check >= self.timeout_check_interval:
                    self._check_timeouts()
                    last_timeout_check = current_time

            except Exception as e:
                print_exception("Receive error", e)
                break

    def _process_incoming_data(self) -> bool:
        """Process incoming data with instant display

        Returns:
            True if data was processed, False if no data available
        """
        waiting = self.connection.in_waiting()
        if not waiting:
            return False

        try:
            # Read single character for instant processing
            data = self.connection.read(1)

            if not data:
                return False

            decoded = data.decode(self.encoding)
            self.last_data_time = time.time()

            if not self.suppress_output:
                # Process and display instantly
                output_lines = self.data_processor.process_data(decoded)
                for text, is_prompt in output_lines:
                    self._display_output(text, is_prompt)

            return True  # Data was processed

        except UnicodeDecodeError as e:
            print_exception("Decode error", e)
            return False

    def _check_timeouts(self) -> None:
        """Check for timeouts and process any remaining buffered data"""
        if self.suppress_output:
            return

        # Check for regular timeout
        timeout_result = self.data_processor.check_timeout(0.1)
        if timeout_result:
            text, is_prompt = timeout_result
            self._display_output(text, is_prompt)

        # Check for prompt candidate timeout
        prompt_result = self.data_processor.check_prompt_candidate(0.02)
        if prompt_result:
            text, is_prompt = prompt_result
            self._display_output(text, is_prompt)

        # Process any remaining buffered content
        if self.data_processor.buffer.has_content():
            buffer_content = self.data_processor.buffer.get_content()
            if self._is_basic_startup(buffer_content):
                is_prompt = self.protocol_detector.detect_prompt(buffer_content)
                if is_prompt:
                    self._display_output(buffer_content, True)
                    self.data_processor.buffer.clear()

    def _is_basic_startup(self, content: str) -> bool:
        """Check if content looks like BASIC startup sequence"""
        content_upper = content.upper()
        return (
            "BASIC" in content_upper or "Microsoft" in content or "Copyright" in content
        ) and content.strip().endswith("Ok")

    def _display_output(self, text: str, is_prompt: bool) -> None:
        """Display output text

        Args:
            text: Text to display
            is_prompt: Whether this is a prompt
        """
        # Always display text (including whitespace and line breaks)
        if text:  # Only skip completely empty strings
            self.user_interface.print_receive(text, is_prompt)

        # Always update prompt state if this is marked as a prompt
        if is_prompt:
            # Use saved prompt content if text is empty (instant mode case)
            prompt_text = (
                text if text.strip() else self.data_processor.last_prompt_content
            )
            if prompt_text:
                self._update_prompt_state(prompt_text)

    def _update_prompt_state(self, prompt_text: str) -> None:
        """Update prompt detection state and mode"""
        self.prompt_detected = True
        self.user_interface.prompt_detected = True

        # Update mode based on prompt
        detected_mode_enum = self.protocol_detector.detect_mode(prompt_text)
        if detected_mode_enum != MSXMode.UNKNOWN:
            # Force update protocol detector mode
            old_mode = self.protocol_detector.current_mode
            self.protocol_detector.current_mode = detected_mode_enum.value

            # Always update user interface when valid mode is detected
            self.user_interface.update_mode(detected_mode_enum.value)

            if self.protocol_detector.debug_mode:
                print_info(
                    f"[MSX Debug] Mode updated: {old_mode} -> {detected_mode_enum.value}"
                )

    def _input_loop(self) -> None:
        """Main user input loop"""
        while not self.stop_event.is_set():
            try:
                # Short delay after prompt detection
                if self.prompt_detected:
                    time.sleep(0.005)  # Very short delay
                    self.prompt_detected = False

                user_input = self.user_interface.prompt()

                if self.user_interface.handle_special_commands(
                    user_input, self.file_transfer, self.stop_event
                ):
                    continue

                self.user_interface.send(user_input)

            except KeyboardInterrupt:
                print_info("Ctrl+C detected. Exiting...")
                break
            except Exception as e:
                print_exception("Input error", e)
                break

    def set_mode(self, mode_value: str) -> None:
        """Set terminal mode

        Args:
            mode_value: Mode to set
        """
        self.protocol_detector.current_mode = mode_value
        self.user_interface.update_mode(mode_value)

    def toggle_debug_mode(self) -> None:
        """Toggle debug mode for protocol detection"""
        debug_mode = not getattr(self.protocol_detector, "debug_mode", False)
        self.protocol_detector.debug_mode = debug_mode
        print_info(f"Debug mode {'enabled' if debug_mode else 'disabled'}")
