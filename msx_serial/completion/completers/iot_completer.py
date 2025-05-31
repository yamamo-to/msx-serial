"""
IoTコマンドの補完機能
"""

from typing import Iterator
from prompt_toolkit.completion import Completion

from .base import BaseCompleter, CompletionContext


class IoTCompleter(BaseCompleter):
    """IoTコマンドの補完を提供するクラス"""

    def __init__(self) -> None:
        """初期化"""
        super().__init__()

    def get_completions(
        self, context: CompletionContext
    ) -> Iterator[Completion]:
        """IOTデバイスの補完候補を生成

        Args:
            context: 補完コンテキスト

        Yields:
            補完候補
        """
        word = context.word
        if not word.startswith("@"):
            word = "@" + word

        for command in self.msx_keywords["IOT"]["keywords"]:
            name = command[0]
            meta = command[1]
            if name.startswith(word):
                completion_text = (
                    name[1:] if name.startswith("@") else name
                )
                yield Completion(
                    completion_text,
                    start_position=-len(context.word),
                    display=name,
                    display_meta=meta,
                ) 