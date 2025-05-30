from typing import Union
from .serial import SerialConfig, SerialConnection
from .telnet import TelnetConfig, TelnetConnection
from .dummy import DummyConfig, DummyConnection
from .base import BaseConnection


class ConnectionManager:
    def __init__(
        self,
        config: Union[SerialConfig, TelnetConfig, DummyConnection],
    ):
        self.config = config
        self.connection: BaseConnection = self._create_connection()

    def _create_connection(self) -> BaseConnection:
        if isinstance(self.config, SerialConfig):
            return SerialConnection(self.config)
        elif isinstance(self.config, TelnetConfig):
            return TelnetConnection(self.config)
        elif isinstance(self.config, DummyConfig):
            return DummyConnection(self.config)
        else:
            raise ValueError("不明な接続タイプ")

    def close(self):
        if self.connection and self.connection.is_open():
            self.connection.close()
