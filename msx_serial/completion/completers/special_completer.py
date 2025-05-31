"""
特殊コマンドの補完機能
"""

from typing import Iterator, List
from prompt_toolkit.completion import Completion, CompleteEvent
from prompt_toolkit.document import Document
from prompt_toolkit.completion.filesystem import PathCompleter

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
        self.path_completer = PathCompleter()

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterator[Completion]:
        context = CompletionContext(
            document.text_before_cursor,
            document.get_word_before_cursor(),
        )

        word = context.word
        if not word.startswith("@"):
            word = "@" + word

        # @cdコマンドの補完
        if context.text.startswith("@cd "):
            # @cdの後のパス部分を取得
            path = context.text[4:].strip()
            # パス補完用の新しいDocumentを作成
            path_document = Document(path)
            # パス補完を実行
            yield from self.path_completer.get_completions(
                path_document, complete_event
            )
            return

        # @encodeコマンドの補完
        if context.text.startswith("@encode "):
            yield from self._complete_encode_command(context)
            return

        # その他の特殊コマンドの補完
        for command in self.special_commands:
            if command.startswith(word):
                completion_text = command[1:] if command.startswith("@") else command
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
