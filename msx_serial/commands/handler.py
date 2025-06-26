"""
Command handler for special terminal commands
"""

import os
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from prompt_toolkit.shortcuts import radiolist_dialog
from prompt_toolkit.styles import Style

from ..common.color_output import print_exception, print_info, print_warn
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
        return [str(cmd.value) for cmd in CommandType if self.is_command_available(cmd)]

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
            print_warn(f"Command '{cmd.value}' is not available in {mode_name} mode.")
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
            path = user_input[len(CommandType.CD.value) :].strip()
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
        args = user_input[len(CommandType.HELP.value) :].strip().split()

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
        help_texts = {
            "exit": "Exit the terminal application.",
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
        else:
            print_warn(f"No help available for '{command}'")

    def _handle_encode(self, user_input: str) -> None:
        """Handle encoding change command"""
        encoding_arg = user_input[len(CommandType.ENCODE.value) :].strip()

        if not encoding_arg:
            print_info("Available encodings: utf-8, msx-jp, shift_jis, cp932")
            return

        # This would need to be implemented in the main terminal class
        print_info(f"Encoding change to '{encoding_arg}' requested")

    def _handle_mode(self, user_input: str, terminal: object = None) -> None:
        """Handle mode switching command"""
        mode_arg = user_input[len(CommandType.MODE.value) :].strip()

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
