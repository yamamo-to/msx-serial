"""
File management utilities for MSX terminal
"""

import base64
import chardet
from pathlib import Path
from typing import Optional, Callable, Iterator
from ..connection.base import Connection
from ..ui.color_output import print_info, print_exception


class FileReader:
    """File reading utilities with encoding detection"""

    @staticmethod
    def detect_encoding(file_path: Path) -> str:
        """Detect file encoding

        Args:
            file_path: Path to file

        Returns:
            Detected encoding
        """
        with open(file_path, "rb") as f:
            raw = f.read()
            result = chardet.detect(raw)
            return result["encoding"] or "utf-8"

    @staticmethod
    def read_text_file(
        file_path: Path, encoding: Optional[str] = None
    ) -> Iterator[str]:
        """Read text file line by line

        Args:
            file_path: Path to file
            encoding: Encoding to use, auto-detect if None

        Yields:
            Lines from file
        """
        if encoding is None:
            encoding = FileReader.detect_encoding(file_path)

        with open(file_path, "r", encoding=encoding) as f:
            for line in f:
                yield line.rstrip()

    @staticmethod
    def read_binary_file(file_path: Path) -> bytes:
        """Read binary file

        Args:
            file_path: Path to file

        Returns:
            File content as bytes
        """
        with open(file_path, "rb") as f:
            return f.read()


class DataEncoder:
    """Data encoding utilities"""

    @staticmethod
    def encode_base64(data: bytes) -> str:
        """Encode data as base64

        Args:
            data: Binary data

        Returns:
            Base64 encoded string
        """
        return base64.b64encode(data).decode("ascii")

    @staticmethod
    def chunk_data(data: str, chunk_size: int = 76) -> Iterator[str]:
        """Split data into chunks

        Args:
            data: Data to chunk
            chunk_size: Size of each chunk

        Yields:
            Data chunks
        """
        for i in range(0, len(data), chunk_size):
            yield data[i : i + chunk_size]


class TransferSession:
    """Manage file transfer session state"""

    def __init__(self, connection: Connection, encoding: str):
        self.connection = connection
        self.encoding = encoding
        self._suppress_callback: Optional[Callable[[bool], None]] = None

    def set_output_suppression_callback(self, callback: Callable[[bool], None]) -> None:
        """Set callback for output suppression

        Args:
            callback: Function to call with True/False for suppression
        """
        self._suppress_callback = callback

    def suppress_output(self, suppress: bool) -> None:
        """Suppress terminal output

        Args:
            suppress: Whether to suppress output
        """
        if self._suppress_callback:
            self._suppress_callback(suppress)

    def send_data(self, data: str) -> None:
        """Send data to connection

        Args:
            data: Data to send
        """
        self.connection.write(data.encode(self.encoding))
        self.connection.flush()

    def send_bytes(self, data: bytes) -> None:
        """Send raw bytes to connection

        Args:
            data: Bytes to send
        """
        self.connection.write(data)
        self.connection.flush()


class FileUploader:
    """Handle file upload operations"""

    def __init__(self, session: TransferSession):
        self.session = session
        self.chunk_size = 76

    def upload_as_base64(
        self,
        file_path: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> bool:
        """Upload file as base64

        Args:
            file_path: Path to file
            progress_callback: Callback for progress updates (current, total)

        Returns:
            True if successful
        """
        try:
            # Read and encode file
            data = FileReader.read_binary_file(file_path)
            encoded = DataEncoder.encode_base64(data)

            # Send data in chunks
            total_size = len(encoded)
            sent_size = 0

            for chunk in DataEncoder.chunk_data(encoded, self.chunk_size):
                self.session.send_data(f"{chunk}\r\n")
                sent_size += len(chunk)

                if progress_callback:
                    progress_callback(sent_size, total_size)

            # Send terminator
            self.session.send_data("`\r\n")
            return True

        except Exception as e:
            print_exception("Upload failed", e)
            return False

    def paste_text_file(self, file_path: Path, target_encoding: str) -> bool:
        """Paste text file content

        Args:
            file_path: Path to text file
            target_encoding: Encoding for transmission

        Returns:
            True if successful
        """
        try:
            for line in FileReader.read_text_file(file_path):
                encoded_line = line.encode(target_encoding)
                self.session.send_bytes(encoded_line)

            return True

        except Exception as e:
            print_exception("Paste failed", e)
            return False


class ProgressTracker:
    """Track upload progress"""

    def __init__(self, total: int, description: str = "Processing"):
        self.total = total
        self.current = 0
        self.description = description

    def update(self, amount: int) -> None:
        """Update progress

        Args:
            amount: Amount to add to current progress
        """
        self.current += amount
        percentage = (self.current / self.total) * 100 if self.total > 0 else 0
        print_info(
            f"{self.description}: {percentage:.1f}% ({self.current}/{self.total})"
        )

    def finish(self) -> None:
        """Mark progress as complete"""
        print_info(f"{self.description}: Complete")
