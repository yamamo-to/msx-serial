"""
Data processing utilities for MSX terminal
"""

import time
from typing import Optional, Tuple, List
from ..protocol.msx_detector import MSXProtocolDetector


class DataBuffer:
    """Buffer management for received data"""

    def __init__(self):
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
    """Process received data and detect prompts"""

    def __init__(self, protocol_detector: MSXProtocolDetector):
        self.detector = protocol_detector
        self.buffer = DataBuffer()

    def process_data(self, raw_data: str) -> List[Tuple[str, bool]]:
        """Process incoming data and return formatted output

        Args:
            raw_data: Raw received data

        Returns:
            List of (text, is_prompt) tuples
        """
        self.buffer.add_data(raw_data)
        output = []

        if self.detector.detect_prompt(self.buffer.get_content()):
            lines = self._split_prompt_data()
            output.extend(lines)
            self.buffer.clear()

        return output

    def check_timeout(self, timeout: float = 0.1) -> Optional[Tuple[str, bool]]:
        """Check for timeout and process buffered data

        Args:
            timeout: Timeout in seconds

        Returns:
            (text, is_prompt) tuple if timeout occurred, None otherwise
        """
        if self.buffer.has_content() and self.buffer.is_timeout(timeout):
            content = self.buffer.get_content()
            is_prompt = self.detector.detect_prompt(content)
            self.buffer.clear()
            return (content, is_prompt)

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
