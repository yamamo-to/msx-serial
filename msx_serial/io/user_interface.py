"""
User interface coordinator for MSX terminal
"""

import threading
from typing import Any, TYPE_CHECKING

from ..connection.base import Connection
from ..display.terminal_output import TerminalDisplay
from ..commands.handler import CommandHandler
from .input_session import InputSession
from .data_sender import DataSender

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

        # Initialize components
        self.display = TerminalDisplay()
        self.input_session = InputSession(prompt_style, self.current_mode)
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

    def _update_completer_mode(self) -> None:
        """Update completer mode (for compatibility)"""
        self.update_mode(self.current_mode)
