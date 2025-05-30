import msx_charset    # noqa: F401  # type: ignore
import threading
from typing import Union
from .connection.manager import ConnectionManager
from .input.user_input import UserInputHandler
from .transfer.file_transfer import FileTransferManager
from .ui.color_output import print_info, print_exception, print_receive
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
        while not self.stop_event.is_set():
            try:
                if self.connection_manager.connection.in_waiting():
                    data = self.connection_manager.connection.read(
                        self.connection_manager.connection.in_waiting()
                    )
                    decoded = data.decode(self.encoding)
                    if not self.suppress_output:
                        print_receive(decoded, end="")
            except Exception as e:
                print_exception("受信エラー", e)
                break

    def _input_loop(self) -> None:
        """ユーザー入力ループ"""
        while not self.stop_event.is_set():
            try:
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
