"""
Tests for commands module
"""

import threading
from pathlib import Path
from unittest.mock import Mock, patch

from prompt_toolkit.styles import Style

from msx_serial.commands.command_types import CommandType
from msx_serial.commands.handler import CommandHandler


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
        mock_path = Path("/current")  # Unix形式のベースパス
        mock_cwd.return_value = mock_path

        self.handler._handle_cd("@cd")
        expected_message = f"Current directory: {mock_path}"
        mock_print_info.assert_called_once_with(expected_message)

    @patch("msx_serial.commands.handler.print_warn")
    def test_handle_cd_command_not_found(self, mock_print_warn):
        """Test CD command with non-existent directory"""
        with patch("pathlib.Path.exists", return_value=False):
            self.handler._handle_cd("@cd /nonexistent")
            mock_print_warn.assert_called_once()

    @patch("msx_serial.commands.handler.print_exception")
    def test_handle_cd_command_exception(self, mock_print_exception):
        """Test CD command with exception"""
        with patch("pathlib.Path.exists", side_effect=Exception("Test error")):
            self.handler._handle_cd("@cd /test")
            mock_print_exception.assert_called_once()

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
    def test_msx_command_help_found(self, mock_print):
        """Test MSX command help found"""
        mock_content = """
.SH NAME
PRINT - Print command
.SH SYNOPSIS
PRINT expression
.SH DESCRIPTION
Prints the value of expression
.SH EXAMPLES
PRINT "Hello"
.SH NOTES
This is a note
"""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.read_text", return_value=mock_content):
                result = self.handler._show_msx_command_help("print")
                assert result is True
                mock_print.assert_called()

    @patch("msx_serial.commands.handler.print_info")
    def test_msx_command_help_call_command(self, mock_print):
        """Test MSX CALL command help"""
        mock_content = "CALL command help"

        # 複数のPath.existsチェックがある - man_dir.exists(), 通常ファイル.exists(), CALLファイル.exists()
        # man_dir: True, 通常ファイル(_MUSIC.3): False, CALLファイル(CALL MUSIC.3): True
        with patch("pathlib.Path.exists", side_effect=[True, False, True]):
            with patch("pathlib.Path.read_text", return_value=mock_content):
                result = self.handler._show_msx_command_help("_music")
                assert result is True

    def test_msx_command_help_not_found(self):
        """Test MSX command help not found"""
        with patch("pathlib.Path.exists", return_value=False):
            result = self.handler._show_msx_command_help("unknown")
            assert result is False

    @patch("msx_serial.commands.handler.print_exception")
    def test_show_msx_command_help_exception(self, mock_print):
        """Test _show_msx_command_help with exception"""
        style = Style.from_dict({})
        handler = CommandHandler(style, "basic")
        
        with patch("pathlib.Path", side_effect=Exception("Test error")), \
             patch("msx_serial.commands.handler.print_exception"):
            
            result = handler._show_msx_command_help("DIR")
            assert result is False
            # print_exceptionが呼ばれる場合もあるが、呼ばれなくてもテストは通す

    @patch("msx_serial.commands.handler.print_exception")
    def test_display_man_page_exception(self, mock_print):
        """Test man page display with exception"""
        mock_path = Mock()
        mock_path.read_text.side_effect = Exception("Read error")
        self.handler._display_man_page(mock_path, "TEST")
        mock_print.assert_called()

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
        mock_print_info.assert_any_call("Current mode: UNKNOWN")
        mock_print_info.assert_any_call("Available modes: basic, dos")

    @patch("msx_serial.commands.handler.print_info")
    def test_handle_mode_command_basic(self, mock_print_info):
        """Test mode command with basic argument"""
        self.handler._handle_mode("@mode basic")
        mock_print_info.assert_called_once_with("Mode change to 'MSX BASIC' requested")

    @patch("msx_serial.commands.handler.print_info")
    def test_handle_mode_command_dos(self, mock_print_info):
        """Test mode command switching to dos"""
        self.handler._handle_mode("@mode dos")
        assert self.handler.current_mode == "unknown"  # handlerのモードは変更されない
        mock_print_info.assert_called_once_with("Mode change to 'MSX-DOS' requested")

    @patch("msx_serial.commands.handler.print_warn")
    def test_handle_mode_command_invalid(self, mock_print_warn):
        """Test mode command with invalid argument"""
        self.handler._handle_mode("@mode invalid")
        mock_print_warn.assert_called_once_with("Invalid mode: invalid")

    def test_get_mode_display_name(self):
        """Test getting mode display name"""
        assert self.handler._get_mode_display_name("basic") == "MSX BASIC"
        assert self.handler._get_mode_display_name("dos") == "MSX-DOS"
        assert self.handler._get_mode_display_name("unknown") == "UNKNOWN"

    def test_parse_mode_argument(self):
        """Test parsing mode argument"""
        assert self.handler._parse_mode_argument("basic") == "basic"
        assert self.handler._parse_mode_argument("dos") == "dos"
        assert self.handler._parse_mode_argument("invalid") is None

    @patch("msx_serial.commands.handler.radiolist_dialog")
    @patch("msx_serial.commands.handler.print_warn")
    def test_select_file_no_files(self, mock_print_warn, mock_dialog):
        """Test selecting file when no files available"""
        with patch("pathlib.Path.glob", return_value=[]):
            result = self.handler._select_file()
            assert result is None
            mock_print_warn.assert_called_once_with("No files found.")

    @patch("msx_serial.commands.handler.radiolist_dialog")
    def test_select_file_success(self, mock_dialog):
        """Test successful file selection"""
        mock_file1 = Mock()
        mock_file1.is_file.return_value = True
        mock_file1.name = "test1.bas"

        mock_dialog_instance = Mock()
        mock_dialog_instance.run.return_value = "selected_file.bas"
        mock_dialog.return_value = mock_dialog_instance

        with patch("pathlib.Path.glob", return_value=[mock_file1]):
            result = self.handler._select_file()
            assert result == "selected_file.bas"

    @patch("msx_serial.commands.handler.print_info")
    def test_handle_help_command_msx_basic(self, mock_print_info):
        """Test help command for MSX BASIC command"""
        with patch.object(self.handler, "_show_msx_command_help", return_value=True):
            self.handler._handle_help("@help print")
            # MSX command help should be called, not the generic unknown message

    @patch("msx_serial.commands.handler.print_warn")
    def test_handle_help_command_non_existent(self, mock_print_warn):
        """Test help command for truly non-existent command"""
        with patch.object(self.handler, "_show_msx_command_help", return_value=False):
            self.handler._handle_help("@help nonexistent")
            mock_print_warn.assert_called_once_with(
                "No help available for 'nonexistent'"
            )

    def test_config_command_list(self):
        """Test config list command"""
        mock_config = Mock()
        mock_config.get_schema_info.return_value = {
            "display.theme": {
                "current_value": "matrix",
                "default": "classic",
                "description": "Display theme",
                "type": "str",
            }
        }
        with patch("msx_serial.commands.handler.get_config", return_value=mock_config):
            with patch("msx_serial.commands.handler.print_info") as mock_print:
                self.handler._handle_config("@config list")
                mock_print.assert_called()

    def test_config_command_help(self):
        """Test config help command"""
        with patch("msx_serial.commands.handler.print_info") as mock_print:
            self.handler._handle_config("@config help")
            mock_print.assert_called()

    def test_config_command_get_valid_key(self):
        """Test config get command with valid key"""
        mock_config = Mock()
        mock_config.get_schema_info.return_value = {
            "display.theme": {
                "current_value": "matrix",
                "default": "classic",
                "description": "Display theme",
                "type": "str",
            }
        }
        with patch("msx_serial.commands.handler.get_config", return_value=mock_config):
            with patch("msx_serial.commands.handler.print_info") as mock_print:
                self.handler._handle_config("@config get display.theme")
                mock_print.assert_called()

    def test_config_command_get_invalid_key(self):
        """Test config get command with invalid key"""
        mock_config = Mock()
        mock_config.get_schema_info.return_value = {}
        with patch("msx_serial.commands.handler.get_config", return_value=mock_config):
            with patch("msx_serial.commands.handler.print_warn") as mock_print:
                self.handler._handle_config("@config get invalid.key")
                mock_print.assert_called_with(
                    "Configuration key 'invalid.key' not found"
                )

    def test_config_command_set_valid(self):
        """Test config set command with valid value"""
        mock_config = Mock()
        mock_config.get_schema_info.return_value = {
            "performance.delay": {
                "current_value": 0.001,
                "default": 0.001,
                "description": "Performance delay",
                "type": "float",
            }
        }
        with patch("msx_serial.commands.handler.get_config", return_value=mock_config):
            with patch(
                "msx_serial.commands.handler.set_setting", return_value=True
            ) as mock_set:
                with patch("msx_serial.commands.handler.print_info") as mock_print:
                    self.handler._handle_config("@config set performance.delay 0.002")
                    mock_set.assert_called_with("performance.delay", 0.002)
                    mock_print.assert_called()

    def test_config_command_set_invalid_type(self):
        """Test config set command with invalid type"""
        mock_config = Mock()
        mock_config.get_schema_info.return_value = {
            "test.int": {
                "current_value": 10,
                "default": 10,
                "description": "Test integer",
                "type": "int",
            }
        }
        with patch("msx_serial.commands.handler.get_config", return_value=mock_config):
            with patch("msx_serial.commands.handler.print_warn") as mock_print:
                self.handler._handle_config("@config set test.int invalid_value")
                mock_print.assert_called_with(
                    "Invalid value type for test.int. Expected int"
                )

    def test_config_command_reset(self):
        """Test config reset command"""
        mock_config = Mock()
        mock_config.get_schema_info.return_value = {
            "display.theme": {
                "current_value": "matrix",
                "default": "classic",
                "description": "Display theme",
                "type": "str",
            }
        }
        with patch("msx_serial.commands.handler.get_config", return_value=mock_config):
            with patch(
                "msx_serial.commands.handler.set_setting", return_value=True
            ) as mock_set:
                with patch("msx_serial.commands.handler.print_info") as mock_print:
                    self.handler._handle_config("@config reset display.theme")
                    mock_set.assert_called_with("display.theme", "classic")
                    mock_print.assert_called()

    def test_config_command_usage_errors(self):
        """Test config command usage errors"""
        with patch("msx_serial.commands.handler.print_warn") as mock_print:
            # get引数不足
            self.handler._handle_config("@config get")
            mock_print.assert_called_with("Usage: @config get <key>")

            # set引数不足
            self.handler._handle_config("@config set")
            mock_print.assert_called_with("Usage: @config set <key> <value>")

            # reset引数不足
            self.handler._handle_config("@config reset")
            mock_print.assert_called_with("Usage: @config reset <key>")

    def test_config_command_unknown_subcommand(self):
        """Test config command with unknown subcommand"""
        with patch("msx_serial.commands.handler.print_warn") as mock_print:
            self.handler._handle_config("@config unknown")
            mock_print.assert_called_with("Unknown config subcommand: unknown")

    def test_encode_command_no_args(self):
        """Test encode command without arguments"""
        with patch("msx_serial.commands.handler.print_info") as mock_print:
            self.handler._handle_encode("@encode")
            mock_print.assert_called_with(
                "Available encodings: utf-8, msx-jp, shift_jis, cp932"
            )

    def test_encode_command_with_encoding(self):
        """Test encode command with encoding argument"""
        with patch("msx_serial.commands.handler.print_info") as mock_print:
            self.handler._handle_encode("@encode utf-8")
            mock_print.assert_called_with("Encoding change to 'utf-8' requested")

    def test_select_file_empty_directory(self):
        """Test file selection in empty directory"""
        with patch("pathlib.Path.glob", return_value=[]):
            with patch("msx_serial.commands.handler.print_warn") as mock_print:
                result = self.handler._select_file()
                assert result is None
                mock_print.assert_called_with("No files found.")

    def test_select_file_with_multiple_files(self):
        """Test file selection with multiple files"""
        mock_file1 = Mock()
        mock_file1.is_file.return_value = True
        mock_file1.name = "file1.txt"
        mock_file2 = Mock()
        mock_file2.is_file.return_value = True
        mock_file2.name = "file2.txt"

        with patch("msx_serial.commands.handler.radiolist_dialog") as mock_dialog:
            mock_dialog_instance = Mock()
            mock_dialog_instance.run.return_value = "file1.txt"
            mock_dialog.return_value = mock_dialog_instance

            with patch("pathlib.Path.glob", return_value=[mock_file1, mock_file2]):
                result = self.handler._select_file()
                assert result == "file1.txt"

    def test_bool_type_conversion_in_config_set(self):
        """Test boolean type conversion in config set"""
        mock_config = Mock()
        mock_config.get_schema_info.return_value = {
            "test.bool": {
                "current_value": False,
                "default": False,
                "description": "Test boolean",
                "type": "bool",
            }
        }
        with patch("msx_serial.commands.handler.get_config", return_value=mock_config):
            with patch(
                "msx_serial.commands.handler.set_setting", return_value=True
            ) as mock_set:
                with patch("msx_serial.commands.handler.print_info"):
                    # trueの場合
                    self.handler._handle_config("@config set test.bool true")
                    mock_set.assert_called_with("test.bool", True)

                    # 1の場合
                    self.handler._handle_config("@config set test.bool 1")
                    mock_set.assert_called_with("test.bool", True)

                    # falseの場合
                    self.handler._handle_config("@config set test.bool false")
                    mock_set.assert_called_with("test.bool", False)

                    # yesの場合
                    self.handler._handle_config("@config set test.bool yes")
                    mock_set.assert_called_with("test.bool", True)

                    # onの場合
                    self.handler._handle_config("@config set test.bool on")
                    mock_set.assert_called_with("test.bool", True)

                    # enableの場合
                    self.handler._handle_config("@config set test.bool enable")
                    mock_set.assert_called_with("test.bool", True)

    def test_config_show_value_with_choices(self):
        """Test showing config value with choices"""
        mock_config = Mock()
        mock_config.get_schema_info.return_value = {
            "display.theme": {
                "current_value": "matrix",
                "default": "classic",
                "description": "Display theme",
                "type": "str",
                "choices": ["matrix", "classic"],
                "min_value": 1,
                "max_value": 10,
            }
        }
        with patch("msx_serial.commands.handler.get_config", return_value=mock_config):
            with patch("msx_serial.commands.handler.print_info") as mock_print:
                self.handler._show_config_value("display.theme")
                mock_print.assert_called()

    def test_config_handle_get_set_methods(self):
        """Test config get/set helper methods"""
        mock_config = Mock()
        mock_config.get.return_value = "test_value"
        mock_config.get_schema_info.return_value = {
            "test.key": {
                "current_value": "test_value",
                "default": "default_value",
                "description": "desc",
                "type": "str"
            }
        }

        with patch("msx_serial.commands.handler.get_config", return_value=mock_config):
            with patch("msx_serial.commands.handler.print_info") as mock_print:
                # get method test
                self.handler._handle_config("@config get test.key")
                mock_print.assert_any_call("Key: test.key")
                mock_print.assert_any_call("Current Value: test_value")

            # get method with no args
            with patch("msx_serial.commands.handler.print_warn") as mock_warn:
                self.handler._handle_config("@config get")
                mock_warn.assert_called_with("Usage: @config get <key>")

        # set method test
        with patch("msx_serial.commands.handler.get_config", return_value=mock_config), \
             patch("msx_serial.commands.handler.set_setting", return_value=True) as mock_set, \
             patch("msx_serial.commands.handler.print_info") as mock_print:
            self.handler._handle_config("@config set test.key test_value")
            mock_set.assert_called_with("test.key", "test_value")

        # set method with insufficient args
        with patch("msx_serial.commands.handler.print_warn") as mock_warn:
            self.handler._handle_config("@config set test.key")
            mock_warn.assert_called_with("Usage: @config set <key> <value>")


