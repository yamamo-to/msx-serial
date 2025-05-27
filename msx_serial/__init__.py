"""
MSXシリアルターミナル
MSXとのシリアル通信を行うターミナルプログラム
"""

from .msx_serial import MSXSerialTerminal, main
from ._version import __version__

__all__ = ["MSXSerialTerminal", "main", "__version__"]