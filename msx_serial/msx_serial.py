#!/usr/bin/env python3
"""
MSXシリアルターミナル
MSXとのシリアル通信またはtelnet接続を行うターミナルプログラム
"""

import argparse
import base64
import chardet
import colorama
import os
import threading
import yaml
import sys
import time
import msx_charset

from enum import Enum
from pathlib import Path
from typing import List, Optional, Union
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.shortcuts import radiolist_dialog
from prompt_toolkit.styles import Style
from prompt_toolkit.lexers import PygmentsLexer
from pygments_msxbasic.lexer import MSXBasicLexer
from .completion.msx0 import MSX0Completer

from tqdm import tqdm
from .iot_nodes import IotNodes
from .upload import upload_program
from .connection.serial import SerialConfig, SerialConnection
from .connection.telnet import TelnetConfig, TelnetConnection
from .connection.base import Connection
from .connection.connection import detect_connection_type


from .console import (
    print_info,
    print_warn,
    print_error,
    print_exception,
    print_receive,
    str_info,
)


class CommandType(Enum):
    """コマンドタイプの列挙型"""

    PASTE = "@paste"
    BYTES = "@bytes"
    EXIT = "@exit"
    UPLOAD = "@upload"
    CD = "@cd"


class MSXSerialTerminal:
    """MSXシリアルターミナルのメインクラス"""

    def __init__(
        self,
        config: Union[TelnetConfig, SerialConfig],
        encoding: str,
        prompt_style: str,
    ):
        """初期化"""
        self.config = config
        self.encoding = encoding
        self.prompt_style = prompt_style
        self.connection: Optional[Connection] = None
        self.running: bool = True
        self.suppress_echo: bool = False  # エコー抑制フラグ
        self._setup_ui()
        colorama.init()

    def _setup_ui(self) -> None:
        """UIの初期設定"""
        self.style = Style.from_dict({"prompt": self.prompt_style})

        self.session = PromptSession(
            #lexer=PygmentsLexer(MSXBasicLexer),
            completer=MSX0Completer(
                special_commands=[cmd.value for cmd in CommandType]
            ),
            vi_mode=False,
            style=self.style,
            complete_in_thread=True,
            complete_while_typing=True,
            refresh_interval=0.1,
            enable_history_search=True,
        )

    def _load_commands(self) -> List[str]:
        """コマンドをYAMLファイルから読み込む"""
        yaml_path = Path(__file__).parent / "commands.yml"
        if yaml_path.exists():
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data.get("commands", []) if data else []
        return []

    def _read(self) -> None:
        """シリアル受信処理"""
        while self.running and self.connection:
            try:
                if self.connection.in_waiting() > 0:
                    data = self.connection.read(self.connection.in_waiting())
                    if not self.suppress_echo:  # エコー抑制フラグをチェック
                        decoded_code = bytes(data).decode(self.encoding)
                        print_receive(f"{decoded_code}", end="")
            except Exception as e:
                if self.running:
                    print_exception("接続エラー", e)
                break

    def _paste_file(self, file_path: Union[str, Path]) -> None:
        """テキストファイルの内容を貼り付け"""
        with open(file_path, "rb") as f:
            raw_data = f.read()
            encoding = chardet.detect(raw_data)["encoding"]

            if encoding in ["SHIFT_JIS", "CP932", "EUC-JP"]:
                for line in raw_data.split(b"\n"):
                    if line:
                        self.connection.write(line + b"\r\n")
                        self.connection.flush()
            else:
                with open(file_path, "r", encoding=encoding) as f:
                    for line in f:
                        msx_codes = line.rstrip() + "\r\n"
                        self.connection.write(msx_codes.encode(self.encoding))
                        self.connection.flush()

    def _upload_file(self, file_path: Union[str, Path]) -> None:
        """ファイルをアップロード"""
        try:
            # エコー抑制を開始
            self.suppress_echo = True

            # BASICプログラムを送信
            self.connection.write(upload_program(file_path).encode("ascii"))
            self.connection.flush()

            # RUNコマンドを送信
            self.connection.write("RUN\r\n".encode("ascii"))
            self.connection.flush()
            time.sleep(1)

            # ファイルを送信
            with open(file_path, "rb") as f:
                data = f.read()
                encoded_data = base64.b64encode(data).decode("ascii")

                # プログレスバーの設定
                with tqdm(
                    total=len(encoded_data),
                    unit="B",
                    unit_scale=True,
                    desc=str_info("アップロード中"),
                    bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
                ) as pbar:
                    for i in range(0, len(encoded_data), 76):
                        chunk = encoded_data[i : i + 76]
                        self.connection.write(chunk.encode("ascii") + b"\r\n")
                        self.connection.flush()
                        pbar.update(len(chunk))
                        time.sleep(0.5)

            self.connection.write(b"`\r\n")
            self.connection.flush()
            print_info("アップロード完了")

        except Exception as e:
            print_exception("アップロードエラー", e)
        finally:
            self.suppress_echo = False

    def _select_file(self) -> Optional[str]:
        """ファイル選択ダイアログを表示"""
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

    def _handle_special_commands(self, user_input: str) -> bool:
        """特殊コマンドの処理"""
        if user_input.strip() == CommandType.EXIT.value:
            print_info("終了します。")
            self.running = False
            return True

        if user_input.strip() == CommandType.PASTE.value:
            file_path = self._select_file()
            if file_path:
                print_info(f"[選択] {file_path}")
                self._paste_file(file_path)
            return True

        if user_input.strip() == CommandType.BYTES.value:
            self._handle_bytes_command()
            return True

        if user_input.strip() == CommandType.UPLOAD.value:
            self._handle_upload_command()
            return True

        if user_input.startswith(CommandType.CD.value):
            self._handle_cd_command(user_input)
            return True

        return False

    def _handle_bytes_command(self) -> None:
        """バイトコマンドの処理"""
        hex_input = input(str_info("16進数のバイト列を入力してください: "))
        try:
            bytes_data = bytes.fromhex(hex_input.replace(" ", ""))
            self.connection.write(bytes_data)
            self.connection.flush()
            print_info(f"送信: {hex_input}")
        except ValueError as e:
            print_exception("エラー: 無効な16進数です", e)

    def _handle_upload_command(self) -> None:
        """アップロードコマンドの処理"""
        file_path = self._select_file()
        if file_path:
            print_info(f"[選択] {file_path}")
            self._upload_file(file_path)
        return True

    def _handle_cd_command(self, user_input: str) -> None:
        """ディレクトリ移動コマンドの処理"""
        try:
            # @cd の後のパスを取得
            path = user_input[len(CommandType.CD.value) :].strip()
            if not path:
                print_info(f"現在のディレクトリ: {Path.cwd()}")
                return

            # 新しいパスに移動
            new_path = Path(path).resolve()
            if new_path.exists() and new_path.is_dir():
                os.chdir(str(new_path))
                print_info(f"ディレクトリを変更しました: {new_path}")
            else:
                print_error(f"指定されたディレクトリが存在しません: {path}")
        except Exception as e:
            print_exception(f"ディレクトリの変更に失敗しました: {path}", e)

    def _read_keyboard(self) -> None:
        """キーボード入力監視"""
        while self.running:
            try:
                user_input = self.session.prompt(
                    "",
                    complete_in_thread=True,
                    complete_while_typing=True,
                    refresh_interval=0.1,
                    enable_history_search=True,
                )

                if self._handle_special_commands(user_input):
                    continue

                if user_input.strip() == "":
                    self.connection.write(b"\r\n")
                else:
                    self._send_user_input(user_input)

            except KeyboardInterrupt:
                print_info("\nCtrl+C で終了します。")
                self.running = False
                break
            except Exception as e:
                print_exception("キーボードエラー", e)
                self.running = False
                break

    def _send_user_input(self, user_input: str) -> None:
        """ユーザー入力を送信"""
        for line in user_input.splitlines():
            if line.strip() == "^C":
                self.connection.write(b"\x03")  # Ctrl-C
            elif line.strip() == "^[":
                self.connection.write(b"\x1b")  # ESC
            else:
                msx_code = line + "\r\n"
                self.connection.write(msx_code.encode(self.encoding))
        self.connection.flush()

    def run(self) -> None:
        """ターミナルを実行"""
        try:
            if isinstance(self.config, SerialConfig):
                self.connection = SerialConnection(self.config)
            elif isinstance(self.config, TelnetConfig):
                self.connection = TelnetConnection(self.config)
            else:
                raise ValueError(f"不明な接続タイプ: {self.config}")

            connection_thread = threading.Thread(target=self._read, daemon=True)
            keyboard_thread = threading.Thread(target=self._read_keyboard, daemon=True)

            connection_thread.start()
            keyboard_thread.start()

            while self.running:
                pass

        except KeyboardInterrupt:
            print_info("Ctrl+C で終了します。")
            self.running = False
        finally:
            self._cleanup(connection_thread, keyboard_thread)

    def _cleanup(
        self, connection_thread: threading.Thread, keyboard_thread: threading.Thread
    ) -> None:
        """リソースのクリーンアップ"""
        connection_thread.join(timeout=1)
        keyboard_thread.join(timeout=1)
        if self.connection and self.connection.is_open():
            self.connection.close()


def main() -> None:
    """メイン関数"""
    parser = argparse.ArgumentParser(description="MSXシリアルターミナル")
    parser.add_argument(
        "connection",
        type=str,
        help="接続先 (例: COM4, /dev/ttyUSB0, 192.168.1.100:2223, telnet://192.168.1.100:2223, serial://COM1?baudrate=9600)",
    )
    parser.add_argument(
        "--baudrate",
        type=int,
        default=115200,
        help="シリアル接続時のボーレート (URI形式で指定する場合は不要)",
    )
    parser.add_argument(
        "--encoding", type=str, default="msx-jp", help="エンコーディング"
    )
    args = parser.parse_args()

    try:
        # 接続タイプを自動判定
        config = detect_connection_type(args.connection)

        terminal = MSXSerialTerminal(
            config,
            encoding=args.encoding,
            prompt_style="#00ff00 bold",
        )
        terminal.run()
    except ValueError as e:
        print_exception("エラー", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