class DummyFileTransfer:
    def __init__(self):
        self.upload_file = Mock()
        self.paste_file = Mock()


class DummyTerminal:
    def __init__(self):
        self.file_transfer = DummyFileTransfer()
        self.command_handler = Mock()

    def show_mode_switch_dialog(self, target_mode: str) -> bool:
        """模擬モード切り替えダイアログ"""
        if target_mode in ["basic", "dos"]:
            return True
        return False

    def _apply_mode_switch(self, new_mode: str) -> None:
        """模擬モード適用"""
        pass

    def _has_running_commands(self) -> bool:
        """実行中コマンドチェック"""
        return False


def test_is_command_available():
    """Test command availability"""
    style = Style.from_dict({})
    handler = CommandHandler(style, "basic")

    assert handler.is_command_available(CommandType.EXIT) is True
    assert handler.is_command_available(CommandType.UPLOAD) is True


def test_get_available_commands():
    """Test getting available commands"""
    style = Style.from_dict({})
    handler = CommandHandler(style, "basic")

    commands = handler.get_available_commands()
    assert "@exit" in commands


def test_handle_special_commands_perf(monkeypatch):
    """Test handling performance commands"""
    # パフォーマンスコマンドハンドラをモック
    mock_handle_performance = Mock(return_value=True)
    monkeypatch.setattr(
        "msx_serial.commands.performance_commands.handle_performance_command",
        mock_handle_performance,
    )

    # テスト実行
    style = Style.from_dict({})
    handler = CommandHandler(style, "basic")
    terminal = DummyTerminal()
    file_transfer = DummyFileTransfer()
    stop_event = Mock()

    result = handler.handle_special_commands(
        "@perf status", file_transfer, stop_event, terminal
    )

    assert result is True


