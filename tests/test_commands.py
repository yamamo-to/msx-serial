"""
Tests for commands module
"""

import threading
import types
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
        """Test getting mode display names"""
        assert (
            self.handler._get_mode_display_name("basic") == "MSX BASIC"
        )  # スペース区切り
        assert self.handler._get_mode_display_name("dos") == "MSX-DOS"
        assert self.handler._get_mode_display_name("unknown") == "UNKNOWN"  # 大文字
        assert self.handler._get_mode_display_name("invalid") == "INVALID"  # 大文字

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

    @patch("msx_serial.commands.handler.print_info")
    def test_handle_help_command_msx_basic(self, mock_print_info):
        """Test @help with MSX BASIC command"""
        self.handler._handle_help("@help ABS")
        # ヘルプが表示される場合、複数回print_infoが呼ばれる
        assert mock_print_info.called
        # 最初の呼び出しでコマンド名が表示される
        first_call = mock_print_info.call_args_list[0]
        assert "ABS" in str(first_call)

    @patch("msx_serial.commands.handler.print_warn")
    def test_handle_help_command_non_existent(self, mock_print_warn):
        """Test @help with non-existent command"""
        self.handler._handle_help("@help NONEXISTENT")
        mock_print_warn.assert_called_once_with("No help available for 'nonexistent'")

    def test_config_command_list(self):
        """@config listコマンドのテスト"""
        handler = CommandHandler(Style.from_dict({}))

        with patch("msx_serial.commands.handler.print_info") as mock_print:
            handler._handle_config("@config list")
            mock_print.assert_called()

    def test_config_command_help(self):
        """@config helpコマンドのテスト"""
        handler = CommandHandler(Style.from_dict({}))

        with patch("msx_serial.commands.handler.print_info") as mock_print:
            handler._handle_config("@config help")
            mock_print.assert_called()

    def test_config_command_get_valid_key(self):
        """@config get（有効なキー）のテスト"""
        handler = CommandHandler(Style.from_dict({}))

        with patch("msx_serial.commands.handler.get_config") as mock_get_config:
            mock_config = Mock()
            mock_config.get_schema_info.return_value = {
                "display.theme": {
                    "current_value": "dark",
                    "default": "light",
                    "description": "Display theme",
                    "type": "str",
                }
            }
            mock_get_config.return_value = mock_config

            with patch("msx_serial.commands.handler.print_info") as mock_print:
                handler._handle_config("@config get display.theme")
                mock_print.assert_called()

    def test_config_command_get_invalid_key(self):
        """@config get（無効なキー）のテスト"""
        handler = CommandHandler(Style.from_dict({}))

        with patch("msx_serial.commands.handler.get_config") as mock_get_config:
            mock_config = Mock()
            mock_config.get_schema_info.return_value = {}
            mock_get_config.return_value = mock_config

            with patch("msx_serial.commands.handler.print_warn") as mock_print:
                handler._handle_config("@config get invalid.key")
                mock_print.assert_called_with(
                    "Configuration key 'invalid.key' not found"
                )

    def test_config_command_set_valid(self):
        """@config set（有効な値）のテスト"""
        handler = CommandHandler(Style.from_dict({}))

        with (
            patch("msx_serial.commands.handler.get_config") as mock_get_config,
            patch("msx_serial.commands.handler.set_setting") as mock_set_setting,
        ):

            mock_config = Mock()
            mock_config.get_schema_info.return_value = {
                "performance.delay": {
                    "current_value": 0.001,
                    "default": 0.001,
                    "description": "Performance delay",
                    "type": "float",
                }
            }
            mock_get_config.return_value = mock_config
            mock_set_setting.return_value = True

            with patch("msx_serial.commands.handler.print_info") as mock_print:
                handler._handle_config("@config set performance.delay 0.002")
                mock_print.assert_called()
                mock_set_setting.assert_called_once()

    def test_config_command_set_invalid_type(self):
        """@config set（無効な型）のテスト"""
        handler = CommandHandler(Style.from_dict({}))

        with patch("msx_serial.commands.handler.get_config") as mock_get_config:
            mock_config = Mock()
            mock_config.get_schema_info.return_value = {
                "performance.delay": {
                    "current_value": 0.001,
                    "default": 0.001,
                    "description": "Performance delay",
                    "type": "int",
                }
            }
            mock_get_config.return_value = mock_config

            with patch("msx_serial.commands.handler.print_warn") as mock_print:
                handler._handle_config("@config set performance.delay invalid_value")
                mock_print.assert_called()

    def test_config_command_reset(self):
        """@config resetコマンドのテスト"""
        handler = CommandHandler(Style.from_dict({}))

        with (
            patch("msx_serial.commands.handler.get_config") as mock_get_config,
            patch("msx_serial.commands.handler.set_setting") as mock_set_setting,
        ):

            mock_config = Mock()
            mock_config.get_schema_info.return_value = {
                "display.theme": {
                    "current_value": "dark",
                    "default": "light",
                    "description": "Display theme",
                    "type": "str",
                }
            }
            mock_get_config.return_value = mock_config
            mock_set_setting.return_value = True

            with patch("msx_serial.commands.handler.print_info") as mock_print:
                handler._handle_config("@config reset display.theme")
                mock_print.assert_called()

    def test_config_command_usage_errors(self):
        """@configコマンドの使用方法エラーのテスト"""
        handler = CommandHandler(Style.from_dict({}))

        with patch("msx_serial.commands.handler.print_warn") as mock_print:
            # get without key
            handler._handle_config("@config get")
            mock_print.assert_called_with("Usage: @config get <key>")

            # set without value
            handler._handle_config("@config set key")
            mock_print.assert_called_with("Usage: @config set <key> <value>")

            # reset without key
            handler._handle_config("@config reset")
            mock_print.assert_called_with("Usage: @config reset <key>")

    def test_config_command_unknown_subcommand(self):
        """@config 不明なサブコマンドのテスト"""
        handler = CommandHandler(Style.from_dict({}))

        with (
            patch("msx_serial.commands.handler.print_warn") as mock_warn,
            patch.object(handler, "_show_config_help") as mock_help,
        ):
            handler._handle_config("@config unknown")
            mock_warn.assert_called_with("Unknown config subcommand: unknown")
            mock_help.assert_called()

    def test_encode_command_no_args(self):
        """@encodeコマンド（引数なし）のテスト"""
        handler = CommandHandler(Style.from_dict({}))

        with patch("msx_serial.commands.handler.print_info") as mock_print:
            handler._handle_encode("@encode")
            mock_print.assert_called_with(
                "Available encodings: utf-8, msx-jp, shift_jis, cp932"
            )

    def test_encode_command_with_encoding(self):
        """@encodeコマンド（エンコーディング指定）のテスト"""
        handler = CommandHandler(Style.from_dict({}))

        with patch("msx_serial.commands.handler.print_info") as mock_print:
            handler._handle_encode("@encode utf-8")
            mock_print.assert_called_with("Encoding change to 'utf-8' requested")

    def test_select_file_empty_directory(self):
        """ファイル選択（空ディレクトリ）のテスト"""
        handler = CommandHandler(Style.from_dict({}))

        with (
            patch("pathlib.Path.cwd") as mock_cwd,
            patch("msx_serial.commands.handler.print_warn") as mock_print,
        ):

            mock_dir = Mock()
            mock_dir.glob.return_value = []
            mock_cwd.return_value = mock_dir

            result = handler._select_file()
            assert result is None
            mock_print.assert_called_with("No files found.")

    def test_select_file_with_multiple_files(self):
        """ファイル選択（複数ファイルあり）のテスト"""
        handler = CommandHandler(Style.from_dict({}))

        with (
            patch("pathlib.Path.cwd") as mock_cwd,
            patch("msx_serial.commands.handler.radiolist_dialog") as mock_dialog,
        ):

            # ファイルのモック
            mock_file1 = Mock()
            mock_file1.is_file.return_value = True
            mock_file1.name = "test1.txt"

            mock_file2 = Mock()
            mock_file2.is_file.return_value = True
            mock_file2.name = "test2.txt"

            mock_dir = Mock()
            mock_dir.glob.return_value = [mock_file1, mock_file2]
            mock_cwd.return_value = mock_dir

            # ダイアログのモック
            mock_dialog_instance = Mock()
            mock_dialog_instance.run.return_value = "/path/to/test1.txt"
            mock_dialog.return_value = mock_dialog_instance

            result = handler._select_file()
            assert result == "/path/to/test1.txt"
            mock_dialog.assert_called_once()

    def test_bool_type_conversion_in_config_set(self):
        """@config setでのbool型変換のテスト"""
        handler = CommandHandler(Style.from_dict({}))

        with (
            patch("msx_serial.commands.handler.get_config") as mock_get_config,
            patch("msx_serial.commands.handler.set_setting") as mock_set_setting,
        ):

            mock_config = Mock()
            mock_config.get_schema_info.return_value = {
                "test.bool": {
                    "current_value": False,
                    "default": False,
                    "description": "Test boolean",
                    "type": "bool",
                }
            }
            mock_get_config.return_value = mock_config
            mock_set_setting.return_value = True

            with patch("msx_serial.commands.handler.print_info"):
                # true値のテスト
                for true_val in ["true", "1", "yes", "on", "enable"]:
                    handler._handle_config(f"@config set test.bool {true_val}")
                    mock_set_setting.assert_called_with("test.bool", True)

                # false値のテスト
                handler._handle_config("@config set test.bool false")
                mock_set_setting.assert_called_with("test.bool", False)

    def test_config_show_value_with_choices(self):
        """@config get（選択肢あり）のテスト"""
        handler = CommandHandler(Style.from_dict({}))

        with patch("msx_serial.commands.handler.get_config") as mock_get_config:
            mock_config = Mock()
            mock_config.get_schema_info.return_value = {
                "display.theme": {
                    "current_value": "dark",
                    "default": "light",
                    "description": "Display theme",
                    "type": "str",
                    "choices": ["light", "dark", "auto"],
                    "min_value": 1,
                    "max_value": 10,
                }
            }
            mock_get_config.return_value = mock_config

            with patch("msx_serial.commands.handler.print_info") as mock_print:
                handler._show_config_value("display.theme")
                # 複数回呼ばれることを確認
                assert (
                    mock_print.call_count >= 6
                )  # Key, Description, Current, Default, Type, Choices, Min, Max

    def test_config_handle_get_set_methods(self):
        """設定の取得・設定用のヘルパーメソッドのテスト"""
        handler = CommandHandler(Style.from_dict({}))

        # _handle_config_get のテスト
        with (
            patch("msx_serial.commands.handler.get_config") as mock_get_config,
            patch("msx_serial.commands.handler.print_info") as mock_print_info,
            patch("msx_serial.commands.handler.print_warn") as mock_print_warn,
        ):

            mock_config = Mock()
            mock_config.get.return_value = "test_value"
            mock_get_config.return_value = mock_config

            # 正常ケース
            handler._handle_config_get(["test.key"])
            mock_print_info.assert_called_with("test.key: test_value")

            # 引数なし
            handler._handle_config_get([])
            mock_print_warn.assert_called_with("設定キーを指定してください")

            # 設定が見つからない
            mock_config.get.return_value = None
            handler._handle_config_get(["invalid.key"])
            mock_print_warn.assert_called_with(
                "設定キー 'invalid.key' が見つかりません"
            )

        # _handle_config_set のテスト
        with (
            patch("msx_serial.commands.handler.set_setting") as mock_set_setting,
            patch("msx_serial.commands.handler.print_info") as mock_print_info,
            patch("msx_serial.commands.handler.print_warn") as mock_print_warn,
        ):

            mock_set_setting.return_value = True

            # 正常ケース（文字列）
            handler._handle_config_set(["test.key", "test_value"])
            mock_set_setting.assert_called_with("test.key", "test_value")

            # bool値
            handler._handle_config_set(["test.bool", "true"])
            mock_set_setting.assert_called_with("test.bool", True)

            # int値
            handler._handle_config_set(["test.int", "42"])
            mock_set_setting.assert_called_with("test.int", 42)

            # float値
            handler._handle_config_set(["test.float", "3.14"])
            mock_set_setting.assert_called_with("test.float", 3.14)

            # 引数不足
            handler._handle_config_set(["key"])
            mock_print_warn.assert_called_with("設定キーと値を指定してください")

            # 設定失敗
            mock_set_setting.return_value = False
            handler._handle_config_set(["test.key", "value"])
            mock_print_warn.assert_called_with("設定の更新に失敗しました: test.key")


