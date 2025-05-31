"""
コマンド補完機能
"""

from typing import Iterator, List
from prompt_toolkit.completion import Completion

from .base import BaseCompleter, CompletionContext
from .help_completer import HelpCompleter
from .special_completer import SpecialCompleter
from .iot_completer import IoTCompleter


class CommandCompleter(BaseCompleter):
    """コマンド補完を提供するクラス"""

    def __init__(self, special_commands: List[str]) -> None:
        super().__init__()
        self.help_completer = HelpCompleter()
        self.special_completer = SpecialCompleter(special_commands)
        self.iot_completer = IoTCompleter()

    def get_completions(
        self, context: CompletionContext
    ) -> Iterator[Completion]:
        if context.text.startswith("@help"):
            yield from self.help_completer.get_completions(context)
            return

        if context.text.startswith("@"):
            yield from self.special_completer.get_completions(context)
            return

        if context.text.startswith("_"):
            yield from self._complete_command_keywords(context)
            return

        yield from self._complete_general_keywords(context)

    def _complete_command_keywords(
        self, context: CompletionContext
    ) -> Iterator[Completion]:
        word = context.word
        if not word.startswith("_"):
            word = "_" + word

        for command in self.msx_keywords["COMMAND"]["keywords"]:
            name = command[0]
            meta = command[1]
            if name.startswith(word):
                completion_text = (
                    name[1:] if name.startswith("_") else name
                )
                yield Completion(
                    completion_text,
                    start_position=-len(context.word),
                    display=name,
                    display_meta=meta,
                )

    def _complete_general_keywords(
        self, context: CompletionContext
    ) -> Iterator[Completion]:
        word = context.word
        for command in self.msx_keywords["GENERAL"]["keywords"]:
            name = command[0]
            meta = command[1]
            if name.startswith(word):
                yield Completion(
                    name,
                    start_position=-len(context.word),
                    display=name,
                    display_meta=meta,
                ) 