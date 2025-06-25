"""
Optimized terminal output handler for MSX serial communication
"""

import os
import sys
from typing import Dict, Any
from threading import RLock


class OptimizedTerminalDisplay:
    """Unified terminal display optimized for instant MSX communication"""

    def __init__(
        self,
        receive_color: str = "\033[92m",  # Green ANSI
    ):
        """Initialize display with instant mode"""
        self.receive_color = receive_color
        self.prompt_color = f"{receive_color}\033[1m"  # Bold
        self.reset_color = "\033[0m"

        # Performance tracking
        self.stats = {
            "total_writes": 0,
            "instant_writes": 0,
        }

        # Thread safety
        self._output_lock = RLock()

    def clear_screen(self) -> None:
        """Clear terminal screen"""
        if os.name == "nt":
            os.system("cls")
        else:
            sys.stdout.write("\033[2J\033[H")
            sys.stdout.flush()

    def print_receive(self, text: str, is_prompt: bool = False) -> None:
        """Display received data with instant formatting"""
        with self._output_lock:
            self.stats["total_writes"] += 1

            # Format text without adding extra newlines
            if is_prompt:
                formatted = f"{self.prompt_color}{text}{self.reset_color}"
            else:
                formatted = f"{self.receive_color}{text}{self.reset_color}"

            # Always write instantly
            self._write_instant(formatted)

    def _write_instant(self, text: str) -> None:
        """Write directly to stdout"""
        sys.stdout.write(text)
        sys.stdout.flush()
        self.stats["instant_writes"] += 1

    def flush(self) -> None:
        """Flush stdout (no-op since we're always instant)"""
        sys.stdout.flush()

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return self.stats.copy()
