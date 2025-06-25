"""
基本的なターミナル表示機能
"""

import subprocess
import sys
from typing import Optional
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText


class TerminalDisplay:
    """ターミナル表示機能を提供するクラス"""

    def __init__(self, receive_color: str = "#00ff00") -> None:
        self.receive_color = receive_color

    def clear_screen(self) -> None:
        """画面をクリア"""
        try:
            if sys.platform == "win32":
                subprocess.run(["cmd", "/c", "cls"], check=False, timeout=5)
            else:
                subprocess.run(["clear"], check=False, timeout=5)
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            # 画面クリアに失敗した場合は何もしない
            pass

    def print_receive(self, text: str, is_prompt: bool = False) -> None:
        """受信したテキストを表示

        Args:
            text: 表示するテキスト
            is_prompt: プロンプトかどうか
        """
        text_to_display = self._wrap_text_if_needed(text)

        color = f"{self.receive_color} bold" if is_prompt else self.receive_color
        print_formatted_text(FormattedText([(color, text_to_display)]))

    def _wrap_text_if_needed(
        self, text: str, max_width: Optional[int] = None
    ) -> str:
        """必要に応じてテキストを改行

        Args:
            text: テキスト
            max_width: 最大幅

        Returns:
            整形されたテキスト
        """
        try:
            import os
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
