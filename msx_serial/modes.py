"""
MSXの動作モード定義
"""

from enum import Enum


class MSXMode(Enum):
    """MSXの動作モード"""

    UNKNOWN = "unknown"
    BASIC = "basic"
    DOS = "dos"
