"""
Tests for input session module
"""

from unittest.mock import Mock, patch
from msx_serial.io.input_session import InputSession
from msx_serial.completion.completers.command_completer import CommandCompleter


class TestInputSession:
    """Test InputSession class"""

    def setup_method(self):
        """Setup test"""
        self.session = InputSession()

    def test_init_default(self):
        """Test initialization with defaults"""
        assert self.session.current_mode == "unknown"
        assert self.session.prompt_detected is False
        assert self.session.session is not None
        assert isinstance(self.session.completer, CommandCompleter)

    def test_init_custom(self):
        """Test initialization with custom parameters"""
        session = InputSession("#ff0000 bold", "basic")
        assert session.current_mode == "basic"

    def test_update_mode(self):
        """Test mode update"""
        self.session.update_mode("basic")
        assert self.session.current_mode == "basic"

    def test_prompt_detected_attribute(self):
        """Test prompt detected attribute"""
        self.session.prompt_detected = True
        assert self.session.prompt_detected is True

        self.session.prompt_detected = False
        assert self.session.prompt_detected is False

    def test_prompt_normal(self):
        """Test getting user input via prompt"""
        with patch.object(self.session.session, "prompt", return_value="user input"):
            result = self.session.prompt()
            assert result == "user input"

    def test_prompt_with_prompt_detected(self):
        """Test prompt when prompt was detected"""
        self.session.prompt_detected = True

        with patch.object(self.session.session, "prompt", return_value="input"):
            result = self.session.prompt()
            assert result == "input"
            # prompt_detected should be reset to False
            assert self.session.prompt_detected is False

    def test_update_mode_with_completer(self):
        """Test mode update with existing completer"""
        mock_completer = Mock()
        mock_completer.set_mode = Mock()

        self.session.completer = mock_completer
        self.session.update_mode("basic")

        assert self.session.current_mode == "basic"
        mock_completer.set_mode.assert_called_once_with("basic")

    def test_prompt_completer_setup(self):
        """Test completer setup in prompt method"""
        mock_completer = Mock()
        mock_completer.set_mode = Mock()

        self.session.completer = mock_completer
        self.session.current_mode = "basic"

        with patch.object(self.session.session, "prompt", return_value="test"):
            self.session.prompt()
            mock_completer.set_mode.assert_called_once_with("basic")
