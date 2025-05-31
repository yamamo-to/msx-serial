"""
MSXシリアルターミナルの接続基底クラス
"""

from dataclasses import dataclass
from typing import Protocol


@dataclass
class ConnectionConfig:
    pass


class Connection(Protocol):
    """接続インターフェース"""

    def write(self, data: bytes) -> None: ...

    def flush(self) -> None: ...

    def read(self, size: int) -> bytes: ...

    def in_waiting(self) -> int: ...

    def close(self) -> None: ...

    def is_open(self) -> bool: ...
