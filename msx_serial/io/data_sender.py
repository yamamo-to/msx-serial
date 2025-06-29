"""
Data sender for terminal communication
"""

import logging
from typing import Optional, Protocol

from msx_serial.common.config_manager import ConfigManager

from ..connection.base import Connection

logger = logging.getLogger(__name__)


class DataProcessor(Protocol):
    """データプロセッサーのプロトコル"""

    def set_last_command(self, command: str) -> None: ...


class DataSender:
    """MSXへのデータ送信処理"""

    def __init__(self, connection: Connection, encoding: Optional[str] = None) -> None:
        self.connection = connection
        self.encoding = encoding or ConfigManager().get("connection.encoding", "msx-jp")
        self.data_processor: Optional[DataProcessor] = None
        self._special_chars = {
            "^C": b"\x03",
            "^[": b"\x1b",
        }

    def set_data_processor(self, processor: DataProcessor) -> None:
        """Set reference to data processor for echo detection

        Args:
            processor: DataProcessor instance
        """
        self.data_processor = processor

    def send(self, user_input: str) -> None:
        """ユーザー入力をMSXに送信"""
        try:
            if self.data_processor:
                self.data_processor.set_last_command(user_input.strip())

            lines = user_input.splitlines()
            if not lines:
                self._send_line("")
                self.connection.flush()
                return

            for line in lines:
                self._send_line(line)

            self.connection.flush()

        except Exception as e:
            logger.error(f"データ送信に失敗: {e}")
            raise

    def _send_line(self, line: str) -> None:
        """1行を送信"""
        line = line.strip()

        if line in self._special_chars:
            self.connection.write(self._special_chars[line])
        else:
            encoded_line = (line + "\r\n").encode(self.encoding)
            self.connection.write(encoded_line)
