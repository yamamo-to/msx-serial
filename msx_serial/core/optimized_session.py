"""
Optimized MSX terminal session with instant response
"""

import msx_charset  # noqa: F401  # type: ignore
import threading
import time

from ..connection.manager import ConnectionManager
from ..core.data_processor import DataProcessor
from ..display.fast_output import HybridTerminalDisplay
from ..io.user_interface import UserInterface
from ..transfer.file_transfer import FileTransferManager
from ..protocol.msx_detector import MSXProtocolDetector, MSXMode
from ..common.color_output import print_info, print_exception
from ..connection.base import ConnectionConfig


class OptimizedMSXTerminalSession:
    """Optimized MSX terminal session with instant response"""

    def __init__(
        self,
        config: ConnectionConfig,
        encoding: str = "msx-jp",
        prompt_style: str = "#00ff00 bold",
    ):
        """Initialize optimized terminal session

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

        # Fixed settings for optimal performance
        self.receive_delay = 0.0001
        self.batch_size = 1  # Single character processing
        self.timeout_check_interval = 0.01

        # Initialize components
        self.connection_manager = ConnectionManager(config)
        self.protocol_detector = MSXProtocolDetector()

        # Initialize data processor with instant mode
        self.data_processor = DataProcessor(self.protocol_detector, instant_mode=True)

        # Use optimized display
        self.display = HybridTerminalDisplay(responsive_mode=True, instant_mode=True)

        self.user_interface = UserInterface(
            prompt_style=prompt_style,
            encoding=encoding,
            connection=self.connection_manager.connection,
        )

        # Replace display with optimized version
        self.user_interface.display = self.display
        self.user_interface.terminal = self

        # Set up echo detection
        self.user_interface.set_data_processor(self.data_processor)

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
            if hasattr(self.display, "flush"):
                self.display.flush()
            self.connection_manager.close()

    def _receive_loop(self) -> None:
        """Data receive loop with instant processing"""
        last_timeout_check = 0
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
        waiting = self.connection_manager.connection.in_waiting()
        if not waiting:
            return False

        try:
            # Read single character for instant processing
            data = self.connection_manager.connection.read(1)

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

        # Additional check for potential BASIC prompts that might be missed
        if self.data_processor.buffer.has_content():
            buffer_content = self.data_processor.buffer.get_content()
            # If buffer contains BASIC-related content and ends with "Ok", process it
            if (
                "BASIC" in buffer_content.upper()
                or "Microsoft" in buffer_content
                or "Copyright" in buffer_content
            ) and buffer_content.strip().endswith("Ok"):
                # Force process this as a potential BASIC prompt
                is_prompt = self.protocol_detector.detect_prompt(buffer_content)
                if is_prompt:
                    self._display_output(buffer_content, True)
                    self.data_processor.buffer.clear()

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


# Backward compatibility alias
FastMSXTerminal = OptimizedMSXTerminalSession
