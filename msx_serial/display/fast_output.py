"""
Fast terminal output handler for improved performance
"""

import os
import sys
import time
from typing import Optional
from threading import RLock


class FastTerminalDisplay:
    """Optimized terminal display for minimal latency"""

    def __init__(self, receive_color: str = "\033[92m"):  # Green ANSI
        """Initialize fast display

        Args:
            receive_color: ANSI color code for received text
        """
        self.receive_color = receive_color
        self.prompt_color = f"{receive_color}\033[1m"  # Bold green
        self.reset_color = "\033[0m"

        # Cache terminal size
        self._terminal_width: Optional[int] = None
        self._size_cache_time = 0
        self._size_cache_ttl = 5.0  # Refresh every 5 seconds

        # Thread safety for concurrent output
        self._output_lock = RLock()

        # Output buffering - reduced for better responsiveness
        self._buffer = []
        self._buffer_size = 0
        self._max_buffer_size = (
            1024  # Reduced from 8KB to 1KB for better responsiveness
        )
        self._last_flush_time = 0
        self._max_buffer_time = 0.05  # Max 50ms buffering delay

    def _get_terminal_width(self) -> int:
        """Get terminal width with caching

        Returns:
            Terminal width in characters
        """
        current_time = time.time()

        # Use cached value if still valid
        if (
            self._terminal_width is not None
            and current_time - self._size_cache_time < self._size_cache_ttl
        ):
            return self._terminal_width

        # Update cache
        try:
            size = os.get_terminal_size()
            self._terminal_width = size.columns
            self._size_cache_time = current_time
        except OSError:
            self._terminal_width = 80  # Default fallback

        return self._terminal_width

    def _wrap_text_fast(self, text: str) -> str:
        """Fast text wrapping with minimal overhead

        Args:
            text: Text to wrap

        Returns:
            Wrapped text
        """
        # Skip wrapping for short text
        if len(text) <= 40:  # Most prompts and short messages
            return text

        width = self._get_terminal_width()

        # Skip wrapping if text fits
        if len(text) <= width:
            return text

        # Simple line-based wrapping (faster than character-based)
        lines = []
        for i in range(0, len(text), width):
            lines.append(text[i : i + width])
        return "\n".join(lines)

    def clear_screen(self) -> None:
        """Clear terminal screen"""
        self._flush_buffer()
        if os.name == "nt":
            os.system("cls")
        else:
            sys.stdout.write("\033[2J\033[H")
            sys.stdout.flush()

    def print_receive(self, text: str, is_prompt: bool = False) -> None:
        """Display received data with minimal formatting overhead

        Args:
            text: Text to display
            is_prompt: Whether this is a prompt line
        """
        with self._output_lock:
            # Use direct ANSI codes for speed
            if is_prompt:
                formatted = f"{self.prompt_color}{text}{self.reset_color}\n"
            else:
                formatted = f"{self.receive_color}{text}{self.reset_color}\n"

            self._buffer_write(formatted, force_flush=is_prompt)

    def print_receive_fast(self, text: str) -> None:
        """Ultra-fast print without color formatting

        Args:
            text: Text to display
        """
        with self._output_lock:
            self._buffer_write(f"{text}\n")

    def _buffer_write(self, text: str, force_flush: bool = False) -> None:
        """Write to buffer with intelligent flushing

        Args:
            text: Text to write
            force_flush: Force immediate flush
        """
        current_time = time.time()

        # Initialize flush time if first write
        if not self._buffer:
            self._last_flush_time = current_time

        self._buffer.append(text)
        self._buffer_size += len(text)

        # Improved flushing conditions for better responsiveness
        should_flush = (
            force_flush
            or
            # Buffer is full
            self._buffer_size >= self._max_buffer_size
            or
            # Contains prompt indicators (immediately flush)
            any(
                prompt in text
                for prompt in [
                    "A>",
                    "B>",
                    "C>",
                    "D>",
                    "E>",
                    "F>",
                    "G>",
                    "H>",
                    ">",
                    "Ok",
                ]
            )
            or
            # Contains line endings (for DIR command output)
            "\n" in text
            or
            # Time-based flush (prevent long delays)
            (current_time - self._last_flush_time) >= self._max_buffer_time
            or
            # Contains MSX BASIC keywords that indicate output completion
            any(
                keyword in text
                for keyword in ["bytes", " Files", " Disk", "Ready", "Syntax error"]
            )
        )

        if should_flush:
            self._flush_buffer()

    def _flush_buffer(self) -> None:
        """Flush output buffer to stdout"""
        if not self._buffer:
            return

        # Write all buffered content at once
        content = "".join(self._buffer)
        sys.stdout.write(content)
        sys.stdout.flush()

        # Clear buffer and update timing
        self._buffer.clear()
        self._buffer_size = 0
        self._last_flush_time = time.time()

    def flush(self) -> None:
        """Manually flush buffer"""
        with self._output_lock:
            self._flush_buffer()


class ResponsiveTerminalDisplay(FastTerminalDisplay):
    """Even more responsive version that prioritizes real-time output"""

    def __init__(self, receive_color: str = "\033[92m"):
        """Initialize responsive display"""
        super().__init__(receive_color)
        # More aggressive settings for maximum responsiveness
        self._max_buffer_size = 256  # Very small buffer
        self._max_buffer_time = 0.01  # 10ms max delay

    def _buffer_write(self, text: str, force_flush: bool = False) -> None:
        """Ultra-responsive buffering with immediate flush for most content"""
        current_time = time.time()

        # Initialize flush time if first write
        if not self._buffer:
            self._last_flush_time = current_time

        self._buffer.append(text)
        self._buffer_size += len(text)

        # Very aggressive flushing for maximum responsiveness
        should_flush = (
            force_flush
            or
            # Any prompt-like character immediately flushes
            ">" in text
            or
            # Any newline immediately flushes
            "\n" in text
            or
            # Very small buffer
            self._buffer_size >= self._max_buffer_size
            or
            # Very short time delay
            (current_time - self._last_flush_time) >= self._max_buffer_time
        )

        if should_flush:
            self._flush_buffer()