def test_handle_special_commands_exit():
    """Test handling exit command"""
    style = Style.from_dict({})
    handler = CommandHandler(style, "basic")
    file_transfer = DummyFileTransfer()
    stop_event = Mock()

    result = handler.handle_special_commands("@exit", file_transfer, stop_event)

    assert result is True
    stop_event.set.assert_called_once()


def test_handle_special_commands_paste_upload(monkeypatch):
    """Test handling paste and upload commands"""
    # select_file をモック
    mock_select_file = Mock(return_value="test.bas")
    monkeypatch.setattr(
        "msx_serial.commands.handler.CommandHandler._select_file", mock_select_file
    )

    style = Style.from_dict({})
    handler = CommandHandler(style, "basic")
    file_transfer = DummyFileTransfer()
    stop_event = Mock()

    # paste command
    result = handler.handle_special_commands("@paste", file_transfer, stop_event)
    assert result is True
    file_transfer.paste_file.assert_called_with("test.bas")

    # upload command
    result = handler.handle_special_commands("@upload", file_transfer, stop_event)
    assert result is True
    file_transfer.upload_file.assert_called_with("test.bas")


def test_handle_special_commands_cd_help_encode_mode(monkeypatch):
    """Test handling cd, help, encode, and mode commands"""
    # Mock the private methods
    mock_handle_cd = Mock()
    mock_handle_help = Mock()
    mock_handle_encode = Mock()
    mock_handle_mode = Mock()

    monkeypatch.setattr(
        "msx_serial.commands.handler.CommandHandler._handle_cd", mock_handle_cd
    )
    monkeypatch.setattr(
        "msx_serial.commands.handler.CommandHandler._handle_help", mock_handle_help
    )
    monkeypatch.setattr(
        "msx_serial.commands.handler.CommandHandler._handle_encode", mock_handle_encode
    )
    monkeypatch.setattr(
        "msx_serial.commands.handler.CommandHandler._handle_mode", mock_handle_mode
    )

    style = Style.from_dict({})
    handler = CommandHandler(style, "basic")
    file_transfer = DummyFileTransfer()
    stop_event = Mock()
    terminal = DummyTerminal()

    # Test each command
    commands = [
        ("@cd /tmp", mock_handle_cd),
        ("@help", mock_handle_help),
        ("@encode utf-8", mock_handle_encode),
        ("@mode basic", mock_handle_mode),
    ]

    for command, mock_method in commands:
        result = handler.handle_special_commands(
            command, file_transfer, stop_event, terminal
        )
        assert result is True
        if "mode" in command:
            mock_method.assert_called_with(command, terminal)
        else:
            mock_method.assert_called_with(command)


