# connection/dummy.py
import queue
from dataclasses import dataclass
from .base import Connection, ConnectionConfig


@dataclass
class DummyConfig(ConnectionConfig):
    """ダミー接続設定"""

    pass


class DummyConnection(Connection):
    """実際の接続なしで動作するダミー接続クラス"""

    def __init__(self, config: DummyConfig):
        self.config = config
        self._open = True
        self._read_buffer: queue.Queue[int] = queue.Queue()
        self._write_buffer: list[bytes] = []

        # 初期メッセージを受信バッファに入れる
        self._simulate_receive("Welcome to MSX Dummy Terminal\r\n")

    def _simulate_receive(self, text: str) -> None:
        """内部で受信したように見せかける"""
        for byte in text.encode("utf-8"):
            self._read_buffer.put(byte)

    def read(self, size: int = 1) -> bytes:
        data = bytearray()
        for _ in range(size):
            if self._read_buffer.empty():
                break
            data.append(self._read_buffer.get())
        return bytes(data)

    def write(self, data: bytes) -> None:
        self._write_buffer.append(data)
        # 書き込まれた内容を即座に「受信」に入れる（エコーバック）
        self._simulate_receive(data.decode("utf-8", errors="ignore"))

    def flush(self) -> None:
        pass  # ダミーなので何もしない

    def in_waiting(self) -> int:
        return self._read_buffer.qsize()

    def is_open(self) -> bool:
        return self._open

    def close(self) -> None:
        self._open = False

    def get_sent_data(self) -> list[bytes]:
        """テスト用：送信されたデータを取得"""
        return self._write_buffer
