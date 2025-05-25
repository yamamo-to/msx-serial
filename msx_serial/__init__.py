"""
MSXシリアルターミナル
MSXとのシリアル通信を行うターミナルプログラム
"""

from .msx_serial import MSXSerialTerminal, ConnectionConfig, main
from ._version import __version__

__all__ = ["MSXSerialTerminal", "ConnectionConfig", "main", "__version__"]