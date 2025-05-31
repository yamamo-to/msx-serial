from typing import Union, Dict, List
from urllib.parse import urlparse, parse_qs
from .serial import SerialConfig
from .telnet import TelnetConfig
from .dummy import DummyConfig


def detect_connection_type(uri: str) -> Union[
    TelnetConfig,
    SerialConfig,
    DummyConfig,
]:
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
        query: Dict[str, List[str]] = parse_qs(parsed.query)

        if scheme == "telnet":
            value = parsed.netloc.split(":")
            if len(value) == 2:
                host = value[0]
                port = int(value[1])
            else:
                host = value[0]
                port = 23
            return TelnetConfig(host=host, port=port)
        elif scheme == "serial":
            return SerialConfig(
                port=parsed.path,
                baudrate=int(query.get("baudrate", ["115200"])[0]),
                bytesize=int(query.get("bytesize", ["8"])[0]),
                parity=query.get("parity", ["N"])[0],
                stopbits=int(query.get("stopbits", ["1"])[0]),
                timeout=int(query["timeout"][0]) if "timeout" in query else None,
                xonxoff=bool(query.get("xonxoff", False)),
                rtscts=bool(query.get("rtscts", False)),
                dsrdtr=bool(query.get("dsrdtr", False)),
            )
        elif scheme == "dummy":
            return DummyConfig()
        else:
            raise ValueError(f"未対応のスキーム: {scheme}")
    except Exception as e:
        raise ValueError(f"無効なURI形式: {uri} ({str(e)})")
