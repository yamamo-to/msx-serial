"""
MSXシリアルターミナル
MSXとのシリアル通信を行うターミナルプログラム
"""

from .msx_serial import MSXSerialTerminal, TerminalConfig, main
from ._version import __version__

__all__ = ["MSXSerialTerminal", "TerminalConfig", "main", "__version__"]