class InstantTerminalDisplay:
    """Instant display with zero buffering for maximum responsiveness"""

    def __init__(self, receive_color: str = "\033[92m"):
        """Initialize instant display

        Args:
            receive_color: ANSI color code for received text
        """
        self.receive_color = receive_color
        self.prompt_color = f"{receive_color}\033[1m"  # Bold green
        self.reset_color = "\033[0m"

        # Thread safety for concurrent output
        self._output_lock = RLock()

    def clear_screen(self) -> None:
        """Clear terminal screen"""
        if os.name == "nt":
            os.system("cls")
        else:
            sys.stdout.write("\033[2J\033[H")
            sys.stdout.flush()

    def print_receive(self, text: str, is_prompt: bool = False) -> None:
        """Display received data instantly with zero buffering

        Args:
            text: Text to display
            is_prompt: Whether this is a prompt line
        """
        with self._output_lock:
            # Smart handling for different text types
            if len(text) == 1:
                # Single character handling
                if text == "\n":
                    # Actual newline character
                    sys.stdout.write("\n")
                elif text == "\r":
                    # Carriage return
                    sys.stdout.write("\r")
                elif text.isprintable():
                    # Regular printable character with color
                    formatted = f"{self.receive_color}{text}{self.reset_color}"
                    sys.stdout.write(formatted)
                # Skip non-printable characters except \n and \r
            else:
                # Multi-character text (lines, prompts)
                if is_prompt:
                    # Prompts get bold formatting and newline
                    formatted = f"{self.prompt_color}{text}{self.reset_color}"
                    if not text.endswith("\n"):
                        formatted += "\n"
                    sys.stdout.write(formatted)
                else:
                    # Regular multi-character text
                    if text.endswith("\n"):
                        # Text already has newline, don't add another
                        formatted = f"{self.receive_color}{text}{self.reset_color}"
                    else:
                        # Text doesn't have newline, don't add one for instant mode
                        formatted = f"{self.receive_color}{text}{self.reset_color}"
                    sys.stdout.write(formatted)

            # Always flush for immediate display
            sys.stdout.flush()

    def print_receive_fast(self, text: str) -> None:
        """Ultra-fast instant print without color formatting

        Args:
            text: Text to display
        """
        with self._output_lock:
            # Smart handling for single characters
            if len(text) == 1:
                # Single character - output directly
                sys.stdout.write(text)
            else:
                # Multi-character text
                if text.endswith("\n"):
                    sys.stdout.write(text)
                else:
                    sys.stdout.write(f"{text}\n")

            sys.stdout.flush()

    def flush(self) -> None:
        """Flush buffers (no-op since there's no buffering)"""
        pass  # No buffering, so nothing to flush


class HybridTerminalDisplay:
    """Hybrid display that chooses optimal method based on content"""

    def __init__(
        self,
        receive_color: str = "#00ff00",
        responsive_mode: bool = True,
        instant_mode: bool = False,
    ):
        """Initialize hybrid display

        Args:
            receive_color: Color for received text
            responsive_mode: Use responsive display for better DIR command response
            instant_mode: Use instant display for zero-buffering (maximum responsiveness)
        """
        from .terminal_output import TerminalDisplay

        # Fallback to original for complex formatting
        self.full_display = TerminalDisplay(receive_color)

        # Choose display based on responsiveness requirements
        if instant_mode:
            self.fast_display = InstantTerminalDisplay()
            self.mode_name = "instant"
        elif responsive_mode:
            self.fast_display = ResponsiveTerminalDisplay()
            self.mode_name = "responsive"
        else:
            self.fast_display = FastTerminalDisplay()
            self.mode_name = "fast"

        # Performance counters
        self.fast_count = 0
        self.full_count = 0

    def clear_screen(self) -> None:
        """Clear terminal screen"""
        self.fast_display.clear_screen()

    def print_receive(self, text: str, is_prompt: bool = False) -> None:
        """Display received data using optimal method

        Args:
            text: Text to display
            is_prompt: Whether this is a prompt line
        """
        # Use fast display for simple cases (most cases for better responsiveness)
        if self._should_use_fast_display(text):
            self.fast_display.print_receive(text, is_prompt)
            self.fast_count += 1
        else:
            # Use full display for complex formatting
            self.full_display.print_receive(text, is_prompt)
            self.full_count += 1

    def _should_use_fast_display(self, text: str) -> bool:
        """Determine if fast display should be used

        Args:
            text: Text to evaluate

        Returns:
            True if fast display is suitable
        """
        # Be very aggressive about using fast display for maximum responsiveness
        # Almost always use fast display unless there are specific complex requirements

        # Only use full display for extremely long text that might cause issues
        if len(text) > 1000:
            return False

        # Fast display handles everything else
        return True

    def flush(self) -> None:
        """Flush all buffers"""
        self.fast_display.flush()

    def get_performance_stats(self) -> dict:
        """Get performance statistics

        Returns:
            Dict with performance counters
        """
        total = self.fast_count + self.full_count
        if total == 0:
            return {"fast_ratio": 0, "total_calls": 0, "display_mode": self.mode_name}

        return {
            "fast_calls": self.fast_count,
            "full_calls": self.full_count,
            "total_calls": total,
            "fast_ratio": self.fast_count / total * 100,
            "display_mode": self.mode_name,
        }
