"""
Optimized MSX Terminal Session for improved performance
"""

import msx_charset  # noqa: F401  # type: ignore
import threading
import time

from ..connection.manager import ConnectionManager
from ..io.user_interface import UserInterface
from ..transfer.file_transfer import FileTransferManager
from ..protocol.msx_detector import MSXProtocolDetector, MSXMode
from ..ui.color_output import print_info, print_exception
from ..connection.base import ConnectionConfig
from .data_processor import DataProcessor
from ..display.fast_output import HybridTerminalDisplay


class OptimizedMSXTerminalSession:
    """High-performance MSX terminal session"""

    def __init__(
        self,
        config: ConnectionConfig,
        encoding: str = "msx-jp",
        prompt_style: str = "#00ff00 bold",
        fast_mode: bool = True,
        responsive_mode: bool = True,
        instant_mode: bool = True,  # Default to instant mode for maximum responsiveness
    ):
        """Initialize optimized terminal session

        Args:
            config: Connection configuration
            encoding: Text encoding
            prompt_style: Prompt styling
            fast_mode: Enable performance optimizations
            responsive_mode: Enable maximum responsiveness for DIR commands
            instant_mode: Enable instant display with zero buffering (best for DIR)
        """
        self.encoding = encoding
        self.fast_mode = fast_mode
        self.responsive_mode = responsive_mode
        self.instant_mode = instant_mode
        self.stop_event = threading.Event()
        self.suppress_output = False
        self.prompt_detected = False
        self.last_data_time = 0
        self.debug_mode = False

        # Performance settings - adjusted for better responsiveness
        if instant_mode:
            self.receive_delay = 0.0001
            self.batch_size = 1  # Single character processing
            self.timeout_check_interval = 0.01  # More frequent timeout checks
        elif self.responsive_mode:
            self.receive_delay = 0.001
            self.batch_size = 512
            self.timeout_check_interval = 0.05  # More frequent timeout checks
        else:
            self.receive_delay = 0.005 if fast_mode else 0.001
            self.batch_size = 4096 if fast_mode else 1024
            self.timeout_check_interval = 0.1

        # Initialize components
        self.connection_manager = ConnectionManager(config)
        self.protocol_detector = MSXProtocolDetector()

        # Initialize data processor with instant mode
        self.data_processor = DataProcessor(
            self.protocol_detector, instant_mode=instant_mode
        )

        # Use optimized display if fast mode enabled
        if fast_mode:
            self.display = HybridTerminalDisplay(
                responsive_mode=responsive_mode, instant_mode=instant_mode
            )

        self.user_interface = UserInterface(
            prompt_style=prompt_style,
            encoding=encoding,
            connection=self.connection_manager.connection,
        )

        # Replace display with optimized version if fast mode
        if fast_mode:
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
            mode_str = f"fast_mode={self.fast_mode}, responsive_mode={self.responsive_mode}, instant_mode={self.instant_mode}"
            print_info(f"Starting MSX Terminal Session ({mode_str})")

            # Start background receive thread
            threading.Thread(target=self._optimized_receive_loop, daemon=True).start()

            # Main input loop
            self._input_loop()

        except KeyboardInterrupt:
            print_info("\nExiting on Ctrl+C...")
        finally:
            self.stop_event.set()
            if hasattr(self, "display") and hasattr(self.display, "flush"):
                self.display.flush()
            self.connection_manager.close()

    def _optimized_receive_loop(self) -> None:
        """Optimized data receive loop with reduced overhead"""
        last_timeout_check = 0
        consecutive_empty_reads = 0

        while not self.stop_event.is_set():
            try:
                current_time = time.time()

                # Process incoming data with batching
                had_data = self._process_incoming_data_batch()

                # Adaptive delay based on data activity and mode
                if had_data:
                    consecutive_empty_reads = 0
                    # Minimal or no delay when data is flowing for maximum responsiveness
                    if self.instant_mode:
                        # No delay at all in instant mode
                        pass
                    elif self.responsive_mode:
                        time.sleep(0.0001)  # Minimal delay
                    else:
                        time.sleep(0.001)
                else:
                    consecutive_empty_reads += 1
                    # Adaptive delay - start fast, slow down if no data
                    if self.instant_mode:
                        # Even when idle, stay very responsive for DIR commands
                        if consecutive_empty_reads < 5:
                            time.sleep(0.0001)  # Stay almost instant initially
                        else:
                            time.sleep(
                                0.001
                            )  # Slight slowdown after sustained inactivity
                    elif self.responsive_mode:
                        # Even when idle, stay responsive for DIR commands
                        if consecutive_empty_reads < 10:
                            time.sleep(0.001)  # Stay fast initially
                        else:
                            time.sleep(
                                self.receive_delay
                            )  # Slow down after sustained inactivity
                    else:
                        time.sleep(self.receive_delay)

                # Check timeouts less frequently
                if current_time - last_timeout_check >= self.timeout_check_interval:
                    self._check_timeouts()
                    last_timeout_check = current_time

            except Exception as e:
                print_exception("Receive error", e)
                break

    def _process_incoming_data_batch(self) -> bool:
        """Process incoming data in batches for better performance

        Returns:
            True if data was processed, False if no data available
        """
        waiting = self.connection_manager.connection.in_waiting()
        if not waiting:
            return False

        try:
            # In instant mode, read character by character for immediate response
            if self.instant_mode:
                # Read single character for instant processing
                data = self.connection_manager.connection.read(1)
            else:
                # Read up to batch_size bytes at once
                read_size = min(waiting, self.batch_size)
                data = self.connection_manager.connection.read(read_size)

            if not data:
                return False

            decoded = data.decode(self.encoding)
            self.last_data_time = time.time()

            if not self.suppress_output:
                # Process all data at once
                output_lines = self.data_processor.process_data(decoded)

                # Display updates based on mode
                if output_lines:
                    if self.instant_mode:
                        self._display_output_instant(output_lines)
                    elif self.responsive_mode:
                        self._display_output_immediate(output_lines)
                    else:
                        self._display_output_batch(output_lines)

            return True  # Data was processed

        except UnicodeDecodeError as e:
            print_exception("Decode error", e)
            return False

    def _display_output_instant(self, output_lines: list) -> None:
        """Display output lines instantly with zero buffering

        Args:
            output_lines: List of (text, is_prompt) tuples
        """
        for text, is_prompt in output_lines:
            self._display_output(text, is_prompt)
            # No explicit flush needed - instant display handles it

    def _display_output_immediate(self, output_lines: list) -> None:
        """Display output lines immediately without batching

        Args:
            output_lines: List of (text, is_prompt) tuples
        """
        for text, is_prompt in output_lines:
            self._display_output(text, is_prompt)
            # Immediate flush after each line for maximum responsiveness
            if hasattr(self, "display") and hasattr(self.display, "flush"):
                self.display.flush()

    def _display_output_batch(self, output_lines: list) -> None:
        """Display multiple output lines efficiently

        Args:
            output_lines: List of (text, is_prompt) tuples
        """
        for text, is_prompt in output_lines:
            self._display_output(text, is_prompt)

        # Flush display buffer after batch
        if hasattr(self, "display") and hasattr(self.display, "flush"):
            self.display.flush()

    def _check_timeouts(self) -> None:
        """Check for timeout conditions"""
        if self.suppress_output:
            return

        # Check for regular timeout
        timeout_result = self.data_processor.check_timeout(0.1)
        if timeout_result:
            text, is_prompt = timeout_result
            self._display_output(text, is_prompt)

        # Check for prompt candidate timeout - more aggressive for BASIC detection
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

        # Update mode based on prompt - always try to update
        detected_mode_enum = self.protocol_detector.detect_mode(prompt_text)
        if detected_mode_enum != MSXMode.UNKNOWN:
            # Force update protocol detector mode
            old_mode = self.protocol_detector.current_mode
            self.protocol_detector.current_mode = detected_mode_enum.value
            
            # Always update user interface when valid mode is detected
            self.user_interface.update_mode(detected_mode_enum.value)
            
            if self.protocol_detector.debug_mode:
                print_info(f"[MSX Debug] Mode updated: {old_mode} -> {detected_mode_enum.value}")

    def _input_loop(self) -> None:
        """Main user input loop"""
        while not self.stop_event.is_set():
            try:
                # Reduced delay after prompt detection
                if self.prompt_detected:
                    if self.instant_mode:
                        delay = 0.005  # Very short delay in instant mode
                    elif self.responsive_mode:
                        delay = 0.01  # Short delay in responsive mode
                    else:
                        delay = 0.02 if self.fast_mode else 0.05
                    time.sleep(delay)
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

    def get_performance_stats(self) -> dict:
        """Get performance statistics

        Returns:
            Dict with performance info
        """
        stats = {
            "fast_mode": self.fast_mode,
            "responsive_mode": self.responsive_mode,
            "instant_mode": self.instant_mode,
            "receive_delay": self.receive_delay,
            "batch_size": self.batch_size,
            "encoding": self.encoding,
        }

        # Add display stats if available
        if hasattr(self, "display") and hasattr(self.display, "get_performance_stats"):
            stats.update(self.display.get_performance_stats())

        return stats

    def toggle_fast_mode(self) -> None:
        """Toggle fast mode on/off"""
        self.fast_mode = not self.fast_mode
        # Update settings based on mode
        if self.instant_mode:
            self.receive_delay = 0.0001
            self.batch_size = 1
        elif self.responsive_mode:
            self.receive_delay = 0.001
            self.batch_size = 512
        else:
            self.receive_delay = 0.005 if self.fast_mode else 0.001
            self.batch_size = 4096 if self.fast_mode else 1024
        print_info(f"Fast mode {'enabled' if self.fast_mode else 'disabled'}")

    def toggle_responsive_mode(self) -> None:
        """Toggle responsive mode for DIR commands"""
        self.responsive_mode = not self.responsive_mode
        # Update settings
        if self.instant_mode:
            self.receive_delay = 0.0001
            self.batch_size = 1
            self.timeout_check_interval = 0.01
        elif self.responsive_mode:
            self.receive_delay = 0.001
            self.batch_size = 512
            self.timeout_check_interval = 0.05
        else:
            self.receive_delay = 0.005 if self.fast_mode else 0.001
            self.batch_size = 4096 if self.fast_mode else 1024
            self.timeout_check_interval = 0.1
        print_info(
            f"Responsive mode {'enabled' if self.responsive_mode else 'disabled'}"
        )

    def toggle_instant_mode(self) -> None:
        """Toggle instant mode for zero-buffering display"""
        self.instant_mode = not self.instant_mode

        # Update data processor
        self.data_processor.set_instant_mode(self.instant_mode)

        # Update display if available
        if hasattr(self, "display"):
            self.display = HybridTerminalDisplay(
                responsive_mode=self.responsive_mode, instant_mode=self.instant_mode
            )
            if hasattr(self, "user_interface"):
                self.user_interface.display = self.display

        # Update settings
        if self.instant_mode:
            self.receive_delay = 0.0001
            self.batch_size = 1  # Single character processing
            self.timeout_check_interval = 0.01
        elif self.responsive_mode:
            self.receive_delay = 0.001
            self.batch_size = 512
            self.timeout_check_interval = 0.05
        else:
            self.receive_delay = 0.005 if self.fast_mode else 0.001
            self.batch_size = 4096 if self.fast_mode else 1024
            self.timeout_check_interval = 0.1

        print_info(f"Instant mode {'enabled' if self.instant_mode else 'disabled'}")

    def toggle_debug_mode(self) -> None:
        """Toggle debug mode for protocol detection"""
        self.debug_mode = not self.debug_mode

        # Update protocol detector debug mode
        if hasattr(self.protocol_detector, "debug_mode"):
            self.protocol_detector.debug_mode = self.debug_mode

        print_info(f"Debug mode {'enabled' if self.debug_mode else 'disabled'}")


# Backward compatibility alias
FastMSXTerminal = OptimizedMSXTerminalSession
