"""
Tests for display module
"""

from unittest.mock import Mock, patch

from msx_serial.display.basic_display import TerminalDisplay


class TestTerminalDisplay:
    """Test TerminalDisplay class"""

    def setup_method(self):
        """Setup test"""
        self.display = TerminalDisplay()

    def test_init_default_color(self):
        """Test initialization with default color"""
        display = TerminalDisplay()
        assert display.receive_color == "#00ff00"

    def test_init_custom_color(self):
        """Test initialization with custom color"""
        display = TerminalDisplay("#ff0000")
        assert display.receive_color == "#ff0000"

    @patch("subprocess.run")
    def test_clear_screen_unix(self, mock_run):
        """Test clear screen on Unix systems"""
        with patch("sys.platform", "linux"):
            self.display.clear_screen()
            mock_run.assert_called_once_with(["clear"], check=False, timeout=5)

    @patch("subprocess.run")
    def test_clear_screen_windows(self, mock_run):
        """Test clear screen on Windows"""
        with patch("sys.platform", "win32"):
            self.display.clear_screen()
            mock_run.assert_called_once_with(
                ["cmd", "/c", "cls"], check=False, timeout=5
            )

    @patch("msx_serial.display.basic_display.print_formatted_text")
    def test_print_receive_regular(self, mock_print):
        """Test printing regular text"""
        self.display.print_receive("test message")
        mock_print.assert_called_once()
        args = mock_print.call_args[0][0]
        assert args[0][0] == "#00ff00"
        assert args[0][1] == "test message"

    @patch("msx_serial.display.basic_display.print_formatted_text")
    def test_print_receive_prompt(self, mock_print):
        """Test printing prompt text"""
        self.display.print_receive("A>", is_prompt=True)
        mock_print.assert_called_once()
        args = mock_print.call_args[0][0]
        assert args[0][0] == "#00ff00 bold"
        assert args[0][1] == "A>"

    @patch("os.get_terminal_size")
    @patch("msx_serial.display.basic_display.print_formatted_text")
    def test_print_receive_long_text(self, mock_print, mock_terminal_size):
        """Test printing text longer than terminal width"""
        mock_terminal_size.return_value = Mock(columns=10)

        long_text = "This is a very long text that should be wrapped"
        self.display.print_receive(long_text)

        mock_print.assert_called_once()
        args = mock_print.call_args[0][0]
        wrapped_text = args[0][1]

        # Text should be wrapped
        assert "\n" in wrapped_text
        lines = wrapped_text.split("\n")
        for line in lines:
            assert len(line) <= 10

    @patch("os.get_terminal_size")
    @patch("msx_serial.display.basic_display.print_formatted_text")
    def test_print_receive_terminal_size_error(self, mock_print, mock_terminal_size):
        """Test printing when terminal size cannot be determined"""
        mock_terminal_size.side_effect = OSError("Cannot get terminal size")

        test_text = "test message"
        self.display.print_receive(test_text)

        mock_print.assert_called_once()
        args = mock_print.call_args[0][0]
        assert args[0][1] == test_text  # Text should be unchanged

    def test_wrap_text_short(self):
        """Test wrapping short text"""
        with patch("os.get_terminal_size") as mock_size:
            mock_size.return_value = Mock(columns=50)
            result = self.display._wrap_text_if_needed("short")
            assert result == "short"

    def test_wrap_text_long(self):
        """Test wrapping long text"""
        with patch("os.get_terminal_size") as mock_size:
            mock_size.return_value = Mock(columns=5)
            result = self.display._wrap_text_if_needed("verylongtext")
            expected = "veryl\nongte\nxt"
            assert result == expected

    def test_wrap_text_os_error(self):
        """Test wrapping when OS error occurs"""
        with patch("os.get_terminal_size") as mock_size:
            mock_size.side_effect = OSError()
            result = self.display._wrap_text_if_needed("test")
            assert result == "test"
