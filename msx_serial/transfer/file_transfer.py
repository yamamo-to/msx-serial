"""
MSXシリアルターミナルのファイル転送処理
"""

import time
import base64
import chardet
from pathlib import Path
from tqdm import tqdm
from .basic_sender import send_basic_program
from ..ui.color_output import print_info, print_exception
from ..connection.base import Connection
from typing import TYPE_CHECKING, Optional, Union

if TYPE_CHECKING:
    from ..terminal import MSXTerminal


class FileTransferManager:
    """ファイル転送マネージャー"""

    def __init__(self, connection: Connection, encoding: str):
        """初期化

        Args:
            connection: 接続オブジェクト
            encoding: 文字エンコーディング
        """
        self.connection = connection
        self.encoding = encoding
        self.chunk_size = 1024
        self.timeout = 10.0
        self.terminal: Optional["MSXTerminal"] = None  # MSXTerminalインスタンスへの参照

    def set_terminal(self, terminal: Optional["MSXTerminal"]) -> None:
        """MSXTerminalインスタンスを設定"""
        self.terminal = terminal

    def paste_file(self, file_path: Union[Path, str]) -> None:
        with open(file_path, "rb") as f:
            raw = f.read()
            enc = chardet.detect(raw)["encoding"]

        with open(file_path, "r", encoding=enc) as f:
            for line in f:
                encoded_line = line.rstrip().encode(self.encoding)
                self.connection.write(encoded_line)
                self.connection.flush()

    def _check_ok(self) -> bool:
        """受信バッファに:改行OKが含まれているか確認"""
        if self.connection.in_waiting():
            data = self.connection.read(self.connection.in_waiting())
            try:
                text = data.decode(self.encoding)
                return ":? `" in text
            except UnicodeDecodeError:
                pass
        return False

    def upload_file(self, file_path: str) -> None:
        try:
            # 出力を抑制
            if self.terminal:
                self.terminal.suppress_output = True

            # BASICプログラムのアップロード
            self.connection.write(
                send_basic_program(
                    "upload.bas",
                    {"filename": Path(file_path).name},
                ).encode("utf-8")
            )
            self.connection.flush()

            # BASICプログラムの実行
            self.connection.write(b"RUN\r\n")
            self.connection.flush()
            time.sleep(1)

            with open(file_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("ascii")
                with tqdm(total=len(encoded), desc="アップロード中", unit="B") as pbar:
                    for i in range(0, len(encoded), 76):
                        chunk = encoded[i : i + 76]
                        self.connection.write((chunk + "\r\n").encode("ascii"))
                        self.connection.flush()
                        pbar.update(len(chunk))
                        time.sleep(0.5)

            self.connection.write(b"`\r\n")
            self.connection.flush()
            print_info("アップロード完了")

        except Exception as e:
            print_exception("アップロード失敗", e)
        finally:
            # 出力抑制を解除
            if self.terminal:
                time.sleep(5)
                self.terminal.suppress_output = False
            self.connection.write(b"\r\nNEW\r\n")
            self.connection.flush()
