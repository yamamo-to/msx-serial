"""
拡張ターミナル表示機能
"""

import subprocess
import sys
import time
from threading import RLock
from typing import Any, Dict


class EnhancedTerminalDisplay:
    """拡張ターミナル表示機能を提供するクラス"""

    def __init__(self) -> None:
        self.last_output_time = time.time()
        self.total_bytes_displayed = 0
        self.performance_mode = "enhanced"
        self.stats = {
            "total_writes": 0,
            "instant_writes": 0,
            "buffered_writes": 0,
            "total_bytes": 0,
        }
        self._output_lock = RLock()

    def clear_screen(self) -> None:
        """画面クリア"""
        try:
            if sys.platform == "win32":
                subprocess.run(["cmd", "/c", "cls"], check=False, timeout=5)
            else:
                subprocess.run(["clear"], check=False, timeout=5)
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            # 画面クリアに失敗した場合は何もしない
            pass

    def print_receive(self, text: str, is_prompt: bool = False) -> None:
        """受信テキストの拡張表示

        Args:
            text: 表示テキスト
            is_prompt: プロンプトフラグ
        """
        formatted = text
        with self._output_lock:
            # Always write instantly
            self._write_instant(formatted)
            self.total_bytes_displayed += len(formatted.encode("utf-8"))
            self.last_output_time = time.time()

    def _write_instant(self, text: str) -> None:
        """即座にテキストを出力

        Args:
            text: 出力テキスト
        """
        sys.stdout.write(text)
        sys.stdout.flush()
        self.stats["instant_writes"] += 1

    def flush(self) -> None:
        """出力をフラッシュ"""
        sys.stdout.flush()

    def get_performance_stats(self) -> Dict[str, Any]:
        """パフォーマンス統計を取得

        Returns:
            統計情報の辞書
        """
        return self.stats.copy()
