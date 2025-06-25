"""
Terminal display output handler
"""

import os
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText


class TerminalDisplay:
    """Terminal display management"""

    def __init__(self, receive_color: str = "#00ff00"):
        self.receive_color = receive_color

    def clear_screen(self) -> None:
        """Clear terminal screen"""
        os.system("cls" if os.name == "nt" else "clear")

    def print_receive(self, text: str, is_prompt: bool = False) -> None:
        """Display received data with proper formatting

        Args:
            text: Text to display
            is_prompt: Whether this is a prompt line
        """
        text_to_display = self._wrap_text_if_needed(text)

        color = f"{self.receive_color} bold" if is_prompt else self.receive_color
        print_formatted_text(FormattedText([(color, text_to_display)]))

    def _wrap_text_if_needed(self, text: str) -> str:
        """Wrap text based on terminal width

        Args:
            text: Original text

        Returns:
            Wrapped text if necessary
        """
        try:
            terminal_size = os.get_terminal_size()
            terminal_width = terminal_size.columns

            if len(text) > terminal_width:
                lines = []
                for i in range(0, len(text), terminal_width):
                    lines.append(text[i : i + terminal_width])
                return "\n".join(lines)
            return text

        except OSError:
            return text
