"""
@helpコマンドの補完機能
"""

from typing import Iterator

from prompt_toolkit.completion import CompleteEvent, Completion
from prompt_toolkit.document import Document

from .base import BaseCompleter, CompletionContext


class HelpCompleter(BaseCompleter):
    """@helpコマンドの補完を提供するクラス"""

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterator[Completion]:
        """メイン補完メソッド - 複雑度を下げるため処理を分割"""
        context = CompletionContext(
            document.text_before_cursor,
            document.get_word_before_cursor(),
        )

        help_args = context.text[6:].strip().split()
        if not help_args:
            yield from self._complete_all_basic_keywords()
            return

        first_arg = self._normalize_first_arg(help_args)

        if first_arg in self.sub_commands:
            yield from self._complete_subcommand_keywords(help_args, first_arg)
        else:
            yield from self._complete_general_keywords(help_args)

    def _complete_all_basic_keywords(self) -> Iterator[Completion]:
        """引数がない場合のすべてのBASICキーワード補完"""
        for key, info in self.msx_keywords["BASIC"]["keywords"]:
            yield Completion(
                key,
                start_position=0,
                display=key,
                display_meta=info,
            )

    def _normalize_first_arg(self, help_args: list[str]) -> str:
        """第一引数の正規化（_プレフィックス処理）"""
        first_arg = help_args[0].upper()
        if first_arg.startswith("_"):
            # _で始まる場合はCALLサブコマンドとして扱う
            original_first_arg = first_arg
            first_arg = "CALL"
            if len(help_args) == 1:
                help_args.clear()
                help_args.extend([first_arg, original_first_arg[1:]])
            else:
                help_args[0] = first_arg
        return first_arg

    def _complete_subcommand_keywords(
        self, help_args: list[str], first_arg: str
    ) -> Iterator[Completion]:
        """サブコマンドを持つコマンドの補完"""
        command_info = self.msx_keywords[first_arg]

        if len(help_args) > 1:
            # 2つ目の引数がある場合のプレフィックス補完
            yield from self._complete_with_prefix(
                command_info["keywords"], help_args[-1].upper()
            )
        else:
            # 2つ目の引数がない場合の全サブコマンド補完
            yield from self._complete_all_keywords(command_info["keywords"])

    def _complete_general_keywords(self, help_args: list[str]) -> Iterator[Completion]:
        """通常のコマンド補完"""
        prefix = help_args[-1].upper()
        yield from self._complete_with_prefix(
            self.msx_keywords["BASIC"]["keywords"], prefix
        )

    def _complete_with_prefix(
        self, keywords: list, prefix: str
    ) -> Iterator[Completion]:
        """プレフィックスマッチング補完"""
        for keyword in keywords:
            name = keyword[0]
            meta = keyword[1]
            if name.upper().startswith(prefix):
                yield Completion(
                    name,
                    start_position=-len(prefix),
                    display=name,
                    display_meta=meta,
                )

    def _complete_all_keywords(self, keywords: list) -> Iterator[Completion]:
        """全キーワード補完"""
        for keyword in keywords:
            name = keyword[0]
            meta = keyword[1]
            yield Completion(
                name,
                start_position=0,
                display=name,
                display_meta=meta,
            )
