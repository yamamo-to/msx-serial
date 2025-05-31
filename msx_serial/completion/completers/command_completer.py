"""
コマンド補完機能
"""

from typing import Iterator, List
from prompt_toolkit.completion import Completion, CompleteEvent
from prompt_toolkit.document import Document

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
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterator[Completion]:
        context = CompletionContext(
            document.text_before_cursor,
            document.get_word_before_cursor(),
        )

        # IOTコマンドの後にコンマがある場合は補完をスキップ
        iot_commands = ("IOTGET", "IOTSET", "IOTFIND")
        if any(cmd in context.text for cmd in iot_commands):
            if "," in context.text:
                return
            yield from self.iot_completer.get_completions(document, complete_event)

        if context.text.startswith("@help"):
            yield from self.help_completer.get_completions(document, complete_event)
            return

        if context.text.startswith("@"):
            yield from self.special_completer.get_completions(document, complete_event)
            return

        # CALL + スペースの直後はCALLサブコマンドのみ
        if context.text.upper().startswith("CALL "):
            yield from self._complete_call_subcommands(context)
            return

        # _で始まる場合はCALLサブコマンドと同じ補完
        if context.text.startswith("_"):
            yield from self._complete_call_subcommands(context)
            return

        # それ以外はBASICキーワード
        yield from self._complete_general_keywords(context)

    def _complete_call_subcommands(
        self, context: CompletionContext
    ) -> Iterator[Completion]:
        word = context.word
        if word.startswith("_"):
            word = word[1:]
        for command in self.msx_keywords["CALL"]["keywords"]:
            name = command[0]
            meta = command[1]
            if name.startswith(word):
                yield Completion(
                    name,
                    start_position=-len(word),
                    display=name,
                    display_meta=meta,
                )

    def _complete_all_subcommands(
        self, context: CompletionContext
    ) -> Iterator[Completion]:
        word = context.word
        if not word.startswith("_"):
            word = "_" + word
        for cmd in self.sub_commands:
            for command in self.msx_keywords[cmd]["keywords"]:
                name = command[0]
                meta = command[1]
                if name.startswith(word):
                    completion_text = name[1:] if name.startswith("_") else name
                    yield Completion(
                        completion_text,
                        start_position=-len(context.word),
                        display=name,
                        display_meta=meta,
                    )

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
                completion_text = name[1:] if name.startswith("_") else name
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
        for command in self.msx_keywords["BASIC"]["keywords"]:
            name = command[0]
            meta = command[1]
            if name.startswith(word):
                yield Completion(
                    name,
                    start_position=-len(word),
                    display=name,
                    display_meta=meta,
                )
