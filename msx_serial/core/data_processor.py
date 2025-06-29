"""
Data processing utilities for MSX terminal
"""

import logging
import time
from typing import List, Optional, Protocol, Tuple

from msx_serial.common.config_manager import ConfigManager

from ..protocol.msx_detector import MSXProtocolDetector

logger = logging.getLogger(__name__)


class FileSystemManager(Protocol):
    """ファイルシステムマネージャーのプロトコル"""

    current_directory: str
    directory_cache: dict
    cache_timestamps: dict
    file_cache: list
    cache_timestamp: float

    def parse_dir_output(self, output: str) -> List[str]: ...

    def parse_files_output(self, output: str) -> List[str]: ...


class DOSFileSystemManager(FileSystemManager):
    """DOSファイルシステムマネージャーのプロトコル"""

    pass


class BASICFileSystemManager(FileSystemManager):
    """BASICファイルシステムマネージャーのプロトコル"""

    pass


class OutputCollector:
    """出力収集の共通処理"""

    def __init__(self, manager: Optional[FileSystemManager], command_name: str) -> None:
        self.manager = manager
        self.command_name = command_name
        self.output_buffer = ""
        self.is_collecting = False

    def start_collection(self) -> None:
        """収集を開始"""
        self.is_collecting = True
        self.output_buffer = ""

    def process_output(self, data: str) -> None:
        """出力を処理"""
        if self.is_collecting:
            self.output_buffer += data

    def finalize_collection(self) -> None:
        """収集を完了しキャッシュを更新"""
        if not self.is_collecting or not self.manager:
            return

        try:
            if self.output_buffer.strip():
                if self.command_name == "DIR":
                    files = self.manager.parse_dir_output(self.output_buffer)
                    current_dir = self.manager.current_directory
                    self.manager.directory_cache[current_dir] = files
                    self.manager.cache_timestamps[current_dir] = time.time()
                    logger.info(
                        f"DIRコマンド出力を自動キャッシュ: {len(files)} 個のファイル/ディレクトリ"
                    )
                elif self.command_name == "FILES":
                    files = self.manager.parse_files_output(self.output_buffer)
                    self.manager.file_cache = files
                    self.manager.cache_timestamp = time.time()
                    logger.debug(
                        f"FILESコマンド出力を自動キャッシュ: {len(files)} 個のファイル"
                    )
        except Exception as e:
            logger.warning(f"{self.command_name}出力の自動キャッシュに失敗: {e}")
        finally:
            self.is_collecting = False
            self.output_buffer = ""


class DataBuffer:
    """受信データのバッファ管理"""

    def __init__(self) -> None:
        self.buffer = ""
        self.last_update_time = 0.0

    def add_data(self, data: str) -> None:
        """Add new data to buffer

        Args:
            data: New data to add
        """
        self.buffer += data
        self.last_update_time = time.time()

    def clear(self) -> None:
        """Clear the buffer"""
        self.buffer = ""

    def get_content(self) -> str:
        """Get buffer content

        Returns:
            Current buffer content
        """
        return self.buffer

    def is_timeout(self, timeout: float) -> bool:
        """Check if buffer has timed out

        Args:
            timeout: Timeout in seconds

        Returns:
            True if timed out
        """
        return (time.time() - self.last_update_time) > timeout

    def has_content(self) -> bool:
        """Check if buffer has content

        Returns:
            True if buffer has content
        """
        return bool(self.buffer.strip())


