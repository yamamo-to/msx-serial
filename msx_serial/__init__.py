"""
MSXシリアルターミナル
MSXとのシリアル通信を行うターミナルプログラム
"""

from .msx_serial import MSXSerialTerminal, TerminalConfig, main

__version__ = "0.1.0"
__all__ = ["MSXSerialTerminal", "TerminalConfig", "main"] 