# connection/dummy.py
import queue
from dataclasses import dataclass
from .base import Connection, ConnectionConfig


@dataclass
class DummyConfig(ConnectionConfig):
    """Dummy connection configuration"""

    pass


class DummyConnection(Connection):
    """Dummy connection class that operates without actual connection"""

    def __init__(self, config: DummyConfig):
        self.config = config
        self._open = True
        self._read_buffer: queue.Queue[int] = queue.Queue()
        self._write_buffer: list[bytes] = []

        # Put initial message in receive buffer
        self._simulate_receive("Welcome to MSX Dummy Terminal\r\n")

    def _simulate_receive(self, text: str) -> None:
        """Simulate receiving data internally"""
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
        # Immediately put written content into "receive" (echo back)
        self._simulate_receive(data.decode("utf-8", errors="ignore"))

    def flush(self) -> None:
        pass  # No-op for dummy

    def in_waiting(self) -> int:
        return self._read_buffer.qsize()

    def is_open(self) -> bool:
        return self._open

    def close(self) -> None:
        self._open = False

    def get_sent_data(self) -> list[bytes]:
        """For testing: get sent data"""
        return self._write_buffer