class DummyFileTransfer:
    def __init__(self):
        self.paste_file = Mock()
        self.upload_file = Mock()


class DummyTerminal:
    def __init__(self):
        self.set_mode = Mock()
        self.data_processor = Mock()
        self.protocol_detector = Mock()
        self.protocol_detector.detect_mode = Mock(
            return_value=types.SimpleNamespace(value="dos")
        )
        self.data_processor.get_last_prompt_for_mode_detection = Mock(
            return_value="MSX-DOS Ok\n"
        )


style = Style([("", "")])


def test_is_command_available():
    handler = CommandHandler(style, current_mode="basic")
    assert handler.is_command_available(CommandType.UPLOAD)
    assert handler.is_command_available(CommandType.PASTE)
    handler.current_mode = "dos"
    assert not handler.is_command_available(CommandType.UPLOAD)
    assert not handler.is_command_available(CommandType.PASTE)
    assert handler.is_command_available(CommandType.MODE)


def test_get_available_commands():
    handler = CommandHandler(style, current_mode="basic")
    cmds = handler.get_available_commands()
    assert any("upload" in c for c in cmds)
    handler.current_mode = "dos"
    cmds = handler.get_available_commands()
    assert not any("upload" in c for c in cmds)


def test_handle_special_commands_perf(monkeypatch):
    handler = CommandHandler(style)
    dummy_term = DummyTerminal()
    # perfコマンド: terminalあり
    monkeypatch.setattr(
        "msx_serial.commands.performance_commands.handle_performance_command",
        lambda t, u: True,
    )
    assert handler.handle_special_commands(
        "@perf stats", None, threading.Event(), terminal=dummy_term
    )
    # perfコマンド: terminalなし
    assert handler.handle_special_commands(
        "@perf stats", None, threading.Event(), terminal=None
    )


