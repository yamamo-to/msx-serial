"""
コマンド補完機能
"""

import logging
from typing import Iterator, List, Optional

from prompt_toolkit.completion import CompleteEvent, Completion
from prompt_toolkit.document import Document

from msx_serial.common.config_manager import ConfigManager

from .base import BaseCompleter, CompletionContext
from .basic_completer import BASICCompleter
from .dos_completer import DOSCompleter
from .help_completer import HelpCompleter
from .iot_completer import IoTCompleter
from .special_completer import SpecialCompleter

logger = logging.getLogger(__name__)


def create_keyword_completion(
    name: str, meta: str, word: str, prefix: str = ""
) -> Completion:
    """キーワード補完候補を生成"""
    completion_text = name[1:] if name.startswith("_") else name
    return Completion(
        completion_text,
        start_position=-len(word),
        display=name,
        display_meta=meta,
    )


class CommandCompleter(BaseCompleter):
    """コマンド補完を提供するクラス"""

    def __init__(
        self,
        special_commands: List[str],
        current_mode: str = "unknown",
        connection: Optional[object] = None,
    ) -> None:
        super().__init__()
        self.help_completer = HelpCompleter()
        self.special_completer = SpecialCompleter(special_commands)
        self.iot_completer = IoTCompleter()
        self.dos_completer = DOSCompleter(connection)
        self.basic_completer = BASICCompleter(connection)
        self.current_mode = current_mode
        self.connection = connection
        self._iot_commands = ConfigManager().get(
            "iot.commands", ["IOTGET", "IOTSET", "IOTFIND"]
        )

    def set_mode(self, mode: str) -> None:
        """現在のモードを設定

        Args:
            mode: モード（basic, dos, unknown）
        """
        self.current_mode = mode

    def set_connection(self, connection: object) -> None:
        """接続オブジェクトを設定

        Args:
            connection: MSX接続オブジェクト
        """
        self.connection = connection
        self.dos_completer.set_connection(connection)
        self.basic_completer.set_connection(connection)

    def set_current_directory(self, directory: str) -> None:
        """現在のディレクトリを設定（DOSモード用）

        Args:
            directory: 現在のディレクトリパス
        """
        self.dos_completer.set_current_directory(directory)
        self.basic_completer.set_current_directory(directory)

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterator[Completion]:
        """メイン補完メソッド - 複雑度を下げるため処理を分割"""
        context = CompletionContext(
            document.text_before_cursor,
            document.get_word_before_cursor(),
        )

        # IOTコマンドの補完チェック
        if self._should_complete_iot_commands(context):
            yield from self.iot_completer.get_completions(document, complete_event)
            return

        # @helpコマンドの補完
        if context.text.startswith("@help"):
            yield from self._complete_help_command(document, complete_event)
            return

        # 特殊コマンド（@で始まる）の補完
        if context.text.startswith("@"):
            yield from self._complete_special_commands(
                context, document, complete_event
            )
            return

        # CALLコマンドとその派生の補完
        if self._should_complete_call_commands(context):
            yield from self._complete_call_subcommands(context)
            return

        # モード別の一般的な補完
        yield from self._complete_mode_specific_commands(
            context, document, complete_event
        )

    def _should_complete_iot_commands(self, context: CompletionContext) -> bool:
        """IOTコマンドの補完が必要かチェック"""
        if any(cmd in context.text for cmd in self._iot_commands):
            return "," not in context.text
        return False

    def _complete_help_command(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterator[Completion]:
        """@helpコマンドの補完（BASICモードのみ）"""
        if self.current_mode == "basic":
            yield from self.help_completer.get_completions(document, complete_event)

    def _complete_special_commands(
        self,
        context: CompletionContext,
        document: Document,
        complete_event: CompleteEvent,
    ) -> Iterator[Completion]:
        """特殊コマンド（@で始まる）の補完"""
        # @modeコマンドの補完
        if self._should_complete_mode_command(context):
            yield Completion(
                "mode",
                start_position=-len(context.word),
                display="@mode",
                display_meta="MSXモードを表示・変更",
            )

        # その他の特殊コマンドも表示
        for completion in self.special_completer.get_completions(
            document, complete_event
        ):
            if completion.text != "mode":  # @modeとの重複を避ける
                yield completion

    def _should_complete_mode_command(self, context: CompletionContext) -> bool:
        """@modeコマンドの補完が必要かチェック"""
        # @modeプレフィックスチェック
        if "@mode".startswith(context.text):
            return True

        # mode補完チェック
        if context.word and "mode".startswith(context.word):
            return True

        return False

    def _should_complete_call_commands(self, context: CompletionContext) -> bool:
        """CALLコマンド系の補完が必要かチェック"""
        if self.current_mode != "basic":
            return False

        # CALLコマンドチェック
        if context.text.upper().startswith("CALL "):
            return True

        # アンダースコアコマンドチェック
        if context.text.startswith("_"):
            return True

        return False

    def _complete_mode_specific_commands(
        self,
        context: CompletionContext,
        document: Document,
        complete_event: CompleteEvent,
    ) -> Iterator[Completion]:
        """モード別の一般的なコマンド補完"""
        if self.current_mode == "basic":
            # BASICモード: BASICキーワードとファイル補完
            yield from self._complete_general_keywords(context)
            yield from self.basic_completer.get_completions(document, complete_event)
        elif self.current_mode == "dos":
            # DOSモード: DOSコマンドのみ（DOSCompleterが全判断を行う）
            yield from self.dos_completer.get_completions(document, complete_event)
        else:
            # 不明モード: すべてのコマンド
            yield from self._complete_general_keywords(context)
            yield from self.dos_completer.get_completions(document, complete_event)
            yield from self.basic_completer.get_completions(document, complete_event)

    def _complete_call_subcommands(
        self, context: CompletionContext
    ) -> Iterator[Completion]:
        """CALLサブコマンドの補完"""
        word = context.word[1:] if context.word.startswith("_") else context.word
        yield from self._complete_keywords_from_category("CALL", word)

    def _complete_all_subcommands(
        self, context: CompletionContext
    ) -> Iterator[Completion]:
        """全サブコマンドの補完"""
        word = context.word
        if not word.startswith("_"):
            word = "_" + word
        try:
            for cmd in self.sub_commands:
                yield from self._complete_keywords_from_category(
                    cmd, word, context.word
                )
        except AttributeError:
            logger.debug("sub_commandsが定義されていません")

    def _complete_command_keywords(
        self, context: CompletionContext
    ) -> Iterator[Completion]:
        """コマンドキーワードの補完"""
        word = context.word
        if not word.startswith("_"):
            word = "_" + word
        yield from self._complete_keywords_from_category("COMMAND", word, context.word)

    def _complete_general_keywords(
        self, context: CompletionContext
    ) -> Iterator[Completion]:
        """一般キーワードの補完"""
        yield from self._complete_keywords_from_category("BASIC", context.word)

    def _complete_keywords_from_category(
        self, category: str, word: str, original_word: str = ""
    ) -> Iterator[Completion]:
        """カテゴリ別キーワード補完の共通処理"""
        try:
            keywords = self.msx_keywords[category]["keywords"]
            for name, meta in keywords:
                if name.startswith(word):
                    yield create_keyword_completion(name, meta, original_word or word)
        except (KeyError, AttributeError) as e:
            logger.debug(f"キーワードカテゴリ '{category}' が見つかりません: {e}")
