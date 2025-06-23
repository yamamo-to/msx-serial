"""
Tests for commands module
"""

import threading
from unittest.mock import Mock, patch
from pathlib import Path
from msx_serial.commands.handler import CommandHandler
from msx_serial.input.commands import CommandType
from prompt_toolkit.styles import Style


class TestCommandHandler:
    """Test CommandHandler class"""

    def setup_method(self):
        """Setup test"""
        self.style = Style.from_dict({"prompt": "#00ff00 bold"})
        self.handler = CommandHandler(self.style, "unknown")

    def test_init(self):
        """Test initialization"""
        assert self.handler.style == self.style
        assert self.handler.current_mode == "unknown"

    def test_is_command_available_basic_only(self):
        """Test command availability for BASIC-only commands"""
        self.handler.current_mode = "basic"
        assert self.handler.is_command_available(CommandType.UPLOAD) is True
        assert self.handler.is_command_available(CommandType.PASTE) is True

        self.handler.current_mode = "dos"
        assert self.handler.is_command_available(CommandType.UPLOAD) is False
        assert self.handler.is_command_available(CommandType.PASTE) is False

    def test_is_command_available_all_modes(self):
        """Test command availability for all-mode commands"""
        self.handler.current_mode = "basic"
        assert self.handler.is_command_available(CommandType.MODE) is True

        self.handler.current_mode = "dos"
        assert self.handler.is_command_available(CommandType.MODE) is True

    def test_is_command_available_general(self):
        """Test command availability for general commands"""
        commands = [
            CommandType.EXIT,
            CommandType.CD,
            CommandType.HELP,
            CommandType.ENCODE,
        ]

        for cmd in commands:
            assert self.handler.is_command_available(cmd) is True

    def test_get_available_commands(self):
        """Test getting available commands"""
        self.handler.current_mode = "basic"
        commands = self.handler.get_available_commands()

        assert "@upload" in commands
        assert "@paste" in commands
        assert "@mode" in commands
        assert "@exit" in commands

        self.handler.current_mode = "dos"
        commands = self.handler.get_available_commands()

        assert "@upload" not in commands
        assert "@paste" not in commands
        assert "@mode" in commands
        assert "@exit" in commands

    @patch("msx_serial.commands.handler.print_info")
    def test_handle_exit_command(self, mock_print_info):
        """Test handling EXIT command"""
        mock_file_transfer = Mock()
        stop_event = threading.Event()

        result = self.handler.handle_special_commands(
            "@exit", mock_file_transfer, stop_event
        )

        assert result is True
        assert stop_event.is_set()
        mock_print_info.assert_called_once_with("Exiting...")

    @patch("msx_serial.commands.handler.print_warn")
    def test_handle_unavailable_command(self, mock_print_warn):
        """Test handling unavailable command"""
        self.handler.current_mode = "dos"
        mock_file_transfer = Mock()
        stop_event = threading.Event()

        result = self.handler.handle_special_commands(
            "@upload", mock_file_transfer, stop_event
        )

        assert result is True
        mock_print_warn.assert_called_once()

    def test_handle_non_command(self):
        """Test handling non-command input"""
        mock_file_transfer = Mock()
        stop_event = threading.Event()

        result = self.handler.handle_special_commands(
            "regular text", mock_file_transfer, stop_event
        )

        assert result is False

    @patch("msx_serial.commands.handler.os.chdir")
    @patch("msx_serial.commands.handler.print_info")
    def test_handle_cd_command_success(self, mock_print_info, mock_chdir):
        """Test successful CD command"""
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_dir", return_value=True),
        ):

            self.handler._handle_cd("@cd /tmp")
            mock_chdir.assert_called_once()
            mock_print_info.assert_called()

    @patch("msx_serial.commands.handler.print_info")
    @patch("pathlib.Path.cwd")
    def test_handle_cd_command_no_path(self, mock_cwd, mock_print_info):
        """Test CD command without path"""
        mock_cwd.return_value = Path("/current")

        self.handler._handle_cd("@cd")
        mock_print_info.assert_called_once_with("Current directory: /current")

    @patch("msx_serial.commands.handler.print_warn")
    def test_handle_cd_command_not_found(self, mock_print_warn):
        """Test CD command with non-existent directory"""
        with patch("pathlib.Path.exists", return_value=False):
            self.handler._handle_cd("@cd /nonexistent")
            mock_print_warn.assert_called_once()

    @patch("msx_serial.commands.handler.print_info")
    def test_handle_help_command_general(self, mock_print_info):
        """Test general help command"""
        self.handler._handle_help("@help")
        mock_print_info.assert_called()

    @patch("msx_serial.commands.handler.print_info")
    def test_handle_help_command_specific(self, mock_print_info):
        """Test specific help command"""
        self.handler._handle_help("@help exit")
        mock_print_info.assert_called_once_with("exit: Exit the terminal application.")

    @patch("msx_serial.commands.handler.print_warn")
    def test_handle_help_command_unknown(self, mock_print_warn):
        """Test help for unknown command"""
        self.handler._handle_help("@help unknown")
        mock_print_warn.assert_called_once_with("No help available for 'unknown'")

    @patch("msx_serial.commands.handler.print_info")
    def test_handle_encode_command_no_arg(self, mock_print_info):
        """Test encode command without argument"""
        self.handler._handle_encode("@encode")
        mock_print_info.assert_called_once_with(
            "Available encodings: utf-8, msx-jp, shift_jis, cp932"
        )

    @patch("msx_serial.commands.handler.print_info")
    def test_handle_encode_command_with_arg(self, mock_print_info):
        """Test encode command with argument"""
        self.handler._handle_encode("@encode utf-8")
        mock_print_info.assert_called_once_with("Encoding change to 'utf-8' requested")

    @patch("msx_serial.commands.handler.print_info")
    def test_handle_mode_command_no_arg(self, mock_print_info):
        """Test mode command without argument"""
        self.handler._handle_mode("@mode")
        mock_print_info.assert_any_call("Current mode: Unknown")
        mock_print_info.assert_any_call("Available modes: basic, dos")

    @patch("msx_serial.commands.handler.print_info")
    def test_handle_mode_command_basic(self, mock_print_info):
        """Test mode command switching to basic"""
        self.handler._handle_mode("@mode basic")
        assert self.handler.current_mode == "basic"
        mock_print_info.assert_called_once_with("Mode switched to: MSX-BASIC")

    @patch("msx_serial.commands.handler.print_info")
    def test_handle_mode_command_dos(self, mock_print_info):
        """Test mode command switching to dos"""
        self.handler._handle_mode("@mode dos")
        assert self.handler.current_mode == "dos"
        mock_print_info.assert_called_once_with("Mode switched to: MSX-DOS")

    @patch("msx_serial.commands.handler.print_warn")
    def test_handle_mode_command_invalid(self, mock_print_warn):
        """Test mode command with invalid mode"""
        self.handler._handle_mode("@mode invalid")
        mock_print_warn.assert_called_once_with("Invalid mode: invalid")

    def test_get_mode_display_name(self):
        """Test getting mode display names"""
        assert self.handler._get_mode_display_name("basic") == "MSX-BASIC"
        assert self.handler._get_mode_display_name("dos") == "MSX-DOS"
        assert self.handler._get_mode_display_name("unknown") == "Unknown"
        assert self.handler._get_mode_display_name("invalid") == "invalid"

    def test_parse_mode_argument(self):
        """Test parsing mode arguments"""
        assert self.handler._parse_mode_argument("basic") == "basic"
        assert self.handler._parse_mode_argument("b") == "basic"
        assert self.handler._parse_mode_argument("BASIC") == "basic"

        assert self.handler._parse_mode_argument("dos") == "dos"
        assert self.handler._parse_mode_argument("d") == "dos"
        assert self.handler._parse_mode_argument("msx-dos") == "dos"

        assert self.handler._parse_mode_argument("invalid") is None

    @patch("msx_serial.commands.handler.radiolist_dialog")
    @patch("msx_serial.commands.handler.print_warn")
    def test_select_file_no_files(self, mock_print_warn, mock_dialog):
        """Test file selection when no files exist"""
        with patch("pathlib.Path.glob", return_value=[]):
            result = self.handler._select_file()
            assert result is None
            mock_print_warn.assert_called_once_with("No files found.")

    @patch("msx_serial.commands.handler.radiolist_dialog")
    def test_select_file_success(self, mock_dialog):
        """Test successful file selection"""
        mock_file = Mock()
        mock_file.name = "test.txt"
        mock_file.is_file.return_value = True

        mock_dialog.return_value.run.return_value = "/path/to/test.txt"

        with (
            patch("pathlib.Path.glob", return_value=[mock_file]),
            patch("pathlib.Path.cwd", return_value=Path("/current")),
        ):
            result = self.handler._select_file()
            assert result == "/path/to/test.txt"
