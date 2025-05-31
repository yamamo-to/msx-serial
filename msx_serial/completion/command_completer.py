"""
MSXシリアルターミナルのコマンド補完機能
"""

import re
from collections import defaultdict
from prompt_toolkit.completion import (
    Completer,
    Completion,
    PathCompleter,
    CompleteEvent,
)
from prompt_toolkit.document import Document
from typing import List, Set, Iterator, Optional, Dict, Tuple
from .loader_keyword import load_keywords
from .loader_iot_nodes import IotNodes
from ..input.commands import CommandType


class CompletionContext:
    """補完コンテキストを管理するクラス"""

    def __init__(self, text: str, word: str):
        self.text = text
        self.word = word
        self.is_rem_or_string = False
        self.is_special_command = False
        self.is_iot_command = False
        self.current_command: Optional[str] = None


class CommandCompleter(Completer):
    """MSXコマンドの補完を提供するクラス"""

    def __init__(self, special_commands: List[str]):
        """初期化

        Args:
            special_commands: 特殊コマンドのリスト
        """
        self.user_variables: Set[str] = set()
        self.device_list = IotNodes().get_node_names()
        self.msx_keywords = load_keywords()
        self.special_commands = special_commands
        self.iot_pattern = re.compile(
            r"(?:CALL\s+IOT(?:GET|SET|FIND)|"
            r'_IOT(?:GET|SET|FIND))\(\s*"([\w/,\s]*)$',
            re.VERBOSE,
        )
        self.path_completer = PathCompleter(
            expanduser=True,
            only_directories=True,
        )
        self._initialize_caches()

    def _initialize_caches(self) -> None:
        """キーワードキャッシュを初期化"""
        self.keyword_caches: Dict[str, Dict[str, List[str]]] = defaultdict(dict)
        self.sub_commands: List[str] = []

        for key, info in self.msx_keywords.items():
            if info["type"] == "subcommand":
                self.sub_commands.append(key)
            self.keyword_caches[key] = self._build_prefix_cache(info["keywords"])

    def _build_prefix_cache(
        self, keywords: List[List[str]]
    ) -> Dict[str, List[str]]:
        """プレフィックスキャッシュを構築

        Args:
            keywords: キーワードのリスト

        Returns:
            プレフィックスキャッシュ
        """
        cache: Dict[str, List[str]] = defaultdict(list)
        for keyword in keywords:
            name = keyword[0]
            for i in range(1, len(name) + 1):
                prefix = name[:i]
                cache[prefix].append(name)
        return cache

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterator[Completion]:
        """補完候補を取得

        Args:
            document: ドキュメント
            complete_event: 補完イベント

        Yields:
            補完候補
        """
        context = CompletionContext(
            document.text_before_cursor, document.get_word_before_cursor()
        )

        if not self._analyze_context(context):
            return

        if context.text.startswith("@cd "):
            yield from self._complete_cd_command(context, complete_event)
        elif context.text.startswith("@help "):
            yield from self._complete_help_command(context)
        elif context.is_special_command:
            yield from self._complete_special_commands(context)
        elif context.is_iot_command:
            yield from self._complete_iot_devices(context)
        elif context.current_command:
            yield from self._complete_command_keywords(context)
        else:
            yield from self._complete_general_keywords(context)

    def _analyze_context(self, context: CompletionContext) -> bool:
        """コンテキストを解析

        Args:
            context: 補完コンテキスト

        Returns:
            解析が成功したかどうか
        """
        if not context.text.strip():
            return False

        context.is_rem_or_string = bool(
            re.search(r"REM", context.text) or "'" in context.text
        )
        if context.is_rem_or_string:
            return False

        if context.text.startswith("@help "):
            context.is_special_command = False
            context.current_command = None
            return True

        context.is_special_command = context.text.startswith("@")
        context.is_iot_command = any(
            cmd in context.text for cmd in ["IOTGET", "IOTSET", "IOTFIND"]
        )

        # CALLコマンドの省略形を検出
        if context.text.startswith("_"):
            context.current_command = "CALL"
            return True

        # サブコマンドを持つコマンドを検出
        text_upper = context.text.upper()
        for command in self.sub_commands:
            if text_upper.startswith(command + " "):
                context.current_command = command
                return True

        return True

    def _complete_cd_command(
        self, context: CompletionContext, complete_event: CompleteEvent
    ) -> Iterator[Completion]:
        """@cdコマンドの補完候補を生成

        Args:
            context: 補完コンテキスト
            complete_event: 補完イベント

        Yields:
            補完候補
        """
        path_part = context.text[len("@cd"):].lstrip()
        path_document = Document(text=path_part, cursor_position=len(path_part))
        yield from self.path_completer.get_completions(path_document, complete_event)

    def _complete_special_commands(
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

    def _complete_iot_devices(self, context: CompletionContext) -> Iterator[Completion]:
        """IOTデバイスの補完候補を生成

        Args:
            context: 補完コンテキスト

        Yields:
            補完候補
        """
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

    def _complete_command_keywords(
        self, context: CompletionContext
    ) -> Iterator[Completion]:
        """コマンドキーワードの補完候補を生成

        Args:
            context: 補完コンテキスト

        Yields:
            補完候補
        """
        if not context.current_command:
            return

        command_info = self.msx_keywords[context.current_command]
        prefix = self._get_command_prefix(context)

        for keyword in command_info["keywords"]:
            name = keyword[0]
            meta = keyword[1]

            if name.startswith(prefix):
                display_name = self._get_display_name(context, name)
                yield Completion(
                    name,
                    start_position=-len(prefix),
                    display=display_name,
                    display_meta=meta,
                )

    def _get_command_prefix(self, context: CompletionContext) -> str:
        """コマンドのプレフィックスを取得

        Args:
            context: 補完コンテキスト

        Returns:
            コマンドのプレフィックス
        """
        if not context.current_command:
            return ""
        if context.current_command == "CALL" and context.text.startswith("_"):
            return context.text[1:].upper()
        command_len = len(context.current_command)
        return context.text[command_len:].lstrip().upper()

    def _get_display_name(self, context: CompletionContext, name: str) -> str:
        """表示名を取得

        Args:
            context: 補完コンテキスト
            name: キーワード名

        Returns:
            表示名
        """
        if context.current_command == "CALL" and context.text.startswith("_"):
            return f"_{name}"
        return name

    def _complete_general_keywords(
        self, context: CompletionContext
    ) -> Iterator[Completion]:
        """一般キーワードの補完候補を生成

        Args:
            context: 補完コンテキスト

        Yields:
            補完候補
        """
        word = context.word.upper()
        if context.text.startswith("@help "):
            word = self._get_help_word(context)

        for key, cache in self.keyword_caches.items():
            candidates = cache.get(word, [])
            for keyword in candidates:
                name, meta = self._get_keyword_info(keyword, key)
                yield Completion(
                    name,
                    start_position=-len(word),
                    display=name,
                    display_meta=meta,
                )

    def _get_help_word(self, context: CompletionContext) -> str:
        """@helpコマンドの補完ワードを取得

        Args:
            context: 補完コンテキスト

        Returns:
            補完ワード
        """
        help_args = context.text[6:].strip().split()
        if len(help_args) > 1:
            return help_args[-1].upper()
        return context.word.upper()

    def _get_keyword_info(self, keyword: str, key: str) -> Tuple[str, str]:
        """キーワード情報を取得

        Args:
            keyword: キーワード
            key: キー

        Returns:
            (キーワード名, メタ情報)のタプル
        """
        if isinstance(keyword, list):
            return keyword[0], keyword[1]
        return keyword, self.msx_keywords[key]["description"]

    def _complete_help_command(self, context: CompletionContext) -> Iterator[Completion]:
        """@helpコマンドの補完候補を生成

        Args:
            context: 補完コンテキスト

        Yields:
            補完候補
        """
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
