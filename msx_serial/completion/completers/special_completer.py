"""
特殊コマンドの補完機能
"""

from typing import Iterator, List
from prompt_toolkit.completion import Completion

from .base import BaseCompleter, CompletionContext
from ...input.commands import CommandType


class SpecialCompleter(BaseCompleter):
    """特殊コマンドの補完を提供するクラス"""

    def __init__(self, special_commands: List[str]) -> None:
        """初期化

        Args:
            special_commands: 特殊コマンドのリスト
        """
        super().__init__()
        self.special_commands = special_commands

    def get_completions(
        self, context: CompletionContext
    ) -> Iterator[Completion]:
        """特殊コマンドの補完候補を生成

        Args:
            context: 補完コンテキスト

        Yields:
            補完候補
        """
        word = context.word
        if not word.startswith("@"):
            word = "@" + word

        # @encodeコマンドの補完
        if context.text.startswith("@encode "):
            yield from self._complete_encode_command(context)
            return

        # その他の特殊コマンドの補完
        for command in self.special_commands:
            if command.startswith(word):
                completion_text = (
                    command[1:] if command.startswith("@") else command
                )
                cmd = CommandType.from_input("@" + completion_text)
                if cmd:
                    yield Completion(
                        completion_text,
                        start_position=-len(context.word),
                        display=command,
                        display_meta=cmd.description,
                    )

    def _complete_encode_command(
        self, context: CompletionContext
    ) -> Iterator[Completion]:
        """@encodeコマンドの補完候補を生成

        Args:
            context: 補完コンテキスト

        Yields:
            補完候補
        """
        encoding = context.text[8:].strip()
        for keyword in self.msx_keywords["ENCODE"]["keywords"]:
            name = keyword[0]
            meta = keyword[1]
            if name.startswith(encoding):
                yield Completion(
                    name,
                    start_position=-len(encoding),
                    display=name,
                    display_meta=meta,
                )