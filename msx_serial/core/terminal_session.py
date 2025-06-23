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
        buffer = ""

        while not self.stop_event.is_set():
            try:
                current_time = time.time()

                if self.connection_manager.connection.in_waiting():
                    data = self.connection_manager.connection.read(
                        self.connection_manager.connection.in_waiting()
                    )
                    decoded = data.decode(self.encoding)
                    buffer += decoded
                    self.last_data_time = current_time

                    if not self.suppress_output:
                        buffer = self._process_received_data(buffer)

                # Handle timeout scenarios
                elif buffer and (current_time - self.last_data_time) > 0.1:
                    if not self.suppress_output and buffer.strip():
                        buffer = self._handle_timeout_buffer(buffer)

                elif (
                    buffer
                    and self.protocol_detector.is_prompt_candidate(buffer)
                    and (current_time - self.last_data_time) > 0.02
                ):
                    if not self.suppress_output and buffer.strip():
                        buffer = self._handle_prompt_candidate(buffer)

            except Exception as e:
                print_exception("Receive error", e)
                break

    def _process_received_data(self, buffer: str) -> str:
        """Process received data buffer

        Args:
            buffer: Data buffer

        Returns:
            Remaining buffer data
        """
        if self.protocol_detector.detect_prompt(buffer):
            return self._handle_prompt_detection(buffer)
        else:
            return self._handle_regular_data(buffer)

    def _handle_prompt_detection(self, buffer: str) -> str:
        """Handle detected prompt in buffer"""
        lines = buffer.split("\n")

        # Display all lines except the last (prompt line)
        for line in lines[:-1]:
            if line.strip():
                self.user_interface.print_receive(line)

        # Handle the prompt line
        last_line = lines[-1]
        if self.protocol_detector.detect_prompt(last_line):
            self.user_interface.print_receive(last_line, is_prompt=True)
            time.sleep(0.01)  # Brief wait for display sync
            self._update_prompt_state(last_line)
        else:
            self.user_interface.print_receive(last_line)

        return ""

    def _handle_regular_data(self, buffer: str) -> str:
        """Handle regular (non-prompt) data"""
        if "\n" in buffer:
            lines = buffer.split("\n")
            for line in lines[:-1]:
                if line.strip():
                    self.user_interface.print_receive(line)
            return lines[-1]  # Keep the last incomplete line

        return buffer

    def _handle_timeout_buffer(self, buffer: str) -> str:
        """Handle buffer on timeout"""
        if self.protocol_detector.detect_prompt(buffer):
            self.user_interface.print_receive(buffer, is_prompt=True)
            self._update_prompt_state(buffer)
        else:
            self.user_interface.print_receive(buffer)
        return ""

    def _handle_prompt_candidate(self, buffer: str) -> str:
        """Handle potential prompt candidate"""
        if self.protocol_detector.detect_prompt(buffer):
            self.user_interface.print_receive(buffer, is_prompt=True)
            self._update_prompt_state(buffer)
        else:
            self.user_interface.print_receive(buffer)
        return ""

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
