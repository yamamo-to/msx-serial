"""
Tests for data sender module
"""

from unittest.mock import Mock, call

from msx_serial.io.data_sender import DataSender


class TestDataSender:
    """Test DataSender class"""

    def setup_method(self) -> None:
        """Setup test"""
        self.mock_connection = Mock()
        self.sender = DataSender(self.mock_connection, "utf-8")

    def test_init(self) -> None:
        """Test initialization"""
        assert self.sender.connection == self.mock_connection
        assert self.sender.encoding == "utf-8"

    def test_init_default_encoding(self) -> None:
        """Test initialization with default encoding"""
        sender = DataSender(self.mock_connection)
        assert sender.encoding == "msx-jp"

    def test_send_simple_text(self) -> None:
        """Test sending simple text"""
        self.sender.send("hello")

        self.mock_connection.write.assert_called_once_with(b"hello\r\n")
        self.mock_connection.flush.assert_called_once()

    def test_send_empty_string(self) -> None:
        """Test sending empty string"""
        self.sender.send("")

        self.mock_connection.write.assert_called_once_with(b"\r\n")
        self.mock_connection.flush.assert_called_once()

    def test_send_multiline_text(self) -> None:
        """Test sending multiline text"""
        self.sender.send("line1\nline2\nline3")

        expected_calls = [call(b"line1\r\n"), call(b"line2\r\n"), call(b"line3\r\n")]
        self.mock_connection.write.assert_has_calls(expected_calls)
        assert self.mock_connection.flush.call_count == 1

    def test_send_ctrl_c(self) -> None:
        """Test sending Ctrl+C"""
        self.sender.send("^C")

        self.mock_connection.write.assert_called_once_with(b"\x03")
        self.mock_connection.flush.assert_called_once()

    def test_send_escape(self) -> None:
        """Test sending Escape"""
        self.sender.send("^[")

        self.mock_connection.write.assert_called_once_with(b"\x1b")
        self.mock_connection.flush.assert_called_once()

    def test_send_ctrl_c_with_spaces(self) -> None:
        """Test sending Ctrl+C with spaces"""
        self.sender.send("  ^C  ")

        self.mock_connection.write.assert_called_once_with(b"\x03")
        self.mock_connection.flush.assert_called_once()

    def test_send_escape_with_spaces(self) -> None:
        """Test sending Escape with spaces"""
        self.sender.send("  ^[  ")

        self.mock_connection.write.assert_called_once_with(b"\x1b")
        self.mock_connection.flush.assert_called_once()

    def test_send_mixed_special_and_normal(self) -> None:
        """Test sending mixed special and normal text"""
        self.sender.send("hello\n^C\nnormal text")

        expected_calls = [call(b"hello\r\n"), call(b"\x03"), call(b"normal text\r\n")]
        self.mock_connection.write.assert_has_calls(expected_calls)
        assert self.mock_connection.flush.call_count == 1

    def test_send_with_custom_encoding(self) -> None:
        """Test sending with custom encoding"""
        sender = DataSender(self.mock_connection, "utf-8")
        sender.send("テスト")

        expected_data = "テスト\r\n".encode("utf-8")
        self.mock_connection.write.assert_called_once_with(expected_data)
        self.mock_connection.flush.assert_called_once()

    def test_send_whitespace_only_lines(self) -> None:
        """Test sending lines with only whitespace"""
        self.sender.send("   \n\t\n   ")

        expected_calls = [call(b"\r\n"), call(b"\r\n"), call(b"\r\n")]
        self.mock_connection.write.assert_has_calls(expected_calls)
        assert self.mock_connection.flush.call_count == 1

    def test_send_partial_control_sequences(self) -> None:
        """Test sending text that contains ^ but not control sequences"""
        self.sender.send("test^text^more")

        self.mock_connection.write.assert_called_once_with(b"test^text^more\r\n")
        self.mock_connection.flush.assert_called_once()
