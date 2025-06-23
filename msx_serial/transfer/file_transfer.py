"""
MSX Serial Terminal File Transfer Processing
"""

import time
import base64
import chardet
from pathlib import Path
from tqdm import tqdm
from typing import TYPE_CHECKING, Optional, Union, BinaryIO, TextIO

from .basic_sender import send_basic_program
from ..common.color_output import print_info, print_exception
from ..connection.base import Connection

if TYPE_CHECKING:
    from ..core.optimized_session import OptimizedMSXTerminalSession


class FileTransferManager:
    """File transfer manager with simplified operations"""

    def __init__(self, connection: Connection, encoding: str):
        """Initialize file transfer manager"""
        self.connection = connection
        self.encoding = encoding
        self.chunk_size = 1024
        self.timeout = 10.0
        self.terminal: Optional["OptimizedMSXTerminalSession"] = None

    def set_terminal(self, terminal: Optional["OptimizedMSXTerminalSession"]) -> None:
        """Set terminal instance reference"""
        self.terminal = terminal

    def paste_file(self, file_path: Union[Path, str]) -> None:
        """Paste file contents to MSX"""
        path = Path(file_path)
        if not path.exists():
            print_exception("File not found", FileNotFoundError(str(path)))
            return

        try:
            encoding = self._detect_encoding(path)
            self._send_file_lines(path, encoding)
        except Exception as e:
            print_exception("Failed to paste file", e)

    def _detect_encoding(self, file_path: Path) -> str:
        """Detect file encoding"""
        with file_path.open("rb") as f:
            raw = f.read()
            detected = chardet.detect(raw)
            return detected.get("encoding", "utf-8")

    def _send_file_lines(self, file_path: Path, encoding: str) -> None:
        """Send file line by line"""
        with file_path.open("r", encoding=encoding) as f:
            for line in f:
                self._send_line(line.rstrip())

    def _send_line(self, line: str) -> None:
        """Send single line to MSX"""
        encoded_line = line.encode(self.encoding)
        self.connection.write(encoded_line)
        self.connection.flush()

    def _check_response(self, expected: str = ":? `") -> bool:
        """Check for expected response in buffer"""
        if not self.connection.in_waiting():
            return False

        try:
            data = self.connection.read(self.connection.in_waiting())
            text = data.decode(self.encoding)
            return expected in text
        except UnicodeDecodeError:
            return False

    def upload_file(self, file_path: str) -> None:
        try:
            # 出力を抑制
            if self.terminal:
                self.terminal.suppress_output = True

            # BASICプログラムのアップロード
            self.connection.write(
                send_basic_program(
                    "upload.bas",
                    {"filename": Path(file_path).name},
                ).encode("utf-8")
            )
            self.connection.flush()

            # BASICプログラムの実行
            self.connection.write(b"RUN\r\n")
            self.connection.flush()
            time.sleep(1)

            with open(file_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("ascii")
                with tqdm(total=len(encoded), desc="アップロード中", unit="B") as pbar:
                    for i in range(0, len(encoded), 76):
                        chunk = encoded[i : i + 76]
                        self.connection.write((chunk + "\r\n").encode("ascii"))
                        self.connection.flush()
                        pbar.update(len(chunk))
                        time.sleep(0.5)

            self.connection.write(b"`\r\n")
            self.connection.flush()
            print_info("アップロード完了")

        except Exception as e:
            print_exception("アップロード失敗", e)
        finally:
            # 出力抑制を解除
            if self.terminal:
                time.sleep(5)
                self.terminal.suppress_output = False
            self.connection.write(b"\r\nNEW\r\n")
            self.connection.flush()
