"""
MSXシリアルターミナルの接続基底クラス
"""

from abc import ABC, abstractmethod
from typing import Optional, Union, BinaryIO
from ..input.commands import CommandType


class BaseConnection(ABC):
    """接続基底クラス"""

    @abstractmethod
    def connect(self) -> None:
        """接続を開始する"""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """接続を切断する"""
        pass

    @abstractmethod
    def send(self, data: Union[str, bytes]) -> None:
        """データを送信する

        Args:
            data: 送信するデータ
        """
        pass

    @abstractmethod
    def receive(self, size: Optional[int] = None) -> bytes:
        """データを受信する

        Args:
            size: 受信するデータサイズ

        Returns:
            受信したデータ
        """
        pass

    @abstractmethod
    def send_file(self, file: BinaryIO) -> None:
        """ファイルを送信する

        Args:
            file: 送信するファイル
        """
        pass

    @abstractmethod
    def receive_file(self, file: BinaryIO) -> None:
        """ファイルを受信する

        Args:
            file: 受信するファイル
        """
        pass

    @abstractmethod
    def execute_command(self, command: CommandType) -> None:
        """コマンドを実行する

        Args:
            command: 実行するコマンド
        """
        pass