def test_handle_special_commands_exit():
    handler = CommandHandler(style)
    stop_event = threading.Event()
    res = handler.handle_special_commands("@exit", None, stop_event)
    assert res is True
    assert stop_event.is_set()


def test_handle_special_commands_paste_upload(monkeypatch):
    handler = CommandHandler(style, current_mode="basic")
    file_transfer = DummyFileTransfer()
    # _select_fileがNone
    monkeypatch.setattr(handler, "_select_file", lambda: None)
    assert handler.handle_special_commands("@paste", file_transfer, threading.Event())
    assert handler.handle_special_commands("@upload", file_transfer, threading.Event())
    # _select_fileがファイル名
    monkeypatch.setattr(handler, "_select_file", lambda: "test.txt")
    assert handler.handle_special_commands("@paste", file_transfer, threading.Event())
    file_transfer.paste_file.assert_called_with("test.txt")
    assert handler.handle_special_commands("@upload", file_transfer, threading.Event())
    file_transfer.upload_file.assert_called_with("test.txt")


def test_handle_special_commands_cd_help_encode_mode(monkeypatch):
    handler = CommandHandler(style)
    file_transfer = DummyFileTransfer()
    monkeypatch.setattr(handler, "_select_file", lambda: None)
    # CD
    monkeypatch.setattr(handler, "_handle_cd", lambda u: True)
    assert handler.handle_special_commands("@cd test", file_transfer, threading.Event())
    # HELP
    monkeypatch.setattr(handler, "_handle_help", lambda u: True)
    assert handler.handle_special_commands("@help", file_transfer, threading.Event())
    # ENCODE
    monkeypatch.setattr(handler, "_handle_encode", lambda u: True)
    assert handler.handle_special_commands(
        "@encode utf-8", file_transfer, threading.Event()
    )
    # MODE
    monkeypatch.setattr(handler, "_handle_mode", lambda u, t: True)
    assert handler.handle_special_commands(
        "@mode basic", file_transfer, threading.Event()
    )


