"""
Tests for user interface module
"""

import threading
from unittest.mock import Mock, patch
from msx_serial.io.user_interface import UserInterface


class TestUserInterface:
    """Test UserInterface class"""

    def setup_method(self):
        """Setup test"""
        # パッチコンテキストを設定して、各テストでPromptSessionをモックする
        self.mock_prompt_session_patcher = patch(
            "msx_serial.io.input_session.PromptSession"
        )
        self.mock_prompt_session = self.mock_prompt_session_patcher.start()

        # PromptSessionのモックを設定
        mock_session = Mock()
        mock_session.prompt.return_value = "mocked input"
        self.mock_prompt_session.return_value = mock_session

        self.mock_connection = Mock()
        self.ui = UserInterface("#00ff00 bold", "utf-8", self.mock_connection)

    def teardown_method(self):
        """Teardown test"""
        self.mock_prompt_session_patcher.stop()

    def test_init(self):
        """Test initialization"""
        assert self.ui.current_mode == "unknown"
        assert self.ui.prompt_detected is False
        assert self.ui.display is not None
        assert self.ui.input_session is not None
        assert self.ui.command_handler is not None
        assert self.ui.data_sender is not None

    def test_update_mode(self):
        """Test mode update"""
        self.ui.update_mode("basic")
        assert self.ui.current_mode == "basic"

    def test_prompt_detected_attribute(self):
        """Test prompt detected attribute"""
        self.ui.prompt_detected = True
        assert self.ui.prompt_detected is True

    def test_print_receive_regular(self):
        """Test printing regular received text"""
        with patch.object(self.ui.display, "print_receive") as mock_print:
            self.ui.print_receive("test message")
            mock_print.assert_called_once_with("test message", False)

    def test_print_receive_prompt(self):
        """Test printing prompt text"""
        with patch.object(self.ui.display, "print_receive") as mock_print:
            self.ui.print_receive("A>", is_prompt=True)
            mock_print.assert_called_once_with("A>", True)

    def test_prompt(self):
        """Test getting user input"""
        with patch.object(self.ui.input_session, "prompt", return_value="user input"):
            result = self.ui.prompt()
            assert result == "user input"

    def test_handle_special_commands_command(self):
        """Test handling special commands that are commands"""
        mock_file_transfer = Mock()
        stop_event = threading.Event()

        with patch.object(
            self.ui.command_handler, "handle_special_commands", return_value=True
        ):
            result = self.ui.handle_special_commands(
                "@exit", mock_file_transfer, stop_event
            )
            assert result is True

    def test_handle_special_commands_not_command(self):
        """Test handling special commands that are not commands"""
        mock_file_transfer = Mock()
        stop_event = threading.Event()

        with patch.object(
            self.ui.command_handler, "handle_special_commands", return_value=False
        ):
            result = self.ui.handle_special_commands(
                "normal text", mock_file_transfer, stop_event
            )
            assert result is False

    def test_send(self):
        """Test sending data"""
        with patch.object(self.ui.data_sender, "send") as mock_send:
            self.ui.send("test data")
            mock_send.assert_called_once_with("test data")

    def test_clear_screen(self):
        """Test clearing screen"""
        with patch.object(self.ui.display, "clear_screen") as mock_clear:
            self.ui.clear_screen()
            mock_clear.assert_called_once()
