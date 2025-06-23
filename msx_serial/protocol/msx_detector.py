"""
MSX protocol detection and mode management
"""

import re
from ..modes import MSXMode
from ..ui.color_output import print_info


class MSXProtocolDetector:
    """Detect MSX prompts and manage mode state"""

    def __init__(self, debug_mode: bool = False):
        # MSX prompt patterns
        self.prompt_pattern = re.compile(r"^[A-Z]>\s*$")
        self.basic_prompt_pattern = re.compile(r"^Ok\s*$", re.IGNORECASE)
        self.dos_prompt_pattern = re.compile(r"^[A-Z]:>\s*$")

        self.current_mode = MSXMode.UNKNOWN.value
        self.debug_mode = debug_mode

    def _debug_print(self, message: str) -> None:
        """Print debug message if debug mode is enabled"""
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

        # Check for single-line prompts first
        single_line_result = bool(
            self.prompt_pattern.search(stripped_buffer)
            or self.basic_prompt_pattern.search(stripped_buffer)
            or self.dos_prompt_pattern.search(stripped_buffer)
        )

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
                if self.prompt_pattern.search(line) or self.dos_prompt_pattern.search(
                    line
                ):
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
        # Check for partial prompts
        if re.match(r"^[A-Z]$", buffer):
            return True
        if re.match(r"^[A-Z]:$", buffer):
            return True
        if re.match(r"^O$", buffer, re.IGNORECASE):
            return True
        if re.match(r"^Ok$", buffer, re.IGNORECASE):
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
                if self.dos_prompt_pattern.search(line):
                    self._debug_print(
                        f"DOS mode detected from multi-line prompt (line: '{line}')"
                    )
                    return MSXMode.DOS
                elif self.prompt_pattern.search(line):
                    self._debug_print(
                        f"General DOS mode detected from multi-line prompt (line: '{line}')"
                    )
                    return MSXMode.DOS

            self._debug_print("Unknown mode from multi-line prompt")
            return MSXMode.UNKNOWN

        # Single line processing (original logic)
        # Debug each pattern match
        basic_match = self.basic_prompt_pattern.search(prompt_text)
        dos_match = self.dos_prompt_pattern.search(prompt_text)
        general_match = self.prompt_pattern.search(prompt_text)

        self._debug_print(f"Pattern matching for '{prompt_text}':")
        self._debug_print(f"  BASIC pattern (r'^Ok\\s*$'): {bool(basic_match)}")
        self._debug_print(f"  DOS pattern (r'^[A-Z]:>\\s*$'): {bool(dos_match)}")
        self._debug_print(f"  General pattern (r'^[A-Z]>\\s*$'): {bool(general_match)}")

        if basic_match:
            self._debug_print(f"BASIC mode detected from prompt: '{prompt_text}'")
            return MSXMode.BASIC
        elif dos_match:
            self._debug_print(f"DOS mode detected from prompt: '{prompt_text}'")
            return MSXMode.DOS
        elif general_match:
            # General prompt (A>, etc.) - assume MSX-DOS
            self._debug_print(f"General DOS mode detected from prompt: '{prompt_text}'")
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
            self._debug_print(
                f"Force mode update: {old_mode} -> {self.current_mode}"
            )
            return True
        return False

    def enable_debug(self) -> None:
        """Enable debug mode"""
        self.debug_mode = True
        print_info("MSX protocol detection debug mode enabled")

    def disable_debug(self) -> None:
        """Disable debug mode"""
        self.debug_mode = False
        print_info("MSX protocol detection debug mode disabled")
