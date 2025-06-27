"""
Tests for EnhancedTerminalDisplay (enhanced_display.py)
"""

from unittest.mock import patch

from msx_serial.display.enhanced_display import EnhancedTerminalDisplay


class TestEnhancedTerminalDisplay:
    def setup_method(self):
        self.display = EnhancedTerminalDisplay()

    @patch("subprocess.run")
    def test_clear_screen_windows(self, mock_run):
        with patch("sys.platform", "win32"):
            self.display.clear_screen()
            mock_run.assert_called_once_with(
                ["cmd", "/c", "cls"], check=False, timeout=5
            )

    @patch("subprocess.run")
    def test_clear_screen_unix(self, mock_run):
        with patch("sys.platform", "linux"):
            self.display.clear_screen()
            mock_run.assert_called_once_with(["clear"], check=False, timeout=5)

    def test_print_receive_regular(self):
        with patch.object(self.display, "_write_instant") as mock_write:
            self.display.print_receive("hello")
            mock_write.assert_called_once_with("hello")

    def test_print_receive_prompt(self):
        with patch.object(self.display, "_write_instant") as mock_write:
            self.display.print_receive("A>", is_prompt=True)
            mock_write.assert_called_once_with("A>")

    def test_write_instant(self):
        with patch("sys.stdout") as mock_stdout:
            self.display._write_instant("test")
            mock_stdout.write.assert_called_with("test")
            mock_stdout.flush.assert_called()
            assert self.display.stats["instant_writes"] == 1

    def test_flush(self):
        with patch("sys.stdout") as mock_stdout:
            self.display.flush()
            mock_stdout.flush.assert_called()

    def test_get_performance_stats(self):
        stats = self.display.get_performance_stats()
        assert isinstance(stats, dict)
        assert "total_writes" in stats
        assert "instant_writes" in stats
        # 値は初期値
        assert stats["total_writes"] == 0
        assert stats["instant_writes"] == 0

    def test_thread_safety(self):
        # _output_lockがRLockであること
        assert type(self.display._output_lock).__name__ == "RLock"

    def test_stats_increment(self):
        with patch("sys.stdout"):
            # print_receiveを呼び出すと_write_instantが呼ばれる
            self.display.print_receive("test")
            assert self.display.stats["instant_writes"] == 1

            # 直接_write_instantを呼び出す
            self.display._write_instant("test")
            assert self.display.stats["instant_writes"] == 2

    def test_initialization(self):
        """Test proper initialization"""
        assert hasattr(self.display, "last_output_time")
        assert hasattr(self.display, "total_bytes_displayed")
        assert hasattr(self.display, "performance_mode")
        assert hasattr(self.display, "stats")
        assert hasattr(self.display, "_output_lock")

        # 初期値の確認
        assert self.display.performance_mode == "enhanced"
        assert self.display.total_bytes_displayed == 0
        assert isinstance(self.display.stats, dict)
