import telnetlib
from dataclasses import dataclass
from .base import Connection, ConnectionConfig
from ..ui.color_output import print_exception


@dataclass
class TelnetConfig(ConnectionConfig):
    """Telnet接続設定"""

    port: int = 23
    host: str = "localhost"


class TelnetConnection(Connection):
    """Telnet接続クラス"""

    def __init__(self, config: TelnetConfig):
        self.connection = telnetlib.Telnet(**config.__dict__)
        self._buffer = bytearray()

    def write(self, data: bytes) -> None:
        self.connection.write(data)

    def flush(self) -> None:
        pass  # Telnetでは不要

    def read(self, size: int) -> bytes:
        try:
            # バッファにデータがない場合は新しいデータを読み取る
            if len(self._buffer) < size:
                # タイムアウトを設定してデータを読み取る
                new_data = self.connection.read_until(b"\n", timeout=0.1)
                if new_data:
                    self._buffer.extend(new_data)

            # バッファから要求されたサイズのデータを返す
            data = self._buffer[:size]
            self._buffer = self._buffer[size:]
            return bytes(data)
        except Exception as e:
            print_exception("Telnet読み取りエラー", e)
            return b""

    def in_waiting(self) -> int:
        try:
            # 新しいデータを確認
            new_data = self.connection.read_until(b"\n", timeout=0.1)
            if new_data:
                self._buffer.extend(new_data)
            return len(self._buffer)
        except Exception:
            return len(self._buffer)

    def close(self) -> None:
        self.connection.close()

    def is_open(self) -> bool:
        return True  # Telnet接続は常に開いていると仮定
