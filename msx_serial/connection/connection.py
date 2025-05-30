from typing import Union, Optional
from urllib.parse import urlparse, parse_qs
from .serial import SerialConfig
from .telnet import TelnetConfig
from .dummy import DummyConfig

import serial


def detect_connection_type(uri: str) -> Union[TelnetConfig, SerialConfig]:
    """URI形式の接続先から接続タイプを判定する"""
    # URI形式でない場合は従来の形式として処理
    if "://" not in uri:
        # IPアドレス:ポート番号の形式をチェック
        if ":" in uri:
            host, port_str = uri.split(":")
            try:
                return TelnetConfig(host=host, port=int(port_str))
            except ValueError:
                pass

        # COMポートまたは/dev/ttyの形式をチェック
        if uri.startswith(("COM", "/dev/tty")):
            return SerialConfig(port=uri)

        # デフォルトはシリアル接続
        return SerialConfig(port=uri)

    # URI形式の解析
    try:
        parsed = urlparse(uri)
        scheme = parsed.scheme.lower()
        query = parse_qs(parsed.query)

        if scheme == "telnet":
            return TelnetConfig(
                host=parsed.hostname or "localhost",
                port=parsed.port or 23
            )
        elif scheme == "serial":
            return SerialConfig(
                port=parsed.netloc,
                baudrate=int(query.get("baudrate", ["115200"])[0]),
                bytesize=int(query.get("bytesize", ["8"])[0]),
                parity=query.get("parity", "N")[0],
                stopbits=int(query.get("stopbits", "1")),
                timeout=int(query["timeout"][0]) if "timeout" in query else None,
                xonxoff=bool(query.get("xonxoff", False)[0]),
                rtscts=bool(query.get("rtscts", False)[0]),
                dsrdtr=bool(query.get("dsrdtr", False)[0]),
            )
        elif scheme == "dummy":
            return DummyConfig()
        else:
            raise ValueError(f"未対応のスキーム: {scheme}")
    except Exception as e:
        raise ValueError(f"無効なURI形式: {uri} ({str(e)})")


class Connection:
    """シリアル接続クラス"""

    def __init__(
        self,
        port: str,
        baudrate: int = 9600,
        bytesize: int = serial.EIGHTBITS,
        parity: str = serial.PARITY_NONE,
        stopbits: int = serial.STOPBITS_ONE,
        timeout: Optional[float] = None,
        write_timeout: Optional[float] = None,
        inter_byte_timeout: Optional[float] = None
    ) -> None:
        """初期化

        Args:
            port: シリアルポート
            baudrate: ボーレート
            bytesize: データビット
            parity: パリティ
            stopbits: ストップビット
            timeout: タイムアウト
            write_timeout: 書き込みタイムアウト
            inter_byte_timeout: バイト間タイムアウト
        """
        self.serial = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=bytesize,
            parity=parity,
            stopbits=stopbits,
            timeout=timeout,
            write_timeout=write_timeout,
            inter_byte_timeout=inter_byte_timeout
        )

    def write(self, data: str) -> None:
        """データを書き込み

        Args:
            data: 書き込むデータ
        """
        self.serial.write(data.encode())

    def read_until(self, expected: str) -> str:
        """期待する文字列まで読み込み

        Args:
            expected: 期待する文字列

        Returns:
            読み込んだデータ
        """
        return self.serial.read_until(
            expected.encode()
        ).decode()

    def read_all(self) -> str:
        """すべてのデータを読み込み

        Returns:
            読み込んだデータ
        """
        return self.serial.read_all().decode()

    def close(self) -> None:
        """接続を閉じる"""
        self.serial.close()

    def is_open(self) -> bool:
        """接続が開いているかどうか

        Returns:
            接続が開いている場合はTrue
        """
        return self.serial.is_open
