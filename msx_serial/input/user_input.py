"""
MSXシリアルターミナルのユーザー入力処理
"""

import os
import sys
import threading
import subprocess
import tempfile
import re
from pathlib import Path
from typing import Optional, Any, TYPE_CHECKING
from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.styles import Style
from prompt_toolkit.shortcuts import radiolist_dialog
from prompt_toolkit.formatted_text import FormattedText

from .commands import CommandType
from ..ui.color_output import print_info, print_warn, print_exception
from ..connection.base import Connection
from ..completion.completers.command_completer import CommandCompleter


if TYPE_CHECKING:
    from ..transfer.file_transfer import FileTransferManager

from ..modes import MSXMode


class UserInputHandler:
    """ユーザー入力処理を管理するクラス"""

    def __init__(
        self,
        prompt_style: str,
        encoding: str,
        connection: Connection,
    ):
        """初期化

        Args:
            prompt_style: プロンプトのスタイル
            encoding: エンコーディング
            connection: 接続設定
        """
        self.prompt_style = prompt_style
        self.encoding = encoding
        self.connection = connection
        # MSXプロンプトパターン（A>, B>, C>などに対応）
        self.prompt_pattern = re.compile(r"[A-Z]>\s*$")
        self.prompt_detected = False  # プロンプト検出フラグ
        self.current_mode = "unknown"  # 現在のMSXモード（文字列）
        self.terminal = None  # MSXTerminalへの参照

        self.session: PromptSession = PromptSession()
        self.style = Style.from_dict({"prompt": prompt_style})
        self.completer = CommandCompleter(
            special_commands=[str(cmd.value) for cmd in CommandType],
            current_mode=self.current_mode,
        )
        self.session = PromptSession(
            completer=self.completer,
            style=self.style,
            complete_in_thread=True,
            mouse_support=False,
            wrap_lines=True,
            enable_history_search=True,
            multiline=False,
            auto_suggest=None,
        )

    def clear_screen(self) -> None:
        """画面をクリア"""
        os.system("cls" if os.name == "nt" else "clear")

    def print_receive(self, text: str, is_prompt: bool = False) -> None:
        """受信データをprompt toolkitのprint_formatted_textで表示

        Args:
            text: 表示するテキスト
            is_prompt: プロンプト行かどうか
        """
        # ターミナルサイズを考慮して表示
        try:
            # ターミナルサイズを取得
            terminal_size = os.get_terminal_size()
            terminal_width = terminal_size.columns

            # テキストを適切に折り返し
            if len(text) > terminal_width:
                # 長い行は適切に折り返す
                lines = []
                for i in range(0, len(text), terminal_width):
                    lines.append(text[i : i + terminal_width])
                text_to_display = "\n".join(lines)
            else:
                text_to_display = text

        except OSError:
            # ターミナルサイズが取得できない場合はそのまま表示
            text_to_display = text

        if is_prompt:
            # プロンプトの場合は改行を追加してカーソル位置を次の行に移動
            print_formatted_text(
                FormattedText(
                    [
                        ("#00ff00 bold", text_to_display),
                    ]
                )
            )
        else:
            print_formatted_text(
                FormattedText(
                    [
                        ("#00ff00", text_to_display),
                    ]
                )
            )

    def _is_command_available(self, command: CommandType) -> bool:
        """コマンドが現在のモードで利用可能かチェック

        Args:
            command: コマンドタイプ

        Returns:
            利用可能な場合はTrue
        """
        # BASICモードでのみ有効なコマンド
        basic_only_commands = {CommandType.UPLOAD, CommandType.PASTE}

        # 全モードで有効なコマンド
        all_mode_commands = {CommandType.MODE}

        if command in basic_only_commands:
            return self.current_mode == "basic"

        if command in all_mode_commands:
            return True

        # その他のコマンドは常に有効
        return True

    def _get_available_commands(self) -> list[str]:
        """現在のモードで利用可能なコマンドのリストを取得

        Returns:
            利用可能なコマンドのリスト
        """
        available_commands = []
        for cmd in CommandType:
            if self._is_command_available(cmd):
                available_commands.append(str(cmd.value))
        return available_commands

    def prompt(self) -> Any:
        """プロンプトを表示してユーザー入力を取得

        Returns:
            ユーザー入力
        """
        # 補完機能のモードを更新（新しいコンプリータは作成しない）
        if hasattr(self, "completer") and self.completer:
            self.completer.set_mode(self.current_mode)
        else:
            # 初回のみ新しいコンプリータを作成
            available_commands = self._get_available_commands()
            self.completer = CommandCompleter(available_commands, self.current_mode)
            self.session.completer = self.completer

        # プロンプト検出フラグをリセット
        if self.prompt_detected:
            self.prompt_detected = False

        return self.session.prompt("")

    def send(self, user_input: str) -> None:
        """ユーザー入力を送信

        Args:
            user_input: ユーザー入力
        """
        lines = user_input.splitlines()
        for line in lines:
            if line.strip() == "^C":
                self.connection.write(b"\x03")
            elif line.strip() == "^[":
                self.connection.write(b"\x1b")
            else:
                self.connection.write((line + "\r\n").encode(self.encoding))
        if len(lines) == 0:
            self.connection.write(("\r\n").encode(self.encoding))
        self.connection.flush()

    def handle_special_commands(
        self,
        user_input: str,
        file_transfer: "FileTransferManager",
        stop_event: threading.Event,
    ) -> bool:
        """特殊コマンドを処理

        Args:
            user_input: ユーザー入力
            file_transfer: ファイル転送マネージャー
            stop_event: 停止イベント

        Returns:
            特殊コマンドが処理されたかどうか
        """
        cmd = CommandType.from_input(user_input)
        if cmd is None:
            return False

        # コマンドが現在のモードで利用可能かチェック
        if not self._is_command_available(cmd):
            mode_name = "BASIC" if self.current_mode == "basic" else "MSX-DOS"
            print_warn(
                f"コマンド '{cmd.value}' は{mode_name}モードでは利用できません。"
            )
            return True

        if cmd == CommandType.EXIT:
            print_info("終了します。")
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
            self._handle_mode(user_input)
            return True
        return False

    def _select_file(self) -> Optional[str]:
        """ファイル選択ダイアログを表示

        Returns:
            選択されたファイルのパス
        """
        current_dir = Path.cwd()
        files = [(str(f), f.name) for f in current_dir.glob("*") if f.is_file()]

        if not files:
            print_warn("ファイルが見つかりません。")
            return None

        return radiolist_dialog(
            title="送信するファイルを選択",
            text="矢印キーで移動、スペースで選択、Enterで決定",
            values=files,
            style=self.style,
        ).run()

    def _handle_cd(self, user_input: str) -> None:
        """ディレクトリ変更コマンドを処理

        Args:
            user_input: ユーザー入力
        """
        try:
            path = user_input[len(CommandType.CD.value) :].strip()
            if not path:
                print_info(f"現在のディレクトリ: {Path.cwd()}")
                return
            new_path = Path(path).resolve()
            if new_path.exists() and new_path.is_dir():
                os.chdir(new_path)
                print_info(f"ディレクトリを変更しました: {new_path}")
            else:
                print_warn(f"ディレクトリが存在しません: {path}")
        except Exception as e:
            print_exception("ディレクトリ変更エラー", e)

    def _handle_help(self, user_input: str) -> None:
        """ヘルプコマンドを処理

        Args:
            user_input: ユーザー入力
        """
        command = user_input[len(CommandType.HELP.value) :].strip()

        # 引数がない場合は利用可能なコマンド一覧を表示
        if not command:
            print_info("利用可能なコマンド:")
            for cmd in CommandType:
                if self._is_command_available(cmd):
                    print_info(f"  {cmd.value} - {cmd.description}")
            return

        # _で始まる場合はCALLコマンドとして扱う
        if command.startswith("_"):
            command = f"CALL {command[1:]}"

        # パッケージのインストールディレクトリを取得
        package_dir = Path(__file__).parent.parent
        man_dir = package_dir / "man"
        # manページのパスを生成
        files = [file for file in man_dir.glob(f"**/{command}.*")]
        if len(files) == 0:
            print_warn(f"コマンド '{command}' のマニュアルページが見つかりません。")
            return
        man_path = files[0]

        try:
            # nroffファイルを読み込む
            with open(man_path, "r", encoding="utf-8") as f:
                content = f.read()

            # nroffファイルの内容を処理
            lines = []
            in_ascii_art = False
            current_section = None
            skip_header = True  # ヘッダー部分をスキップするフラグ

            for line in content.split("\n"):
                # ヘッダー部分をスキップ
                if skip_header:
                    if line.startswith(".SH NAME"):
                        skip_header = False
                    continue

                # セクションの開始を検出
                if line.startswith(".SH "):
                    if in_ascii_art:
                        lines.append("")  # ASCIIアートの後に空行を追加
                        in_ascii_art = False
                    current_section = line[4:].strip()
                    lines.append(f"\n{current_section}")
                    lines.append("=" * len(current_section))
                    continue

                # 段落の開始を検出
                if line.startswith(".PP"):
                    if not in_ascii_art:
                        lines.append("")
                    continue

                # 太字の開始を検出
                if line.startswith(".B "):
                    lines.append(line[3:])
                    continue

                # ASCIIアートの開始を検出
                if any(c in line for c in "＊｜＋－"):
                    if not in_ascii_art:
                        lines.append("")  # ASCIIアートの前に空行を追加
                        in_ascii_art = True
                    lines.append(line)
                    continue

                # 通常のテキスト
                if not in_ascii_art:
                    lines.append(line)

            # 結果をページャーで表示
            content = "\n".join(lines)
            try:
                # 一時ファイルに内容を書き込む
                with tempfile.NamedTemporaryFile(
                    mode="w", encoding="utf-8", suffix=".txt", delete=False
                ) as f:
                    f.write(content)
                    temp_path = f.name

                # プラットフォームに応じてページャーを選択
                if sys.platform == "win32":
                    # Windowsの場合、moreコマンドを使用
                    subprocess.run(["notepad", temp_path])
                else:
                    # Unix系の場合、lessコマンドを使用
                    subprocess.run(["less", temp_path])

            finally:
                # 一時ファイルを削除
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

        except Exception as e:
            print_exception("マニュアル表示エラー", e)

    def _handle_encode(self, user_input: str) -> None:
        """エンコーディング切り替えコマンドを処理

        Args:
            user_input: ユーザー入力
        """
        encoding = user_input[len(CommandType.ENCODE.value) :].strip()
        if not encoding:
            print_info(f"現在のエンコーディング: {self.encoding}")
            print_info("利用可能なエンコーディング:")
            print_info("  msx-jp   - MSX日本語")
            print_info("  msx-intl - MSX国際")
            print_info("  msx-br   - MSXブラジル")
            print_info("  shift-jis - Shift-JIS")
            return

        if encoding not in ["msx-jp", "msx-intl", "msx-br", "shift-jis"]:
            print_warn(f"不明なエンコーディング: {encoding}")
            return

        self.encoding = encoding
        print_info(f"エンコーディングを {encoding} に変更しました。")

    def _handle_mode(self, user_input: str) -> None:
        """モードコマンドを処理

        Args:
            user_input: ユーザー入力
        """
        mode_arg = user_input[len(CommandType.MODE.value) :].strip()

        if not mode_arg:
            # 引数がない場合は現在のモードを表示
            mode_name = self._get_mode_display_name(self.current_mode)
            print_info(f"現在のMSXモード: {mode_name}")
            return

        # 引数がある場合はモードを強制変更
        new_mode = self._parse_mode_argument(mode_arg)
        if new_mode is not None:
            self.current_mode = new_mode
            mode_name = self._get_mode_display_name(new_mode)
            print_info(f"MSXモードを {mode_name} に強制変更しました。")
            # 補完機能を更新
            self._update_completer_mode()
            if self.terminal:
                # 文字列からMSXModeに変換
                if new_mode == "basic":
                    self.terminal.set_mode(MSXMode.BASIC)
                elif new_mode == "dos":
                    self.terminal.set_mode(MSXMode.DOS)
                else:
                    self.terminal.set_mode(MSXMode.UNKNOWN)
        else:
            print_warn(f"不明なモード: {mode_arg}")
            print_info("利用可能なモード: basic, dos, unknown")

    def _get_mode_display_name(self, mode: str) -> str:
        """モードの表示名を取得

        Args:
            mode: モード

        Returns:
            表示名
        """
        # 文字列ベースのモード管理
        if mode == "basic":
            return "BASIC"
        elif mode == "dos":
            return "MSX-DOS"
        elif mode == "unknown":
            return "不明"
        else:
            return "不明"

    def _parse_mode_argument(self, mode_arg: str) -> Optional[str]:
        """モード引数を解析

        Args:
            mode_arg: モード引数

        Returns:
            解析されたモード、不明な場合はNone
        """
        mode_arg_lower = mode_arg.lower()
        if mode_arg_lower in ["basic", "b"]:
            return "basic"
        elif mode_arg_lower in ["dos", "d", "msx-dos"]:
            return "dos"
        elif mode_arg_lower in ["unknown", "u", "unk"]:
            return "unknown"
        else:
            return None

    def _update_completer_mode(self) -> None:
        """補完機能に現在のモードを通知"""
        if hasattr(self, "completer") and self.completer:
            self.completer.set_mode(self.current_mode)
            # セッションのコンプリータを確実に設定
            if hasattr(self, "session"):
                self.session.completer = self.completer
