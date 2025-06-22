import msx_charset  # noqa: F401  # type: ignore
import threading
import re
from .connection.manager import ConnectionManager
from .input.user_input import UserInputHandler
from .transfer.file_transfer import FileTransferManager
from .ui.color_output import (
    print_info,
    print_exception,
    print_receive,
    print_prompt_receive,
    print_receive_no_newline,
)
from .connection.base import ConnectionConfig


class MSXTerminal:
    def __init__(
        self,
        config: ConnectionConfig,
        encoding: str = "msx-jp",
        prompt_style: str = "#00ff00 bold",
    ):
        self.encoding = encoding
        self.prompt_style = prompt_style
        self.stop_event = threading.Event()
        self.suppress_output = False  # 出力抑制フラグ
        self.prompt_detected = False  # プロンプト検出フラグ
        # MSXプロンプトパターン（A>, B>, C>などに対応）
        self.prompt_pattern = re.compile(r"[A-Z]>\s*$")

        # コンポーネントの初期化
        self.connection_manager = ConnectionManager(config)
        self.user_input = UserInputHandler(
            prompt_style=prompt_style,
            encoding=encoding,
            connection=self.connection_manager.connection,
        )
        self.file_transfer = FileTransferManager(
            connection=self.connection_manager.connection,
            encoding=encoding,
        )
        self.file_transfer.set_terminal(self)  # 自身の参照を渡す

    def run(self) -> None:
        """ターミナルメインループ"""
        try:
            # バックグラウンド受信スレッド
            threading.Thread(target=self._read_loop, daemon=True).start()

            # ユーザー入力ループ（メインスレッド）
            self._input_loop()

        except KeyboardInterrupt:
            print_info("\nCtrl+C で終了します。")
        finally:
            self.stop_event.set()
            self.connection_manager.close()

    def _read_loop(self) -> None:
        """受信データを非同期に表示"""
        buffer = ""
        while not self.stop_event.is_set():
            try:
                if self.connection_manager.connection.in_waiting():
                    data = self.connection_manager.connection.read(
                        self.connection_manager.connection.in_waiting()
                    )
                    decoded = data.decode(self.encoding)
                    buffer += decoded

                    if not self.suppress_output:
                        # プロンプトを検出
                        if self.prompt_pattern.search(buffer):
                            # プロンプトが見つかった場合、改行を追加して表示
                            lines = buffer.split("\n")
                            for i, line in enumerate(lines[:-1]):
                                print_receive(line)

                            # 最後の行（プロンプト）を改行付きで表示
                            last_line = lines[-1]
                            if self.prompt_pattern.search(last_line):
                                print_prompt_receive(last_line)
                                self.prompt_detected = True
                            else:
                                print_receive_no_newline(last_line)
                            buffer = ""
                        else:
                            # 通常の出力
                            print_receive_no_newline(decoded)

            except Exception as e:
                print_exception("受信エラー", e)
                break

    def _input_loop(self) -> None:
        """ユーザー入力ループ"""
        while not self.stop_event.is_set():
            try:
                # プロンプトが検出された場合、少し待機してから入力を開始
                if self.prompt_detected:
                    import time

                    time.sleep(0.1)  # 100ms待機
                    self.prompt_detected = False

                user_input = self.user_input.prompt()
                if self.user_input.handle_special_commands(
                    user_input, self.file_transfer, self.stop_event
                ):
                    continue
                self.user_input.send(user_input)

            except KeyboardInterrupt:
                print_info("Ctrl+C を検出しました。終了します。")
                break
            except Exception as e:
                print_exception("入力エラー", e)
                break
