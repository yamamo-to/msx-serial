"""
MSX Terminal Session - Main terminal coordination
"""

import msx_charset  # noqa: F401  # type: ignore
import threading
import time

from ..connection.manager import ConnectionManager
from ..io.user_interface import UserInterface
from ..transfer.file_transfer import FileTransferManager
from ..protocol.msx_detector import MSXProtocolDetector
from ..ui.color_output import print_info, print_exception
from ..connection.base import ConnectionConfig
from .data_processor import DataProcessor


class MSXTerminalSession:
    """Main MSX terminal session coordinator"""

    def __init__(
        self,
        config: ConnectionConfig,
        encoding: str = "msx-jp",
        prompt_style: str = "#00ff00 bold",
    ):
        """Initialize terminal session

        Args:
            config: Connection configuration
            encoding: Text encoding
            prompt_style: Prompt styling
        """
        self.encoding = encoding
        self.stop_event = threading.Event()
        self.suppress_output = False
        self.prompt_detected = False
        self.last_data_time = 0

        # Initialize components
        self.connection_manager = ConnectionManager(config)
        self.protocol_detector = MSXProtocolDetector()
        self.data_processor = DataProcessor(self.protocol_detector)

        self.user_interface = UserInterface(
            prompt_style=prompt_style,
            encoding=encoding,
            connection=self.connection_manager.connection,
        )
        self.user_interface.terminal = self

        self.file_transfer = FileTransferManager(
            connection=self.connection_manager.connection,
            encoding=encoding,
        )
        self.file_transfer.set_terminal(self)

    def run(self) -> None:
        """Start terminal session"""
        try:
            # Start background receive thread
            threading.Thread(target=self._receive_loop, daemon=True).start()

            # Main input loop
            self._input_loop()

        except KeyboardInterrupt:
            print_info("\nExiting on Ctrl+C...")
        finally:
            self.stop_event.set()
            self.connection_manager.close()

    def _receive_loop(self) -> None:
        """Handle incoming data from MSX"""
        while not self.stop_event.is_set():
            try:
                self._process_incoming_data()
                self._check_timeouts()
                time.sleep(0.001)  # Small delay to prevent busy waiting
            except Exception as e:
                print_exception("Receive error", e)
                break

    def _process_incoming_data(self) -> None:
        """Process any available incoming data"""
        if not self.connection_manager.connection.in_waiting():
            return

        try:
            data = self.connection_manager.connection.read(
                self.connection_manager.connection.in_waiting()
            )
            decoded = data.decode(self.encoding)
            self.last_data_time = time.time()

            if not self.suppress_output:
                # Process data through the data processor
                output_lines = self.data_processor.process_data(decoded)
                for text, is_prompt in output_lines:
                    self._display_output(text, is_prompt)

        except UnicodeDecodeError as e:
            print_exception("Decode error", e)

    def _check_timeouts(self) -> None:
        """Check for timeout conditions"""
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

    def _display_output(self, text: str, is_prompt: bool) -> None:
        """Display output text

        Args:
            text: Text to display
            is_prompt: Whether this is a prompt
        """
        self.user_interface.print_receive(text, is_prompt)
        if is_prompt:
            self._update_prompt_state(text)

    def _update_prompt_state(self, prompt_text: str) -> None:
        """Update prompt detection state and mode"""
        self.prompt_detected = True
        self.user_interface.prompt_detected = True

        # Update mode based on prompt
        if self.protocol_detector.force_mode_update(prompt_text):
            self.user_interface.update_mode(self.protocol_detector.current_mode)

    def _input_loop(self) -> None:
        """Main user input loop"""
        while not self.stop_event.is_set():
            try:
                # Wait briefly after prompt detection
                if self.prompt_detected:
                    time.sleep(0.05)
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
