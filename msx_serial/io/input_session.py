"""
Input session management for terminal
"""

import re
from typing import Any, Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style

from ..commands.command_types import CommandType
from ..completion.completers.command_completer import CommandCompleter


class InputSession:
    """Manage user input and prompt session"""

    def __init__(
        self,
        prompt_style: str = "#00ff00 bold",
        current_mode: str = "unknown",
        connection: Optional[Any] = None,
    ) -> None:
        self.current_mode = current_mode
        self.prompt_detected = False
        self.prompt_pattern = re.compile(r"[A-Z]>\s*$")
        self.connection = connection

        self.style = Style.from_dict({"prompt": prompt_style})
        self.completer = CommandCompleter(
            special_commands=[str(cmd.value) for cmd in CommandType],
            current_mode=current_mode,
            connection=connection,
        )

        self.session: PromptSession = PromptSession(
            completer=self.completer,
            style=self.style,
            complete_in_thread=True,
            mouse_support=False,
            wrap_lines=True,
            enable_history_search=True,
            multiline=False,
            auto_suggest=None,
        )

    def prompt(self) -> Any:
        """Display prompt and get user input

        Returns:
            User input
        """
        if hasattr(self, "completer") and self.completer:
            self.completer.set_mode(self.current_mode)
        else:
            available_commands = [str(cmd.value) for cmd in CommandType]
            self.completer = CommandCompleter(
                available_commands, self.current_mode, self.connection
            )
            self.session.completer = self.completer

        if self.prompt_detected:
            self.prompt_detected = False

        return self.session.prompt("")

    def update_mode(self, mode: str) -> None:
        """Update current mode

        Args:
            mode: New mode
        """
        self.current_mode = mode
        if hasattr(self, "completer") and self.completer:
            self.completer.set_mode(mode)
