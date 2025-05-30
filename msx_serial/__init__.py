"""
MSXシリアルターミナル
MSXとのシリアル通信を行うターミナルプログラム
"""

from .terminal import MSXTerminal
from ._version import __version__
from .__main__ import main

__all__ = ["MSXTerminal", "__version__", "main"]
