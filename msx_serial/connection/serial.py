import serial
from dataclasses import dataclass
from .base import Connection


@dataclass
class SerialConfig:
    port: str = ""
    baudrate: int = 115200
    bytesize: int = 8
    parity: str = "N"
    stopbits: int = 1
    timeout: float = None
    xonxoff: bool = False
    rtscts: bool = False
    dsrdtr: bool = False


class SerialConnection(Connection):
    """シリアル接続クラス"""
    def __init__(self, config: SerialConfig):
        self.connection = serial.Serial(**config.__dict__)

    def write(self, data: bytes) -> None:
        self.connection.write(data)

    def flush(self) -> None:
        self.connection.flush()

    def read(self, size: int) -> bytes:
        return self.connection.read(size)

    def in_waiting(self) -> int:
        return self.connection.in_waiting

    def close(self) -> None:
        self.connection.close()

    def is_open(self) -> bool:
        return self.connection.is_open
