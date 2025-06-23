"""
MSX protocol detection and mode management
"""

import re
from ..modes import MSXMode


class MSXProtocolDetector:
    """Detect MSX prompts and manage mode state"""

    def __init__(self):
        # MSX prompt patterns
        self.prompt_pattern = re.compile(r"^[A-Z]>\s*$")
        self.basic_prompt_pattern = re.compile(r"^Ok\s*$", re.IGNORECASE)
        self.dos_prompt_pattern = re.compile(r"^[A-Z]:>\s*$")

        self.current_mode = MSXMode.UNKNOWN.value

    def detect_prompt(self, buffer: str) -> bool:
        """Check if buffer contains a complete prompt

        Args:
            buffer: Text buffer to check

        Returns:
            True if prompt is detected
        """
        return bool(
            self.prompt_pattern.search(buffer)
            or self.basic_prompt_pattern.search(buffer)
            or self.dos_prompt_pattern.search(buffer)
        )

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
        if self.basic_prompt_pattern.search(prompt_text):
            return MSXMode.BASIC
        elif self.dos_prompt_pattern.search(prompt_text):
            return MSXMode.DOS
        elif self.prompt_pattern.search(prompt_text):
            # General prompt (A>, etc.) - assume MSX-DOS
            return MSXMode.DOS
        else:
            return MSXMode.UNKNOWN

    def update_mode(self, new_mode: MSXMode) -> bool:
        """Update current mode if different

        Args:
            new_mode: New mode to set

        Returns:
            True if mode was changed
        """
        if new_mode.value != self.current_mode:
            self.current_mode = new_mode.value
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
            self.current_mode = detected_mode.value
            return True
        return False
