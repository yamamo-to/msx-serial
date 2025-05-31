"""
IoTコマンドの補完機能
"""

import re
from typing import Iterator
from prompt_toolkit.completion import Completion, CompleteEvent
from prompt_toolkit.document import Document
from .base import BaseCompleter, CompletionContext
from ...util.loader_iot_nodes import IotNodes


class IoTCompleter(BaseCompleter):
    """IoTコマンドの補完を提供するクラス"""

    def __init__(self) -> None:
        """初期化"""
        super().__init__()
        self.iot_pattern = re.compile(
            r"(?:CALL\s+IOT(?:GET|SET|FIND)|"
            r'_IOT(?:GET|SET|FIND))\(\s*"([\w/,\s]*)$',
            re.VERBOSE,
        )
        self.device_list = IotNodes().get_node_names()

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterator[Completion]:
        """IOTデバイスの補完候補を生成

        Args:
            document: 補完コンテキストのドキュメント
            complete_event: 補完イベント

        Yields:
            補完候補
        """
        context = CompletionContext(
            document.text_before_cursor,
            document.get_word_before_cursor(),
        )

        match = self.iot_pattern.search(context.text)
        if not match or "," in context.text:
            return

        prefix = match.group(1)
        for device in self.device_list:
            if device.startswith(prefix):
                yield Completion(
                    device,
                    start_position=-len(prefix),
                    display=device,
                    display_meta="IOT device",
                )
