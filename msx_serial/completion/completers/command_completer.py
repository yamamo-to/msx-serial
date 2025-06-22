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
from .dos_completer import DOSCompleter


class CommandCompleter(BaseCompleter):
    """コマンド補完を提供するクラス"""

    def __init__(self, special_commands: List[str], current_mode: str = "unknown") -> None:
        super().__init__()
        self.help_completer = HelpCompleter()
        self.special_completer = SpecialCompleter(special_commands)
        self.iot_completer = IoTCompleter()
        self.dos_completer = DOSCompleter()
        self.current_mode = current_mode

    def set_mode(self, mode: str) -> None:
        """現在のモードを設定

        Args:
            mode: モード（basic, dos, unknown）
        """
        self.current_mode = mode

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
            # @helpコマンドはBASICモードでのみ表示
            if self.current_mode == "basic":
                yield from self.help_completer.get_completions(document, complete_event)
            return

        if context.text.startswith("@"):
            # @modeコマンドは全モードで利用可能
            # context.wordには@が含まれていない場合があるので、context.textから判定
            if "@mode".startswith(context.text) or (context.word and "mode".startswith(context.word)):
                yield Completion(
                    "mode",
                    start_position=-len(context.word),
                    display="@mode",
                    display_meta="MSXモードを表示・変更",
                )
            
            # その他の特殊コマンドはBASICモードでのみ表示（@modeは除外）
            if self.current_mode == "basic":
                # @modeコマンドと重複しないようにフィルタリング
                for completion in self.special_completer.get_completions(document, complete_event):
                    if completion.text != "mode":
                        yield completion
            return

        # CALL + スペースの直後はCALLサブコマンドのみ（BASICモードのみ）
        if context.text.upper().startswith("CALL ") and self.current_mode == "basic":
            yield from self._complete_call_subcommands(context)
            return

        # _で始まる場合はCALLサブコマンドと同じ補完（BASICモードのみ）
        if context.text.startswith("_") and self.current_mode == "basic":
            yield from self._complete_call_subcommands(context)
            return

        # モードに応じた補完
        if self.current_mode == "basic":
            # BASICモード: BASICキーワードと特殊コマンド
            yield from self._complete_general_keywords(context)
        elif self.current_mode == "dos":
            # DOSモード: DOSコマンド
            yield from self.dos_completer.get_completions(document, complete_event)
        else:
            # 不明モード: すべてのコマンド
            yield from self._complete_general_keywords(context)
            yield from self.dos_completer.get_completions(document, complete_event)

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
