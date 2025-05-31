import serial
from dataclasses import dataclass
from typing import Optional, cast
from .base import Connection, ConnectionConfig


@dataclass
class SerialConfig(ConnectionConfig):
    port: str = ""
    baudrate: int = 115200
    bytesize: int = 8
    parity: str = "N"
    stopbits: int = 1
    timeout: Optional[float] = None
    xonxoff: bool = False
    rtscts: bool = False
    dsrdtr: bool = False


class SerialConnection(Connection):
    """シリアル接続クラス"""

    def __init__(self, config: SerialConfig):
        self.connection = serial.Serial(
            port=config.port,
            baudrate=config.baudrate,
            bytesize=config.bytesize,
            parity=config.parity,
            stopbits=config.stopbits,
            timeout=config.timeout,
            xonxoff=config.xonxoff,
            rtscts=config.rtscts,
            dsrdtr=config.dsrdtr,
        )

    def write(self, data: bytes) -> None:
        self.connection.write(data)

    def flush(self) -> None:
        self.connection.flush()

    def read(self, size: int) -> bytes:
        return cast(bytes, self.connection.read(size))

    def in_waiting(self) -> int:
        return cast(int, self.connection.in_waiting)

    def close(self) -> None:
        self.connection.close()

    def is_open(self) -> bool:
        return cast(bool, self.connection.is_open)