class DataProcessor:
    """受信データの処理とプロンプト検出"""

    def __init__(
        self, protocol_detector: MSXProtocolDetector, instant_mode: bool = False
    ) -> None:
        self.detector = protocol_detector
        self.buffer = DataBuffer()
        self.instant_mode = instant_mode
        self.last_sent_command: Optional[str] = None
        self.echo_suppressed = False
        self.last_prompt_content = ""

        # 出力収集機能
        self.dos_collector: Optional[OutputCollector] = None
        self.basic_collector: Optional[OutputCollector] = None
        self._basic_keywords = ConfigManager().get(
            "basic.keywords", ["BASIC", "Microsoft", "Copyright", "Bytes free", "MSX"]
        )

    def set_dos_filesystem_manager(
        self, manager: Optional[DOSFileSystemManager]
    ) -> None:
        """DOSFileSystemManagerの参照を設定

        Args:
            manager: DOSFileSystemManagerインスタンス
        """
        self.dos_collector = OutputCollector(manager, "DIR") if manager else None

    def set_basic_filesystem_manager(
        self, manager: Optional[BASICFileSystemManager]
    ) -> None:
        """BASICFileSystemManagerの参照を設定

        Args:
            manager: BASICFileSystemManagerインスタンス
        """
        self.basic_collector = OutputCollector(manager, "FILES") if manager else None

    def set_instant_mode(self, enabled: bool) -> None:
        """Enable or disable instant mode

        Args:
            enabled: True to enable instant mode
        """
        self.instant_mode = enabled

    def set_last_command(self, command: str) -> None:
        """Set the last sent command for echo detection

        Args:
            command: Last command sent to MSX
        """
        self.last_sent_command = command.strip()
        self.echo_suppressed = False  # Reset echo suppression

        # 出力収集を開始
        if self.last_sent_command.upper() == "DIR" and self.dos_collector:
            self.dos_collector.start_collection()
        elif self.last_sent_command.upper() == "FILES" and self.basic_collector:
            self.basic_collector.start_collection()

    def process_data(self, raw_data: str) -> List[Tuple[str, bool]]:
        """Process incoming data and return formatted output

        Args:
            raw_data: Raw received data

        Returns:
            List of (text, is_prompt) tuples
        """
        # 出力収集
        if self.dos_collector:
            self.dos_collector.process_output(raw_data)
        if self.basic_collector:
            self.basic_collector.process_output(raw_data)

        if self.instant_mode:
            return self._process_data_instant(raw_data)
        else:
            return self._process_data_buffered(raw_data)

    def _process_data_instant(self, raw_data: str) -> List[Tuple[str, bool]]:
        """Process data in instant mode - immediate display + simultaneous buffering

        Args:
            raw_data: Raw received data

        Returns:
            List of (text, is_prompt) tuples
        """
        output = []

        self._debug_received_data(raw_data)

        # Always display received data immediately (core principle)
        if self.echo_suppressed or not self.last_sent_command:
            output.append((raw_data, False))

        # Add to buffer for prompt detection
        self.buffer.add_data(raw_data)
        current_content = self.buffer.get_content()

        # Handle command echo suppression
        if self._should_suppress_echo(current_content):
            self._process_echo_suppression(current_content)

        # Check for prompt detection (for mode detection only)
        if self.detector.detect_prompt(current_content):
            self._finalize_output_collections()
            self.last_prompt_content = current_content
            self.buffer.clear()
            output.append(("", True))

        return output

    def _debug_received_data(self, raw_data: str) -> None:
        """Debug output for received data"""
        if hasattr(self.detector, "debug_mode") and self.detector.debug_mode:
            # Debug output removed for cleaner production code
            pass

    def _should_suppress_echo(self, current_content: str) -> bool:
        """Check if echo should be suppressed"""
        return bool(
            self.last_sent_command
            and not self.echo_suppressed
            and self.last_sent_command in current_content
        )

    def _process_echo_suppression(self, current_content: str) -> None:
        """Process command echo suppression"""
        self.echo_suppressed = True
        if self.last_sent_command:
            command_end = current_content.find(self.last_sent_command) + len(
                self.last_sent_command
            )
        else:
            command_end = 0

        if command_end < len(current_content):
            remaining = current_content[command_end:].lstrip("\r\n ")
            self.buffer.clear()
            if remaining:
                self.buffer.add_data(remaining)
        else:
            self.buffer.clear()

    def _process_data_buffered(self, raw_data: str) -> List[Tuple[str, bool]]:
        """Process data in buffered mode - original behavior

        Args:
            raw_data: Raw received data

        Returns:
            List of (text, is_prompt) tuples
        """
        self.buffer.add_data(raw_data)
        output = []

        if self.detector.detect_prompt(self.buffer.get_content()):
            self._finalize_output_collections()
            lines = self._split_prompt_data()
            output.extend(lines)
            self.buffer.clear()

        return output

    def _finalize_output_collections(self) -> None:
        """出力収集を完了"""
        if self.dos_collector:
            self.dos_collector.finalize_collection()
        if self.basic_collector:
            self.basic_collector.finalize_collection()

    def _is_likely_prompt(self, content: str) -> bool:
        """Check if content looks like a complete prompt

        Args:
            content: Content to check

        Returns:
            True if looks like a complete prompt
        """
        content = content.strip()

        # プロトコル検出器の統一されたパターンを使用
        if self.detector.unified_prompt_pattern.search(content):
            return True

        # Check for BASIC message ending with Ok
        if content.endswith("Ok"):
            return self._has_basic_keywords(content)

        return False

    def _get_prompt_patterns(self) -> list[str]:
        """Get list of MSX prompt patterns"""
        # 正規表現を使った統一されたプロンプトパターン
        # この方法はより簡潔で保守しやすい
        prompt_patterns = []

        # MSX-DOSプロンプト: A>, B>, C>, ..., Z>
        for drive in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            prompt_patterns.append(f"{drive}>")

        # MSX-DOSプロンプト（コロン付き）: A:>, B:>, C:>, ..., Z:>
        for drive in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            prompt_patterns.append(f"{drive}:>")

        # BASICプロンプト
        prompt_patterns.extend(["Ok", "Ready"])

        # エラープロンプト
        prompt_patterns.append("?Redo from start")

        return prompt_patterns

    def _has_basic_keywords(self, content: str) -> bool:
        """Check if content contains BASIC-related keywords"""
        content_upper = content.upper()
        return any(keyword.upper() in content_upper for keyword in self._basic_keywords)

    def check_timeout(self, timeout: float = 0.1) -> Optional[Tuple[str, bool]]:
        """Check for timeout and process buffered data

        Args:
            timeout: Timeout in seconds

        Returns:
            (text, is_prompt) tuple if timeout occurred, None otherwise
        """
        if self.instant_mode:
            # In instant mode, only check for prompt detection to trigger mode changes
            if self.buffer.has_content() and self.buffer.is_timeout(timeout):
                content = self.buffer.get_content()
                is_prompt = self.detector.detect_prompt(content)

                if is_prompt:
                    # Save prompt content for mode detection and clear buffer
                    self.last_prompt_content = content
                    self.buffer.clear()
                    return ("", True)  # type: ignore  # Empty content to avoid duplication, but signal prompt
                else:
                    # Not a prompt - clear buffer (content already shown)
                    self.buffer.clear()
        else:
            # Original buffered behavior
            if self.buffer.has_content() and self.buffer.is_timeout(timeout):
                content = self.buffer.get_content()
                is_prompt = self.detector.detect_prompt(content)
                self.buffer.clear()
                return (content, is_prompt)

        return None

    def get_last_prompt_for_mode_detection(self) -> Optional[str]:
        """Get the last detected prompt content for mode detection

        Returns:
            Last prompt content if available, None otherwise
        """
        if self.last_prompt_content:
            content = self.last_prompt_content
            self.last_prompt_content = ""  # Clear after use
            return content
        return None

    def check_prompt_candidate(
        self, candidate_timeout: float = 0.02
    ) -> Optional[Tuple[str, bool]]:
        """Check for prompt candidate

        Args:
            candidate_timeout: Timeout for prompt candidates

        Returns:
            (text, is_prompt) tuple if candidate found, None otherwise
        """
        if self.instant_mode:
            # In instant mode, be more aggressive about prompt detection
            if self.buffer.has_content() and self.buffer.is_timeout(
                candidate_timeout * 0.5
            ):  # Faster timeout
                content = self.buffer.get_content()
                if self._is_likely_prompt(content):
                    is_prompt = self.detector.detect_prompt(content)
                    self.buffer.clear()
                    return (content, is_prompt)
        else:
            # Original behavior
            if (
                self.buffer.has_content()
                and self.detector.is_prompt_candidate(self.buffer.get_content())
                and self.buffer.is_timeout(candidate_timeout)
            ):
                content = self.buffer.get_content()
                is_prompt = self.detector.detect_prompt(content)
                self.buffer.clear()
                return (content, is_prompt)

        return None

    def _split_prompt_data(self) -> List[Tuple[str, bool]]:
        """Split buffer into lines and identify prompt

        Returns:
            List of (text, is_prompt) tuples
        """
        lines = self.buffer.get_content().split("\n")
        output = []

        # Add all lines except the last as regular data
        for line in lines[:-1]:
            if line.strip():
                output.append((line, False))

        # Check if last line is a prompt
        last_line = lines[-1]
        if last_line.strip():
            is_prompt = self.detector.detect_prompt(last_line)
            output.append((last_line, is_prompt))

        return output

    def has_incomplete_data(self) -> bool:
        """Check if there's incomplete data in buffer

        Returns:
            True if buffer has incomplete data
        """
        content = self.buffer.get_content()
        return bool(content) and "\n" not in content