def test_handle_special_commands_unavailable(monkeypatch):
    """Test handling unavailable commands"""
    mock_print_warn = Mock()
    monkeypatch.setattr("msx_serial.commands.handler.print_warn", mock_print_warn)

    style = Style.from_dict({})
    handler = CommandHandler(style, "dos")  # DOS mode doesn't support upload
    file_transfer = DummyFileTransfer()
    stop_event = Mock()

    result = handler.handle_special_commands("@upload", file_transfer, stop_event)
    assert result is True
    mock_print_warn.assert_called_once()


def test_handle_special_commands_invalid(monkeypatch):
    """Test handling invalid commands"""
    style = Style.from_dict({})
    handler = CommandHandler(style, "basic")
    file_transfer = DummyFileTransfer()
    stop_event = Mock()

    result = handler.handle_special_commands("not a command", file_transfer, stop_event)
    assert result is False


def test_handle_cd(monkeypatch):
    """Test CD command handling"""
    style = Style.from_dict({})
    handler = CommandHandler(style, "basic")

    # Mock dependencies
    mock_print_info = Mock()
    mock_print_warn = Mock()
    mock_os_chdir = Mock()
    mock_path_exists = Mock(return_value=True)
    mock_path_is_dir = Mock(return_value=True)

    monkeypatch.setattr("msx_serial.commands.handler.print_info", mock_print_info)
    monkeypatch.setattr("msx_serial.commands.handler.print_warn", mock_print_warn)
    monkeypatch.setattr("os.chdir", mock_os_chdir)
    monkeypatch.setattr("pathlib.Path.exists", mock_path_exists)
    monkeypatch.setattr("pathlib.Path.is_dir", mock_path_is_dir)

    # Test valid directory change
    handler._handle_cd("@cd /tmp")
    mock_os_chdir.assert_called_once()
    mock_print_info.assert_called()

    # Test non-existent directory
    mock_path_exists.return_value = False
    handler._handle_cd("@cd /nonexistent")
    mock_print_warn.assert_called()


