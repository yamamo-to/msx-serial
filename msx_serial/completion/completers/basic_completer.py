"""
BASICモード用の補完機能
"""

import asyncio
import logging
from typing import Iterator, Optional

from prompt_toolkit.completion import CompleteEvent, Completion
from prompt_toolkit.document import Document

from msx_serial.common.config_manager import ConfigManager

from ..basic_filesystem import BASICFileSystemManager
from .base import BaseCompleter

logger = logging.getLogger(__name__)


def strip_quotes(text: str) -> str:
    """引用符を除去して返す"""
    if text.startswith('"') and text.endswith('"'):
        return text[1:-1]
    elif text.startswith('"'):
        return text[1:]
    return text


def create_completion(
    completion_text: str, description: str, start_position: int, current_word: str
) -> Completion:
    """補完候補を生成"""
    display_text = strip_quotes(completion_text)
    actual_completion = strip_quotes(completion_text)
    return Completion(
        actual_completion,
        start_position=start_position,
        display=display_text,
        display_meta=description,
    )


class BASICCompleter(BaseCompleter):
    """BASICモード用の補完機能"""

    def __init__(self, connection: Optional[object] = None) -> None:
        """初期化

        Args:
            connection: MSX接続オブジェクト
        """
        super().__init__()
        self.connection = connection
        self.filesystem_manager = BASICFileSystemManager(connection)
        self.last_refresh_time = 0.0
        self.refresh_interval = ConfigManager().get("basic.refresh_interval", 5.0)

    def set_connection(self, connection: object) -> None:
        """接続オブジェクトを設定

        Args:
            connection: MSX接続オブジェクト
        """
        self.connection = connection
        self.filesystem_manager.set_connection(connection)

    def set_current_directory(self, directory: str) -> None:
        """現在のディレクトリを設定

        Args:
            directory: 現在のディレクトリパス
        """
        self.filesystem_manager.set_current_directory(directory)

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterator[Completion]:
        """BASICコマンドの補完を提供

        Args:
            document: 入力ドキュメント
            complete_event: 補完イベント

        Yields:
            補完候補
        """
        command_line = document.text_before_cursor.strip()
        if not command_line:
            return

        # 引用符で終わる場合
        if command_line.endswith('"'):
            yield from self._handle_quoted_end(command_line)
            return

        # 引用符が含まれる場合
        if '"' in command_line:
            yield from self._handle_quoted_middle(command_line)
            return

        # 通常のコマンドライン解析
        yield from self._handle_normal_command(document, command_line)

    def _handle_quoted_end(self, command_line: str) -> Iterator[Completion]:
        """引用符で終わる場合の処理"""
        command_part = command_line[: command_line.find('"')].strip()
        if not command_part:
            return

        command = command_part.upper()
        file_completions = self.filesystem_manager.get_completions_for_command(
            command, "", 0
        )

        for completion_text, description in file_completions:
            yield create_completion(completion_text, description, 0, "")

    def _handle_quoted_middle(self, command_line: str) -> Iterator[Completion]:
        """引用符が含まれる場合の処理"""
        quote_pos = command_line.find('"')
        command_part = command_line[:quote_pos].strip()
        if not command_part:
            return

        command = command_part.upper()
        current_word = command_line[quote_pos + 1 :].strip()

        file_completions = self.filesystem_manager.get_completions_for_command(
            command, current_word, 0
        )

        for completion_text, description in file_completions:
            yield create_completion(
                completion_text, description, -len(current_word), current_word
            )

    def _handle_normal_command(
        self, document: Document, command_line: str
    ) -> Iterator[Completion]:
        """通常のコマンドライン処理"""
        command, args, arg_position = self.filesystem_manager.parse_basic_command_line(
            command_line
        )

        if not command or not (args or document.text_before_cursor.endswith(" ")):
            return

        current_word = self._extract_current_word(document, command_line)
        file_completions = self.filesystem_manager.get_completions_for_command(
            command, current_word, arg_position - 1 if args else 0
        )

        for completion_text, description in file_completions:
            yield create_completion(
                completion_text, description, -len(current_word), current_word
            )

    def _extract_current_word(self, document: Document, command_line: str) -> str:
        """現在の単語を抽出

        Args:
            document: 入力ドキュメント
            command_line: コマンドライン

        Returns:
            現在の単語
        """
        if command_line.endswith(" "):
            return ""

        words = command_line.split()
        if not words:
            return ""

        last_word = words[-1]
        return strip_quotes(last_word)

    def _trigger_background_refresh(self) -> None:
        """バックグラウンドでキャッシュ更新を試行"""
        try:
            loop = asyncio.get_running_loop()
            current_time = loop.time()
        except RuntimeError:
            return

        if current_time - self.last_refresh_time > self.refresh_interval:
            asyncio.create_task(self._background_refresh())
            self.last_refresh_time = current_time

    async def _background_refresh(self) -> None:
        """バックグラウンドでキャッシュを更新"""
        try:
            await self.filesystem_manager.refresh_file_cache()
        except OSError as e:
            logger.debug(f"バックグラウンド更新に失敗: {e}")
        except Exception as e:
            logger.warning(f"予期しないエラーでバックグラウンド更新に失敗: {e}")
