"""
MSX Terminal main module with optimized performance
"""

import msx_charset  # noqa: F401  # type: ignore
import threading
import time

from .connection.manager import ConnectionManager
from .io.user_interface import UserInterface
from .transfer.file_transfer import FileTransferManager
from .protocol.msx_detector import MSXProtocolDetector
from .ui.color_output import print_info, print_exception
from .connection.base import ConnectionConfig
from .core.data_processor import DataProcessor
from .core.optimized_session import OptimizedMSXTerminalSession


class MSXTerminalSession:
    """MSX Terminal Session with improved display synchronization"""

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
            print_info("Starting MSX Terminal Session")

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
        """Background thread for receiving data"""
        buffer = ""
        last_timeout_check = 0

        while not self.stop_event.is_set():
            try:
                current_time = time.time()

                # Read available data
                if self.connection_manager.connection.in_waiting():
                    data = self.connection_manager.connection.read(
                        self.connection_manager.connection.in_waiting()
                    )
                    decoded = data.decode(self.encoding)
                    buffer += decoded
                    self.last_data_time = current_time

                    if not self.suppress_output:
                        output_lines = self.data_processor.process_data(decoded)
                        for text, is_prompt in output_lines:
                            self._display_output(text, is_prompt)

                # Check timeouts every 0.1 seconds
                if current_time - last_timeout_check >= 0.1:
                    if not self.suppress_output:
                        # Check for timeout
                        timeout_result = self.data_processor.check_timeout(0.1)
                        if timeout_result:
                            text, is_prompt = timeout_result
                            self._display_output(text, is_prompt)

                        # Check for prompt candidate timeout
                        prompt_result = self.data_processor.check_prompt_candidate(0.02)
                        if prompt_result:
                            text, is_prompt = prompt_result
                            self._display_output(text, is_prompt)

                    last_timeout_check = current_time

                time.sleep(0.001)

            except UnicodeDecodeError as e:
                print_exception("Decode error", e)
            except Exception as e:
                print_exception("Receive error", e)
                break

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
                # Wait a bit after prompt detection
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


# Use optimized session as default with responsive mode enabled for better DIR command response
MSXTerminal = OptimizedMSXTerminalSession

# Backward compatibility aliases
MSXTerminalOriginal = MSXTerminalSession  # Original version for fallback
UserInputHandler = UserInterface  # Legacy alias

__all__ = ["MSXTerminal", "MSXTerminalSession"]