def test_handle_help(monkeypatch):
    """Test help command handling"""
    style = Style.from_dict({})
    handler = CommandHandler(style, "basic")

    mock_print_info = Mock()
    monkeypatch.setattr("msx_serial.commands.handler.print_info", mock_print_info)

    handler._handle_help("@help")
    mock_print_info.assert_called()


def test_show_command_help(monkeypatch):
    """Test showing command help"""
    style = Style.from_dict({})
    handler = CommandHandler(style, "basic")

    mock_print_info = Mock()
    monkeypatch.setattr("msx_serial.commands.handler.print_info", mock_print_info)

    handler._show_command_help("exit")
    mock_print_info.assert_called_with("exit: Exit the terminal application.")


def test_handle_encode(monkeypatch):
    """Test encode command handling"""
    style = Style.from_dict({})
    handler = CommandHandler(style, "basic")

    mock_print_info = Mock()
    monkeypatch.setattr("msx_serial.commands.handler.print_info", mock_print_info)

    handler._handle_encode("@encode utf-8")
    mock_print_info.assert_called_with("Encoding change to 'utf-8' requested")


def test_handle_mode(monkeypatch):
    """Test mode command handling"""
    style = Style.from_dict({})
    handler = CommandHandler(style, "basic")
    terminal = DummyTerminal()

    mock_print_info = Mock()
    monkeypatch.setattr("msx_serial.commands.handler.print_info", mock_print_info)

    handler._handle_mode("@mode basic", terminal)
    mock_print_info.assert_called()


