from typing import Union
from .serial import SerialConfig, SerialConnection
from .telnet import TelnetConfig, TelnetConnection
from .dummy import DummyConfig, DummyConnection
from .base import Connection, ConnectionConfig


class ConnectionManager:
    def __init__(
        self,
        config: ConnectionConfig,
    ) -> None:
        self.config = config
        self.connection: Connection = self._create_connection()

    def _create_connection(self) -> Union[
        SerialConnection,
        TelnetConnection,
        DummyConnection,
    ]:
        if isinstance(self.config, SerialConfig):
            return SerialConnection(self.config)
        elif isinstance(self.config, TelnetConfig):
            return TelnetConnection(self.config)
        elif isinstance(self.config, DummyConfig):
            return DummyConnection(self.config)
        else:
            raise ValueError("不明な接続タイプ")

    def close(self) -> None:
        if self.connection and self.connection.is_open():
            self.connection.close()
