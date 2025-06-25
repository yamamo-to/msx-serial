"""
MSX Protocol Detection and Mode Management
"""

import re
from enum import Enum

from ..common.color_output import print_info


class MSXMode(Enum):
    """MSX動作モード"""

    UNKNOWN = "unknown"
    BASIC = "basic"
    DOS = "dos"


class MSXProtocolDetector:
    """MSXプロンプトを検出してモード状態を管理"""

    def __init__(self, debug_mode: bool = False):
        # 統一されたMSXプロンプトパターン
        # DOS: A>, B>, C>, etc. (全アルファベット対応)
        self.dos_prompt_pattern = re.compile(r"^[A-Z]>\s*$")
        # DOS with colon: A:>, B:>, C:>, etc.
        self.dos_colon_prompt_pattern = re.compile(r"^[A-Z]:>\s*$")
        # BASIC: Ok, Ready
        self.basic_prompt_pattern = re.compile(r"^(Ok|Ready)\s*$", re.IGNORECASE)
        # エラープロンプト: ?Redo from start
        self.error_prompt_pattern = re.compile(r"^\?Redo from start\s*$", re.IGNORECASE)

        # 統合されたプロンプトパターン（すべてを一度にチェック）
        self.unified_prompt_pattern = re.compile(
            r"^([A-Z]>|[A-Z]:>|Ok|Ready|\?Redo from start)\s*$", re.IGNORECASE
        )

        # 後方互換性のためのエイリアス
        self.prompt_pattern = self.dos_prompt_pattern

        self.current_mode = MSXMode.UNKNOWN.value
        self.debug_mode = debug_mode

    def _debug_print(self, message: str) -> None:
        """デバッグモードが有効な場合にデバッグメッセージを出力"""
        if self.debug_mode:
            print_info(f"[MSX Debug] {message}")

    def detect_prompt(self, buffer: str) -> bool:
        """Check if buffer contains a complete prompt

        Args:
            buffer: Text buffer to check

        Returns:
            True if prompt is detected
        """
        # Strip whitespace for prompt detection
        stripped_buffer = buffer.strip()

        # 統合されたパターンで単一行プロンプトをチェック
        single_line_result = bool(self.unified_prompt_pattern.search(stripped_buffer))

        if single_line_result:
            self._debug_print(
                f"detect_prompt('{buffer.strip()}') -> {single_line_result} (single-line)"
            )
            return single_line_result

        # Check for multi-line text ending with BASIC prompt
        if "\n" in stripped_buffer:
            lines = stripped_buffer.split("\n")
            last_line = lines[-1].strip()

            # Check if the last line is a BASIC prompt
            if self.basic_prompt_pattern.search(last_line):
                self._debug_print(
                    f"detect_prompt('{buffer.strip()}') -> True (multi-line BASIC)"
                )
                return True

            # Check if any line ending is a DOS prompt
            for line in lines:
                line = line.strip()
                if self.dos_prompt_pattern.search(
                    line
                ) or self.dos_colon_prompt_pattern.search(line):
                    self._debug_print(
                        f"detect_prompt('{buffer.strip()}') -> True (multi-line DOS)"
                    )
                    return True

        self._debug_print(f"detect_prompt('{buffer.strip()}') -> False")
        return False

    def is_prompt_candidate(self, buffer: str) -> bool:
        """Check if buffer might be an incomplete prompt

        Args:
            buffer: Text buffer to check

        Returns:
            True if buffer might be a prompt candidate
        """
        # 統合された部分プロンプトパターン
        partial_patterns = [
            r"^[A-Z]$",  # A, B, C, etc.
            r"^[A-Z]:$",  # A:, B:, C:, etc. (for DOS colon prompts)
            r"^O$",  # O (for Ok)
            r"^Ok$",  # Ok
            r"^R$",  # R (for Ready)
            r"^Re$",  # Re (for Ready)
            r"^Rea$",  # Rea (for Ready)
            r"^Read$",  # Read (for Ready)
            r"^Ready$",  # Ready
            r"^\?$",  # ? (for ?Redo from start)
            r"^\?R$",  # ?R (for ?Redo from start)
            r"^\?Redo$",  # ?Redo (for ?Redo from start)
        ]

        buffer = buffer.strip()
        # 大文字小文字を区別しない（BASICプロンプトのみ）か、厳密に大文字（DOSプロンプト）
        for pattern in partial_patterns:
            if pattern.startswith(r"^[A-Z"):  # DOS patterns - case sensitive
                if re.match(pattern, buffer):
                    return True
            else:  # BASIC patterns - case insensitive
                if re.match(pattern, buffer, re.IGNORECASE):
                    return True

        return False

    def detect_mode(self, prompt_text: str) -> MSXMode:
        """Detect MSX mode from prompt text

        Args:
            prompt_text: Prompt text to analyze

        Returns:
            Detected MSX mode
        """
        prompt_text = prompt_text.strip()

        # For multi-line text, check the last line for BASIC prompt
        if "\n" in prompt_text:
            lines = prompt_text.split("\n")
            last_line = lines[-1].strip()

            # If last line is BASIC prompt, this is BASIC mode
            if self.basic_prompt_pattern.search(last_line):
                self._debug_print(
                    f"BASIC mode detected from multi-line prompt (last line: '{last_line}')"
                )
                return MSXMode.BASIC

            # Check all lines for DOS prompts
            for line in lines:
                line = line.strip()
                if self.dos_prompt_pattern.search(
                    line
                ) or self.dos_colon_prompt_pattern.search(line):
                    self._debug_print(
                        f"DOS mode detected from multi-line prompt (line: '{line}')"
                    )
                    return MSXMode.DOS

            self._debug_print("Unknown mode from multi-line prompt")
            return MSXMode.UNKNOWN

        # Single line processing with optimized pattern matching
        self._debug_print(f"Pattern matching for '{prompt_text}':")

        if self.basic_prompt_pattern.search(prompt_text):
            self._debug_print(f"BASIC mode detected from prompt: '{prompt_text}'")
            return MSXMode.BASIC
        elif self.dos_prompt_pattern.search(
            prompt_text
        ) or self.dos_colon_prompt_pattern.search(prompt_text):
            self._debug_print(f"DOS mode detected from prompt: '{prompt_text}'")
            return MSXMode.DOS
        else:
            self._debug_print(f"Unknown mode from prompt: '{prompt_text}'")
            return MSXMode.UNKNOWN

    def update_mode(self, new_mode: MSXMode) -> bool:
        """Update current mode if different

        Args:
            new_mode: New mode to set

        Returns:
            True if mode was changed
        """
        if new_mode.value != self.current_mode:
            old_mode = self.current_mode
            self.current_mode = new_mode.value
            self._debug_print(f"Mode changed: {old_mode} -> {self.current_mode}")
            return True
        return False

    def force_mode_update(self, prompt_text: str) -> bool:
        """Force mode update based on prompt text

        Args:
            prompt_text: Prompt text to analyze

        Returns:
            True if mode was updated
        """
        detected_mode = self.detect_mode(prompt_text)
        if detected_mode != MSXMode.UNKNOWN:
            old_mode = self.current_mode
            self.current_mode = detected_mode.value
            self._debug_print(f"Force mode update: {old_mode} -> {self.current_mode}")
            return True
        return False

    def enable_debug(self) -> None:
        """デバッグモードを有効化"""
        self.debug_mode = True
        print_info("MSX protocol detection debug mode enabled")

    def disable_debug(self) -> None:
        """デバッグモードを無効化"""
        self.debug_mode = False
        print_info("MSX protocol detection debug mode disabled")