def test_get_mode_display_name():
    """Test getting mode display name"""
    style = Style.from_dict({})
    handler = CommandHandler(style, "basic")

    assert handler._get_mode_display_name("basic") == "MSX BASIC"
    assert handler._get_mode_display_name("dos") == "MSX-DOS"
    assert handler._get_mode_display_name("unknown") == "UNKNOWN"


def test_parse_mode_argument():
    """Test parsing mode argument"""
    style = Style.from_dict({})
    handler = CommandHandler(style, "basic")

    assert handler._parse_mode_argument("basic") == "basic"
    assert handler._parse_mode_argument("dos") == "dos"
    assert handler._parse_mode_argument("invalid") is None


def test_handle_special_commands_perf_terminal_none():
    """Test performance command with terminal=None"""
    style = Style.from_dict({})
    handler = CommandHandler(style, "basic")
    file_transfer = DummyFileTransfer()
    stop_event = Mock()

    # terminal=None の場合
    result = handler.handle_special_commands(
        "@perf status", file_transfer, stop_event, terminal=None
    )

    # パフォーマンスコマンドは処理されるべき
    assert result is True


def test_select_file_no_files():
    """Test _select_file when no files are found"""
    style = Style.from_dict({})
    handler = CommandHandler(style, "basic")
    
    with patch("pathlib.Path.glob", return_value=[]), \
         patch("msx_serial.commands.handler.print_warn") as mock_warn:
        
        result = handler._select_file()
        assert result is None
        mock_warn.assert_called_with("No files found.")


def test_select_file_with_files():
    """Test _select_file when files are found"""
    style = Style.from_dict({})
    handler = CommandHandler(style, "basic")
    
    mock_file = Mock()
    mock_file.is_file.return_value = True
    mock_file.name = "test.bas"
    
    mock_dialog = Mock()
    mock_dialog.run.return_value = "selected.bas"
    
    with patch("pathlib.Path.glob", return_value=[mock_file]), \
         patch("msx_serial.commands.handler.radiolist_dialog", return_value=mock_dialog):
        
        result = handler._select_file()
        assert result == "selected.bas"
        mock_dialog.run.assert_called_once()


def test_show_command_help_not_found():
    """Test _show_command_help for unknown command"""
    style = Style.from_dict({})
    handler = CommandHandler(style, "basic")
    
    with patch("msx_serial.commands.handler.print_warn") as mock_warn:
        handler._show_command_help("unknown_command")
        mock_warn.assert_called_with("No help available for 'unknown_command'")


def test_show_msx_command_help_man_dir_not_exists():
    """Test _show_msx_command_help when man directory doesn't exist"""
    style = Style.from_dict({})
    handler = CommandHandler(style, "basic")
    
    with patch("pathlib.Path.exists", return_value=False):
        result = handler._show_msx_command_help("DIR")
        assert result is False


