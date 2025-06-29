"""
Command handler for special terminal commands
"""

import os
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from prompt_toolkit.shortcuts import radiolist_dialog
from prompt_toolkit.styles import Style

from ..common.color_output import print_exception, print_info, print_warn
from ..common.config_manager import get_config, set_setting
from .command_types import CommandType
from .performance_commands import handle_performance_command

if TYPE_CHECKING:
    from ..transfer.file_transfer import FileTransferManager


class CommandHandler:
    """Handle special terminal commands"""

    def __init__(self, style: Style, current_mode: str = "unknown"):
        self.style = style
        self.current_mode = current_mode

    def is_command_available(self, command: CommandType) -> bool:
        """Check if command is available in current mode

        Args:
            command: Command type

        Returns:
            True if command is available
        """
        basic_only_commands = {CommandType.UPLOAD, CommandType.PASTE}
        all_mode_commands = {CommandType.MODE}

        if command in basic_only_commands:
            return self.current_mode == "basic"

        if command in all_mode_commands:
            return True

        return True

    def get_available_commands(self) -> list[str]:
        """Get list of available commands for current mode

        Returns:
            List of available commands
        """
        return [cmd.command for cmd in CommandType if self.is_command_available(cmd)]

    def handle_special_commands(
        self,
        user_input: str,
        file_transfer: "FileTransferManager",
        stop_event: threading.Event,
        terminal: object = None,
    ) -> bool:
        """Process special commands

        Args:
            user_input: User input
            file_transfer: File transfer manager
            stop_event: Stop event
            terminal: Terminal instance for performance commands

        Returns:
            True if special command was processed
        """
        # Handle performance commands first
        if user_input.startswith("@perf"):
            if terminal:
                return handle_performance_command(terminal, user_input)
            else:
                print_warn("Performance commands require terminal instance")
                return True

        cmd = CommandType.from_input(user_input)
        if cmd is None:
            return False

        if not self.is_command_available(cmd):
            mode_name = "BASIC" if self.current_mode == "basic" else "MSX-DOS"
            print_warn(f"Command '{cmd.command}' is not available in {mode_name} mode.")
            return True

        if cmd == CommandType.EXIT:
            print_info("Exiting...")
            stop_event.set()
            return True
        elif cmd == CommandType.PASTE:
            file = self._select_file()
            if file:
                file_transfer.paste_file(file)
            return True
        elif cmd == CommandType.UPLOAD:
            file = self._select_file()
            if file:
                file_transfer.upload_file(file)
            return True
        elif cmd == CommandType.CD:
            self._handle_cd(user_input)
            return True
        elif cmd == CommandType.HELP:
            self._handle_help(user_input)
            return True
        elif cmd == CommandType.ENCODE:
            self._handle_encode(user_input)
            return True
        elif cmd == CommandType.MODE:
            self._handle_mode(user_input, terminal)
            return True
        elif cmd == CommandType.CONFIG:
            self._handle_config(user_input)
            return True
        elif cmd == CommandType.PERF:
            self._handle_perf(user_input)
            return True

        return False

    def _select_file(self) -> Optional[str]:
        """Show file selection dialog

        Returns:
            Selected file path
        """
        current_dir = Path.cwd()
        files = [(str(f), f.name) for f in current_dir.glob("*") if f.is_file()]

        if not files:
            print_warn("No files found.")
            return None

        return radiolist_dialog(
            title="Select file to send",
            text="Use arrow keys to navigate, space to select, Enter to confirm",
            values=files,
            style=self.style,
        ).run()

    def _handle_cd(self, user_input: str) -> None:
        """Handle directory change command"""
        try:
            path = user_input[len(CommandType.CD.command) :].strip()
            if not path:
                print_info(f"Current directory: {Path.cwd()}")
                return

            target_path = Path(path).expanduser().resolve()
            if target_path.exists() and target_path.is_dir():
                os.chdir(target_path)
                print_info(f"Changed directory to: {target_path}")
            else:
                print_warn(f"Directory not found: {target_path}")
        except Exception as e:
            print_exception("Failed to change directory", e)

    def _handle_help(self, user_input: str) -> None:
        """Handle help command"""
        args = user_input[len(CommandType.HELP.command) :].strip().split()

        if not args:
            self._show_general_help()
        else:
            command = args[0].lower()
            self._show_command_help(command)

    def _show_general_help(self) -> None:
        """Show general help"""
        help_text = """
Available commands:
  @exit     - Exit the terminal
  @cd [dir] - Change directory
  @help     - Show this help
  @encode   - Change encoding
  @mode     - Switch MSX mode
  @perf     - Performance control (see @perf help)
  
MSX-specific commands (BASIC mode only):
  @paste    - Paste a file as BASIC program
  @upload   - Upload a file to MSX

Use @help <command> for detailed help on specific commands.
        """
        print_info(help_text.strip())

    def _show_command_help(self, command: str) -> None:
        """Show help for specific command"""
        # 内蔵コマンドのヘルプ
        help_texts = {
            "exit": "Exit the program. Usage: @exit",
            "cd": "Change current directory. Usage: @cd [directory]",
            "help": "Show help information. Usage: @help [command]",
            "encode": "Change text encoding. Usage: @encode [encoding]",
            "mode": "Switch MSX mode. Usage: @mode [basic|dos]",
            "paste": "Paste file as BASIC program (BASIC mode only)",
            "upload": "Upload file to MSX (BASIC mode only)",
            "perf": "Performance control commands. Usage: @perf help for details",
        }

        if command in help_texts:
            print_info(f"{command}: {help_texts[command]}")
            return

        # MSX BASICコマンドのヘルプファイルを検索
        if self._show_msx_command_help(command):
            return

        # ヘルプが見つからない場合
        print_warn(f"No help available for '{command}'")

    def _show_msx_command_help(self, command: str) -> bool:
        """Show MSX BASIC command help from man pages

        Args:
            command: Command name to search

        Returns:
            True if help was found and displayed
        """
        try:
            # man ディレクトリのパスを取得
            current_dir = Path(__file__).parent.parent
            man_dir = current_dir / "man"

            if not man_dir.exists():
                return False

            # コマンド名を大文字に変換してmanファイルを検索
            command_upper = command.upper()
            man_file = man_dir / f"{command_upper}.3"

            if man_file.exists():
                self._display_man_page(man_file, command_upper)
                return True

            # アンダースコアで始まる場合はCALLコマンド系として検索
            if command.startswith("_"):
                call_command = command[1:].upper()
                call_man_file = man_dir / f"CALL {call_command}.3"
                if call_man_file.exists():
                    self._display_man_page(call_man_file, f"CALL {call_command}")
                    return True

            return False

        except Exception as e:
            print_exception("Error reading help file", e)
            return False

    def _display_man_page(self, man_file: Path, command_name: str) -> None:
        """Display man page content

        Args:
            man_file: Path to man file
            command_name: Command name for display
        """
        try:
            content = man_file.read_text(encoding="utf-8")

            # 簡単なman形式の解析
            lines = content.split("\n")
            in_examples = False

            print_info(f"=== {command_name} ===")

            for line in lines:
                line = line.strip()

                # セクションの判定
                if line.startswith(".SH NAME"):
                    continue
                elif line.startswith(".SH SYNOPSIS"):
                    print_info("\n【使用法】")
                    continue
                elif line.startswith(".SH DESCRIPTION"):
                    print_info("\n【説明】")
                    continue
                elif line.startswith(".SH EXAMPLES"):
                    print_info("\n【例】")
                    in_examples = True
                    continue
                elif line.startswith(".SH NOTES"):
                    print_info("\n【注意】")
                    in_examples = False  # 例セクション終了
                    continue
                elif line.startswith("."):
                    # その他の制御文字は無視
                    continue

                # 内容の表示
                if line:
                    if in_examples:
                        print_info(f"  {line}")
                    else:
                        print_info(line)

        except Exception as e:
            print_exception(f"Error displaying help for {command_name}", e)

    def _handle_encode(self, user_input: str) -> None:
        """Handle encoding change command"""
        encoding_arg = user_input[len(CommandType.ENCODE.command) :].strip()

        if not encoding_arg:
            print_info("Available encodings: utf-8, msx-jp, shift_jis, cp932")
            return

        # This would need to be implemented in the main terminal class
        print_info(f"Encoding change to '{encoding_arg}' requested")

    def _handle_mode(self, user_input: str, terminal: object = None) -> None:
        """Handle mode switching command"""
        mode_arg = user_input[len(CommandType.MODE.command) :].strip()

        if not mode_arg:
            # Try to detect mode from last prompt
            detected_mode = self.current_mode
            if terminal and hasattr(terminal, "data_processor"):
                last_prompt = (
                    terminal.data_processor.get_last_prompt_for_mode_detection()
                )
                if last_prompt:
                    detected_mode_enum = getattr(
                        terminal, "protocol_detector"
                    ).detect_mode(last_prompt)
                    detected_mode = detected_mode_enum.value
                    print_info(f"Last prompt analyzed: '{last_prompt.strip()}'")
                    print_info(
                        f"Detected mode: {self._get_mode_display_name(detected_mode)}"
                    )
                else:
                    print_info(
                        f"Current mode: {self._get_mode_display_name(self.current_mode)}"
                    )
                    print_info("(No recent prompt to analyze)")
            else:
                print_info(
                    f"Current mode: {self._get_mode_display_name(self.current_mode)}"
                )

            print_info("Available modes: basic, dos")
            return

        new_mode = self._parse_mode_argument(mode_arg)
        if new_mode:
            print_info(
                f"Mode change to '{self._get_mode_display_name(new_mode)}' requested"
            )
            # 手動でモードを変更する場合
            if terminal and hasattr(terminal, "set_mode"):
                terminal.set_mode(new_mode)  # type: ignore
        else:
            print_warn(f"Invalid mode: {mode_arg}")

    def _get_mode_display_name(self, mode: str) -> str:
        """Get display name for mode"""
        return {"basic": "MSX BASIC", "dos": "MSX-DOS"}.get(mode, mode.upper())

    def _parse_mode_argument(self, mode_arg: str) -> Optional[str]:
        """Parse mode argument"""
        mode_mapping = {
            "basic": "basic",
            "b": "basic",
            "dos": "dos",
            "d": "dos",
            "msx-dos": "dos",
        }
        return mode_mapping.get(mode_arg.lower())

    def _handle_config(self, user_input: str) -> None:
        """Handle configuration command"""
        config_args = user_input[len(CommandType.CONFIG.command) :].strip().split()

        if not config_args:
            self._show_config_help()
            return

        subcommand = config_args[0].lower()

        if subcommand == "list":
            self._show_config_list()
        elif subcommand == "get":
            if len(config_args) >= 2:
                self._show_config_value(config_args[1])
            else:
                print_warn("Usage: @config get <key>")
        elif subcommand == "set":
            if len(config_args) >= 3:
                key = config_args[1]
                value = " ".join(config_args[2:])
                self._set_config_value(key, value)
            else:
                print_warn("Usage: @config set <key> <value>")
        elif subcommand == "reset":
            if len(config_args) >= 2:
                self._reset_config_value(config_args[1])
            else:
                print_warn("Usage: @config reset <key>")
        elif subcommand == "help":
            self._show_config_help()
        else:
            print_warn(f"Unknown config subcommand: {subcommand}")
            self._show_config_help()

    def _show_config_help(self) -> None:
        """Show configuration help"""
        help_text = """
Configuration Commands:
  @config list                - Show all configuration settings
  @config get <key>          - Show specific setting value
  @config set <key> <value>  - Set configuration value
  @config reset <key>        - Reset setting to default
  @config help               - Show this help

Examples:
  @config get display.theme
  @config set performance.receive_delay 0.0002
  @config reset encoding.default
        """
        print_info(help_text.strip())

    def _show_config_list(self) -> None:
        """Show all configuration settings"""
        # 設定項目をカテゴリ別に分類
        categories: dict[str, dict[str, Any]] = {}
        config_info = get_config().get_schema_info()

        for key, info in config_info.items():
            category = key.split(".")[0]
            if category not in categories:
                categories[category] = {}
            categories[category][key] = info

        # カテゴリ別に表示
        for category, settings in sorted(categories.items()):
            print_info(f"\n[{category.upper()}]")
            for key, info in sorted(settings.items()):
                current = info["current_value"]
                default = info["default"]
                desc = info["description"]
                print_info(f"  {key}: {current} (default: {default})")
                print_info(f"    {desc}")

    def _show_config_value(self, key: str) -> None:
        """Show specific configuration value"""
        config_manager = get_config()
        schema_info = config_manager.get_schema_info()

        if key not in schema_info:
            print_warn(f"Configuration key '{key}' not found")
            return

        info = schema_info[key]
        current = info["current_value"]
        default = info["default"]
        desc = info["description"]
        choices = info.get("choices")

        print_info(f"Key: {key}")
        print_info(f"Description: {desc}")
        print_info(f"Current Value: {current}")
        print_info(f"Default Value: {default}")
        print_info(f"Type: {info['type']}")

        if choices:
            print_info(f"Valid Choices: {', '.join(map(str, choices))}")

        if info.get("min_value") is not None:
            print_info(f"Min Value: {info['min_value']}")
        if info.get("max_value") is not None:
            print_info(f"Max Value: {info['max_value']}")

    def _set_config_value(self, key: str, value_str: str) -> None:
        """Set configuration value"""
        config_manager = get_config()
        schema_info = config_manager.get_schema_info()

        if key not in schema_info:
            print_warn(f"Configuration key '{key}' not found")
            return

        info = schema_info[key]
        value_type = info["type"]

        # 型変換
        try:
            converted_value: Any
            if value_type == "bool":
                converted_value = value_str.lower() in (
                    "true",
                    "1",
                    "yes",
                    "on",
                    "enable",
                )
            elif value_type == "int":
                converted_value = int(value_str)
            elif value_type == "float":
                converted_value = float(value_str)
            else:
                converted_value = value_str
        except ValueError:
            print_warn(f"Invalid value type for {key}. Expected {value_type}")
            return

        # 設定を更新
        if set_setting(key, converted_value):
            print_info(f"Configuration updated: {key} = {converted_value}")
            print_info("Note: Some changes may require restart to take effect")
        else:
            print_warn(f"Failed to set {key} = {converted_value}")

    def _reset_config_value(self, key: str) -> None:
        """Reset configuration value to default"""
        config_manager = get_config()
        schema_info = config_manager.get_schema_info()

        if key not in schema_info:
            print_warn(f"Configuration key '{key}' not found")
            return

        default_value = schema_info[key]["default"]

        if set_setting(key, default_value):
            print_info(f"Configuration reset: {key} = {default_value}")
        else:
            print_warn(f"Failed to reset {key}")

    def _handle_perf(self, user_input: str) -> None:
        """Handle performance command"""
        # This method should be implemented to handle performance commands
        print_warn("Performance command handling not implemented")