def test_handle_special_commands_unavailable(monkeypatch):
    handler = CommandHandler(style, current_mode="dos")
    file_transfer = DummyFileTransfer()
    # UPLOADはdosモードで不可
    monkeypatch.setattr(handler, "_select_file", lambda: "test.txt")
    res = handler.handle_special_commands("@upload", file_transfer, threading.Event())
    assert res is True


def test_handle_special_commands_invalid(monkeypatch):
    handler = CommandHandler(style)
    file_transfer = DummyFileTransfer()
    # 存在しないコマンド
    res = handler.handle_special_commands("@unknown", file_transfer, threading.Event())
    assert res is False


def test_handle_cd(monkeypatch):
    handler = CommandHandler(style)
    # パスなし
    monkeypatch.setattr("msx_serial.commands.handler.print_info", lambda msg: None)
    handler._handle_cd("@cd ")
    # 存在しないパス
    monkeypatch.setattr("msx_serial.commands.handler.print_warn", lambda msg: None)
    monkeypatch.setattr("pathlib.Path.exists", lambda self: False)
    handler._handle_cd("@cd notfound")
    # 存在するディレクトリ
    monkeypatch.setattr("pathlib.Path.exists", lambda self: True)
    monkeypatch.setattr("pathlib.Path.is_dir", lambda self: True)
    monkeypatch.setattr("os.chdir", lambda path: None)
    handler._handle_cd("@cd .")
    # 例外発生
    monkeypatch.setattr(
        "pathlib.Path.exists", lambda self: (_ for _ in ()).throw(Exception("err"))
    )
    monkeypatch.setattr(
        "msx_serial.commands.handler.print_exception", lambda msg, e: None
    )
    handler._handle_cd("@cd error")