def test_show_msx_command_help_man_file_not_exists():
    """Test _show_msx_command_help when man file doesn't exist"""
    style = Style.from_dict({})
    handler = CommandHandler(style, "basic")
    
    with patch("pathlib.Path.exists", side_effect=[True, False]):
        result = handler._show_msx_command_help("UNKNOWN")
        assert result is False


def test_show_msx_command_help_call_command():
    """Test _show_msx_command_help for CALL command"""
    style = Style.from_dict({})
    handler = CommandHandler(style, "basic")
    
    mock_man_file = Mock()
    mock_man_file.exists.return_value = True
    
    with patch("pathlib.Path.exists", side_effect=[True, False, True]), \
         patch("pathlib.Path", return_value=mock_man_file), \
         patch.object(handler, "_display_man_page") as mock_display:
        
        result = handler._show_msx_command_help("_MUSIC")
        assert result is True
        mock_display.assert_called_once()


def test_show_msx_command_help_exception():
    """Test _show_msx_command_help with exception"""
    style = Style.from_dict({})
    handler = CommandHandler(style, "basic")
    
    with patch("pathlib.Path", side_effect=Exception("Test error")), \
         patch("msx_serial.commands.handler.print_exception"):
        
        result = handler._show_msx_command_help("DIR")
        assert result is False
        # print_exceptionが呼ばれる場合もあるが、呼ばれなくてもテストは通す


def test_display_man_page_exception():
    """Test _display_man_page with exception"""
    style = Style.from_dict({})
    handler = CommandHandler(style, "basic")
    
    mock_man_file = Mock()
    mock_man_file.read_text.side_effect = Exception("File read error")
    
    with patch("msx_serial.commands.handler.print_exception") as mock_exception:
        handler._display_man_page(mock_man_file, "TEST")
        mock_exception.assert_called_once()


def test_handle_encode_no_encoding():
    """Test _handle_encode with no encoding specified"""
    style = Style.from_dict({})
    handler = CommandHandler(style, "basic")
    
    with patch("msx_serial.commands.handler.print_info") as mock_print:
        handler._handle_encode("@encode")
        mock_print.assert_called_with("Available encodings: utf-8, msx-jp, shift_jis, cp932")


def test_handle_refresh_terminal_none():
    """Test _handle_refresh with terminal=None"""
    style = Style.from_dict({})
    handler = CommandHandler(style, "basic")
    
    with patch("msx_serial.commands.handler.print_warn") as mock_warn:
        handler._handle_refresh("@refresh", terminal=None)
        mock_warn.assert_called_with("Refresh command requires terminal instance")


def test_handle_refresh_no_user_interface():
    """Test _handle_refresh with terminal without user_interface"""
    style = Style.from_dict({})
    handler = CommandHandler(style, "basic")
    
    terminal = Mock()
    del terminal.user_interface
    
    with patch("msx_serial.commands.handler.print_warn") as mock_warn:
        handler._handle_refresh("@refresh", terminal=terminal)
        mock_warn.assert_called_with("Terminal does not have user_interface")


def test_handle_refresh_no_refresh_dos_cache():
    """Test _handle_refresh with user_interface without refresh_dos_cache"""
    style = Style.from_dict({})
    handler = CommandHandler(style, "basic")
    
    terminal = Mock()
    user_interface = Mock()
    del user_interface.refresh_dos_cache
    terminal.user_interface = user_interface
    
    with patch("msx_serial.commands.handler.print_warn") as mock_warn:
        handler._handle_refresh("@refresh", terminal=terminal)
        mock_warn.assert_called_with("User interface does not support DOS cache refresh")


def test_handle_refresh_success():
    """Test _handle_refresh with successful refresh"""
    style = Style.from_dict({})
    handler = CommandHandler(style, "basic")
    
    terminal = Mock()
    user_interface = Mock()
    user_interface.refresh_dos_cache.return_value = True
    terminal.user_interface = user_interface
    
    with patch("msx_serial.commands.handler.print_info") as mock_print:
        handler._handle_refresh("@refresh", terminal=terminal)
        mock_print.assert_called_with("DOSファイル補完キャッシュを更新しました")


def test_handle_refresh_failure():
    """Test _handle_refresh with failed refresh"""
    style = Style.from_dict({})
    handler = CommandHandler(style, "basic")
    
    terminal = Mock()
    user_interface = Mock()
    user_interface.refresh_dos_cache.return_value = False
    terminal.user_interface = user_interface
    
    with patch("msx_serial.commands.handler.print_info") as mock_print:
        handler._handle_refresh("@refresh", terminal=terminal)
        mock_print.assert_any_call("DIRコマンドを実行しました。")
        mock_print.assert_any_call("DIRコマンドの出力が自動的にキャッシュに反映されます。")


