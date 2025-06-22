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
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from prompt_toolkit.shortcuts import radiolist_dialog

from .commands import CommandType
from ..ui.color_output import print_info, print_warn, print_exception
from ..connection.base import Connection
from ..completion.completers.command_completer import CommandCompleter


if TYPE_CHECKING:
    from ..transfer.file_transfer import FileTransferManager


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
        self.session: PromptSession = PromptSession()
        self.style = Style.from_dict({"prompt": prompt_style})
        self.session = PromptSession(
            completer=CommandCompleter(
                special_commands=[str(cmd.value) for cmd in CommandType]
            ),
            style=self.style,
            complete_in_thread=True,
        )
        # MSXプロンプトパターン（A>, B>, C>などに対応）
        self.prompt_pattern = re.compile(r'[A-Z]>\s*$')

    def prompt(self) -> Any:
        """プロンプトを表示してユーザー入力を取得

        Returns:
            ユーザー入力
        """
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
            path = user_input[len(CommandType.CD.value):].strip()
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
        command = user_input[len(CommandType.HELP.value):].strip()
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
        encoding = user_input[len(CommandType.ENCODE.value):].strip()
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
