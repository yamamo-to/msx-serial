#!/usr/bin/env python3
"""
MSXシリアルターミナル
MSXとのシリアル通信を行うターミナルプログラム
"""

import argparse
import base64
import chardet
import colorama
import threading
import serial
import yaml
import msx_charset
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Optional, Union
from colorama import Fore, Style as ColorStyle
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.shortcuts import radiolist_dialog
from prompt_toolkit.styles import Style
from .iot_nodes import IotNodes
from .upload import upload_program
import os


class CommandType(Enum):
    """コマンドタイプの列挙型"""

    PASTE = "@paste"
    BYTES = "@bytes"
    EXIT = "@exit"
    UPLOAD = "@upload"
    CD = "@cd"


@dataclass
class TerminalConfig:
    """ターミナル設定"""

    port: str = "/dev/tty.usbserial"
    baudrate: int = 115200
    encoding: str = "msx-jp"
    prompt_style: str = "#00ff00 bold"


class MSXSerialTerminal:
    """MSXシリアルターミナルのメインクラス"""

    def __init__(self, config: TerminalConfig):
        """初期化"""
        self.config = config
        self.ser: Optional[serial.Serial] = None
        self.running: bool = True
        iot_nodes = IotNodes()
        self.commands: List[str] = (
            iot_nodes.get_node_names() + self._load_commands()
        )
        self._setup_ui()
        colorama.init()

    def _setup_ui(self) -> None:
        """UIの初期設定"""
        self.style = Style.from_dict({"prompt": self.config.prompt_style})

        # @で始まるコマンドを優先的に表示
        special_commands = [cmd.value for cmd in CommandType]
        normal_commands = [cmd for cmd in self.commands if not cmd.startswith("@")]

        self.session = PromptSession(
            completer=WordCompleter(
                special_commands + normal_commands,
                ignore_case=True,
                sentence=True,  # 文全体を補完対象とする
            ),
            style=self.style,
            complete_in_thread=True,
            complete_while_typing=True,  # タイピング中に補完を有効化
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

    def _read_serial(self) -> None:
        """シリアル受信処理"""
        while self.running and self.ser:
            try:
                if self.ser.in_waiting > 0:
                    data = self.ser.read(self.ser.in_waiting)
                    decoded_code = bytes(data).decode(self.config.encoding)
                    print(f"{Fore.GREEN}{decoded_code}{ColorStyle.RESET_ALL}", end="")
            except Exception as e:
                if self.running:
                    print(f"{Fore.RED}[シリアルエラー] {e}{ColorStyle.RESET_ALL}")
                break

    def _paste_file(self, file_path: Union[str, Path]) -> None:
        """テキストファイルを送信"""
        with open(file_path, "rb") as f:
            raw_data = f.read()
            encoding = chardet.detect(raw_data)["encoding"]

            if encoding in ["SHIFT_JIS", "CP932", "EUC-JP"]:
                for line in raw_data.split(b"\n"):
                    if line:
                        self.ser.write(line + b"\r\n")
                        self.ser.flush()
            else:
                with open(file_path, "r", encoding=encoding) as f:
                    for line in f:
                        msx_codes = line.rstrip() + "\r\n"
                        self.ser.write(msx_codes.encode(self.config.encoding))
                        self.ser.flush()

    def _upload_file(self, file_path: Union[str, Path]) -> None:
        """ファイルをアップロード"""

        # BASICプログラムを送信
        self.ser.write(upload_program(file_path).encode("ascii"))
        self.ser.flush()

        # RUNコマンドを送信
        self.ser.write("RUN\r\n".encode("ascii"))
        self.ser.flush()
        time.sleep(1)

        # ファイルを送信
        with open(file_path, "rb") as f:
            data = f.read()
            encoded_data = base64.b64encode(data).decode("ascii")
            for i in range(0, len(encoded_data), 76):
                chunk = encoded_data[i : i + 76]
                self.ser.write(chunk.encode("ascii") + b"\r\n")
                self.ser.flush()
                time.sleep(0.5)

        self.ser.write(b"`\r\n")
        self.ser.flush()

    def _select_file(self) -> Optional[str]:
        """ファイル選択ダイアログを表示"""
        current_dir = Path.cwd()
        files = [(str(f), f.name) for f in current_dir.glob("*") if f.is_file()]

        if not files:
            print(
                f"{Fore.YELLOW}[警告] ファイルが見つかりません。{ColorStyle.RESET_ALL}"
            )
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
            print(f"{Fore.YELLOW}終了します。{ColorStyle.RESET_ALL}")
            self.running = False
            return True

        if user_input.strip() == CommandType.PASTE.value:
            file_path = self._select_file()
            if file_path:
                print(f"{Fore.BLUE}[選択] {file_path}{ColorStyle.RESET_ALL}")
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
        hex_input = input(
            f"{Fore.CYAN}16進数のバイト列を入力してください: {ColorStyle.RESET_ALL}"
        )
        try:
            bytes_data = bytes.fromhex(hex_input.replace(" ", ""))
            self.ser.write(bytes_data)
            self.ser.flush()
            print(f"{Fore.GREEN}送信: {hex_input}{ColorStyle.RESET_ALL}")
        except ValueError as e:
            print(f"{Fore.RED}エラー: 無効な16進数です - {e}{ColorStyle.RESET_ALL}")

    def _handle_upload_command(self) -> None:
        """アップロードコマンドの処理"""
        file_path = self._select_file()
        if file_path:
            print(f"{Fore.BLUE}[選択] {file_path}{ColorStyle.RESET_ALL}")
            self._upload_file(file_path)
        return True

    def _handle_cd_command(self, user_input: str) -> None:
        """ディレクトリ移動コマンドの処理"""
        try:
            # @cd の後のパスを取得
            path = user_input[len(CommandType.CD.value):].strip()
            if not path:
                # パスが指定されていない場合は現在のディレクトリを表示
                print(f"{Fore.CYAN}現在のディレクトリ: {Path.cwd()}{ColorStyle.RESET_ALL}")
                return

            # 新しいパスに移動
            new_path = Path(path).resolve()
            if new_path.exists() and new_path.is_dir():
                # 現在のディレクトリを新しいパスに変更
                os.chdir(str(new_path))
                print(f"{Fore.GREEN}ディレクトリを変更しました: {new_path}{ColorStyle.RESET_ALL}")
            else:
                print(f"{Fore.RED}エラー: 指定されたディレクトリが存在しません: {path}{ColorStyle.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}エラー: ディレクトリの変更に失敗しました - {e}{ColorStyle.RESET_ALL}")

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
                    self.ser.write(b"\r\n")
                else:
                    self._send_user_input(user_input)

            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Ctrl+C で終了します。{ColorStyle.RESET_ALL}")
                self.running = False
                break
            except Exception as e:
                print(f"{Fore.RED}[キーボードエラー] {e}{ColorStyle.RESET_ALL}")
                self.running = False
                break

    def _send_user_input(self, user_input: str) -> None:
        """ユーザー入力を送信"""
        for line in user_input.splitlines():
            if line.strip() == "^C":
                self.ser.write(b"\x03")  # Ctrl-C
            elif line.strip() == "^[":
                self.ser.write(b"\x1b")  # ESC
            else:
                msx_code = line + "\r\n"
                self.ser.write(msx_code.encode(self.config.encoding))
        self.ser.flush()

    def run(self) -> None:
        """ターミナルを実行"""
        try:
            self.ser = serial.Serial(self.config.port, self.config.baudrate, timeout=1)

            serial_thread = threading.Thread(target=self._read_serial, daemon=True)
            keyboard_thread = threading.Thread(target=self._read_keyboard, daemon=True)

            serial_thread.start()
            keyboard_thread.start()

            while self.running:
                pass

        except KeyboardInterrupt:
            print(f"{Fore.YELLOW}Ctrl+C で終了します。{ColorStyle.RESET_ALL}")
            self.running = False
        finally:
            self._cleanup(serial_thread, keyboard_thread)

    def _cleanup(
        self, serial_thread: threading.Thread, keyboard_thread: threading.Thread
    ) -> None:
        """リソースのクリーンアップ"""
        serial_thread.join(timeout=1)
        keyboard_thread.join(timeout=1)
        if self.ser and self.ser.is_open:
            self.ser.close()


def main() -> None:
    """メイン関数"""
    parser = argparse.ArgumentParser(description="MSXシリアルターミナル")
    parser.add_argument(
        "--port", type=str, required=True, help="シリアルポート"
    )
    parser.add_argument("--baudrate", type=int, default=115200, help="ボーレート")
    parser.add_argument("--encoding", type=str, default='msx-jp', help="エンコーディング")
    args = parser.parse_args()

    config = TerminalConfig(port=args.port, baudrate=args.baudrate, encoding=args.encoding)
    terminal = MSXSerialTerminal(config)
    terminal.run()


if __name__ == "__main__":
    main()