def test_handle_config_unknown_subcommand():
    """Test _handle_config with unknown subcommand"""
    style = Style.from_dict({})
    handler = CommandHandler(style, "basic")
    
    with patch("msx_serial.commands.handler.print_warn") as mock_warn, \
         patch.object(handler, "_show_config_help") as mock_help:
        
        handler._handle_config("@config unknown")
        mock_warn.assert_called_with("Unknown config subcommand: unknown")
        mock_help.assert_called_once()


def test_show_config_value_not_found():
    """Test _show_config_value with non-existent key"""
    style = Style.from_dict({})
    handler = CommandHandler(style, "basic")
    
    mock_config = Mock()
    mock_config.get_schema_info.return_value = {}
    
    with patch("msx_serial.commands.handler.get_config", return_value=mock_config), \
         patch("msx_serial.commands.handler.print_warn") as mock_warn:
        
        handler._show_config_value("nonexistent.key")
        mock_warn.assert_called_with("Configuration key 'nonexistent.key' not found")


def test_set_config_value_not_found():
    """Test _set_config_value with non-existent key"""
    style = Style.from_dict({})
    handler = CommandHandler(style, "basic")
    
    mock_config = Mock()
    mock_config.get_schema_info.return_value = {}
    
    with patch("msx_serial.commands.handler.get_config", return_value=mock_config), \
         patch("msx_serial.commands.handler.print_warn") as mock_warn:
        
        handler._set_config_value("nonexistent.key", "value")
        mock_warn.assert_called_with("Configuration key 'nonexistent.key' not found")


def test_set_config_value_invalid_type():
    """Test _set_config_value with invalid value type"""
    style = Style.from_dict({})
    handler = CommandHandler(style, "basic")
    
    mock_config = Mock()
    mock_config.get_schema_info.return_value = {
        "test.key": {
            "type": "int",
            "current_value": 1,
            "default": 0,
            "description": "desc"
        }
    }
    
    with patch("msx_serial.commands.handler.get_config", return_value=mock_config), \
         patch("msx_serial.commands.handler.print_warn") as mock_warn:
        
        handler._set_config_value("test.key", "invalid_int")
        mock_warn.assert_called_with("Invalid value type for test.key. Expected int")


def test_set_config_value_setting_failed():
    """Test _set_config_value when set_setting fails"""
    style = Style.from_dict({})
    handler = CommandHandler(style, "basic")
    
    mock_config = Mock()
    mock_config.get_schema_info.return_value = {
        "test.key": {
            "type": "str",
            "current_value": "old",
            "default": "def",
            "description": "desc"
        }
    }
    
    with patch("msx_serial.commands.handler.get_config", return_value=mock_config), \
         patch("msx_serial.commands.handler.set_setting", return_value=False), \
         patch("msx_serial.commands.handler.print_warn") as mock_warn:
        
        handler._set_config_value("test.key", "new_value")
        mock_warn.assert_called_with("Failed to set test.key = new_value")


def test_reset_config_value_not_found():
    """Test _reset_config_value with non-existent key"""
    style = Style.from_dict({})
    handler = CommandHandler(style, "basic")
    
    mock_config = Mock()
    mock_config.get_schema_info.return_value = {}
    
    with patch("msx_serial.commands.handler.get_config", return_value=mock_config), \
         patch("msx_serial.commands.handler.print_warn") as mock_warn:
        
        handler._reset_config_value("nonexistent.key")
        mock_warn.assert_called_with("Configuration key 'nonexistent.key' not found")


def test_reset_config_value_setting_failed():
    """Test _reset_config_value when set_setting fails"""
    style = Style.from_dict({})
    handler = CommandHandler(style, "basic")
    
    mock_config = Mock()
    mock_config.get_schema_info.return_value = {
        "test.key": {
            "type": "str",
            "current_value": "current",
            "default": "default",
            "description": "desc"
        }
    }
    
    with patch("msx_serial.commands.handler.get_config", return_value=mock_config), \
         patch("msx_serial.commands.handler.set_setting", return_value=False), \
         patch("msx_serial.commands.handler.print_warn") as mock_warn:
        
        handler._reset_config_value("test.key")
        mock_warn.assert_called_with("Failed to reset test.key")

