import re
from typing import List
from prompt_toolkit.completion import Completer, Completion
from pygments_msxbasic.lexer import MSX_BASIC_KEYWORDS
from ..iot_nodes import IotNodes


class MSX0Completer(Completer):
    def __init__(self, special_commands: List[str]):
        self.user_variables = set()
        self.device_list = IotNodes().get_node_names()
        self.msx0_keywords = ["_IOTGET()", "_IOTSET()"]
        self.special_commands = special_commands

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        word = document.get_word_before_cursor()

        # @で始まるコマンドを優先的に表示
        if text.startswith("@"):
            for command in self.special_commands:
                if command.startswith(word):
                    yield Completion(command, start_position=-len(word))
            return

        # REM行や文字列は補完対象外
        if re.search(r'REM', text) or "'" in text:
            return

        match = re.search(r'_IOT[GS]ET\(\s*"([\w/,\s]*)$', text)
        if match:
            if "," not in text:
                prefix = match.group(1)
                for device in self.device_list:
                    if device.startswith(prefix):
                        yield Completion(
                            device + '"',
                            start_position=-len(prefix),
                            display=device,
                            display_meta='IOT device',
                        )
                return
        elif "_IOTGET" in text:
            return
        elif "_IOTSET" in text:
            return

        for keyword in self.msx0_keywords:
            if keyword.startswith(word.upper()):
                yield Completion(
                    keyword,
                    start_position=-len(word),
                    display_meta='MSX0 keyword'
                )

        # キーワード補完
        for keyword in MSX_BASIC_KEYWORDS:
            if keyword.startswith(word.upper()):
                yield Completion(
                    keyword,
                    start_position=-len(word),
                    display_meta='MSX BASIC keyword'
                )
