"""
@helpコマンドの補完機能
"""

from typing import Iterator
from prompt_toolkit.completion import Completion, CompleteEvent
from prompt_toolkit.document import Document

from .base import BaseCompleter, CompletionContext


class HelpCompleter(BaseCompleter):
    """@helpコマンドの補完を提供するクラス"""

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterator[Completion]:
        context = CompletionContext(
            document.text_before_cursor,
            document.get_word_before_cursor(),
        )

        help_args = context.text[6:].strip().split()
        if not help_args:
            # 引数がない場合は、すべてのコマンドを候補として表示
            for key, info in self.msx_keywords["BASIC"]["keywords"]:
                yield Completion(
                    key,
                    start_position=0,
                    display=key,
                    display_meta=info,
                )
            return

        first_arg = help_args[0].upper()
        if first_arg.startswith("_"):
            first_arg = "CALL"
            if len(help_args) == 1:
                help_args = [first_arg, help_args[0][1:]]
            else:
                help_args = [first_arg] + help_args[1:]

        if first_arg in self.sub_commands:
            # サブコマンドを持つコマンドの場合
            if len(help_args) > 1:
                # 2つ目の引数がある場合は、そのサブコマンドのキーワードを補完
                prefix = help_args[-1].upper()
                command_info = self.msx_keywords[first_arg]
                for keyword in command_info["keywords"]:
                    name = keyword[0]
                    meta = keyword[1]
                    if name.startswith(prefix):
                        yield Completion(
                            name,
                            start_position=-len(prefix),
                            display=name,
                            display_meta=meta,
                        )
            else:
                # 2つ目の引数がない場合は、そのコマンドのサブコマンドを補完
                command_info = self.msx_keywords[first_arg]
                for keyword in command_info["keywords"]:
                    name = keyword[0]
                    meta = keyword[1]
                    yield Completion(
                        name,
                        start_position=0,
                        display=name,
                        display_meta=meta,
                    )
            return

        # 通常のコマンド補完
        prefix = help_args[-1].upper()
        for key, info in self.msx_keywords["BASIC"]["keywords"]:
            if key.upper().startswith(prefix):
                yield Completion(
                    key,
                    start_position=-len(prefix),
                    display=key,
                    display_meta=info,
                )