def test_handle_help(monkeypatch):
    handler = CommandHandler(style)
    monkeypatch.setattr(handler, "_show_general_help", lambda: None)
    monkeypatch.setattr(handler, "_show_command_help", lambda c: None)
    handler._handle_help("@help")
    handler._handle_help("@help exit")


def test_show_command_help(monkeypatch):
    handler = CommandHandler(style)
    monkeypatch.setattr("msx_serial.commands.handler.print_info", lambda msg: None)
    monkeypatch.setattr("msx_serial.commands.handler.print_warn", lambda msg: None)
    handler._show_command_help("exit")
    handler._show_command_help("unknown")


def test_handle_encode(monkeypatch):
    handler = CommandHandler(style)
    monkeypatch.setattr("msx_serial.commands.handler.print_info", lambda msg: None)
    handler._handle_encode("@encode ")
    handler._handle_encode("@encode utf-8")


def test_handle_mode(monkeypatch):
    handler = CommandHandler(style)
    dummy_term = DummyTerminal()
    monkeypatch.setattr("msx_serial.commands.handler.print_info", lambda msg: None)
    monkeypatch.setattr("msx_serial.commands.handler.print_warn", lambda msg: None)
    # 引数なし: terminalあり
    handler._handle_mode("@mode", terminal=dummy_term)
    # 引数なし: terminalなし
    handler._handle_mode("@mode", terminal=None)
    # 有効なmode
    handler._handle_mode("@mode basic", terminal=dummy_term)
    # 無効なmode
    handler._handle_mode("@mode invalid", terminal=dummy_term)


def test_get_mode_display_name():
    handler = CommandHandler(style)
    assert handler._get_mode_display_name("basic") == "MSX BASIC"
    assert handler._get_mode_display_name("dos") == "MSX-DOS"
    assert handler._get_mode_display_name("other") == "OTHER"


def test_parse_mode_argument():
    handler = CommandHandler(style)
    assert handler._parse_mode_argument("basic") == "basic"
    assert handler._parse_mode_argument("b") == "basic"
    assert handler._parse_mode_argument("dos") == "dos"
    assert handler._parse_mode_argument("d") == "dos"
    assert handler._parse_mode_argument("msx-dos") == "dos"
    assert handler._parse_mode_argument("invalid") is None


def test_handle_special_commands_perf_terminal_none():
    handler = CommandHandler(style)
    with patch("msx_serial.commands.handler.print_warn") as mock_warn:
        result = handler.handle_special_commands(
            "@perf stats", None, threading.Event(), terminal=None
        )
        assert result is True
        mock_warn.assert_called_once_with(
            "Performance commands require terminal instance"
        )


def test_select_file_dialog_runs():
    handler = CommandHandler(style)
    mock_file = Mock()
    mock_file.name = "test.txt"
    mock_file.is_file.return_value = True
    with (
        patch("pathlib.Path.glob", return_value=[mock_file]),
        patch("pathlib.Path.cwd", return_value=Path(".")),
        patch("msx_serial.commands.handler.radiolist_dialog") as mock_dialog,
    ):
        mock_dialog.return_value.run.return_value = "/path/to/test.txt"
        result = handler._select_file()
        assert result == "/path/to/test.txt"
        mock_dialog.return_value.run.assert_called_once()


def test_handle_cd_exception():
    handler = CommandHandler(style)
    with patch("msx_serial.commands.handler.print_exception") as mock_exc:
        # Path.existsが例外を投げる
        with patch("pathlib.Path.exists", side_effect=Exception("fail")):
            handler._handle_cd("@cd error")
            mock_exc.assert_called()
