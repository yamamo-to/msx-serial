"""
MSXシリアルターミナル
"""

import msx_charset  # noqa: F401  # type: ignore
import threading
import re
from .connection.manager import ConnectionManager
from .input.user_input import UserInputHandler
from .transfer.file_transfer import FileTransferManager
from .ui.color_output import (
    print_info,
    print_exception,
)
from .connection.base import ConnectionConfig
from .modes import MSXMode


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
        self.current_mode = MSXMode.UNKNOWN.value  # 現在のMSXモード（文字列）
        # MSXプロンプトパターン（A>, B>, C>などに対応）- より厳密なパターン
        self.prompt_pattern = re.compile(r"^[A-Z]>\s*$")
        # BASICモードのプロンプトパターン
        self.basic_prompt_pattern = re.compile(r"^Ok\s*$", re.IGNORECASE)
        # MSX-DOSモードのプロンプトパターン
        self.dos_prompt_pattern = re.compile(r"^[A-Z]:>\s*$")
        self.last_data_time = 0  # 最後にデータを受信した時刻

        # コンポーネントの初期化
        self.connection_manager = ConnectionManager(config)
        self.user_input = UserInputHandler(
            prompt_style=prompt_style,
            encoding=encoding,
            connection=self.connection_manager.connection,
        )
        self.user_input.terminal = self  # UserInputHandlerに自身の参照を渡す
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
        import time

        while not self.stop_event.is_set():
            try:
                current_time = time.time()

                if self.connection_manager.connection.in_waiting():
                    data = self.connection_manager.connection.read(
                        self.connection_manager.connection.in_waiting()
                    )
                    decoded = data.decode(self.encoding)
                    buffer += decoded
                    self.last_data_time = current_time

                    if not self.suppress_output:
                        # プロンプトを検出（BASIC、MSX-DOS、一般的なプロンプトすべてをチェック）
                        if (
                            self.prompt_pattern.search(buffer)
                            or self.basic_prompt_pattern.search(buffer)
                            or self.dos_prompt_pattern.search(buffer)
                        ):
                            # プロンプトが見つかった場合、改行を追加して表示
                            lines = buffer.split("\n")
                            for i, line in enumerate(lines[:-1]):
                                if line.strip():  # 空行でない場合のみ表示
                                    self.user_input.print_receive(line)

                            # 最後の行（プロンプト）を改行付きで表示
                            last_line = lines[-1]
                            if (
                                self.prompt_pattern.search(last_line)
                                or self.basic_prompt_pattern.search(last_line)
                                or self.dos_prompt_pattern.search(last_line)
                            ):
                                self.user_input.print_receive(last_line, is_prompt=True)
                                # プロンプト表示後は改行を出力しない（ユーザー入力が上書きしないように）
                                # プロンプト表示の完了を確実にするため、少し待機
                                time.sleep(0.01)  # 10ms待機
                                self.prompt_detected = True
                                # UserInputHandlerにもプロンプト検出を通知
                                self.user_input.prompt_detected = True
                                # 強制モード更新を実行
                                self._force_mode_update(last_line)
                            else:
                                self.user_input.print_receive(last_line)
                            buffer = ""
                        else:
                            # プロンプトが検出されない場合、改行文字で分割して処理
                            if "\n" in buffer:
                                lines = buffer.split("\n")
                                # 最後の行以外を表示（最後の行は不完全な可能性があるため）
                                for i, line in enumerate(lines[:-1]):
                                    if line.strip():  # 空行でない場合のみ表示
                                        self.user_input.print_receive(line)
                                # 最後の行をバッファに残す
                                buffer = lines[-1]
                            # 改行がない場合は何もしない（バッファに蓄積）
                            # ただし、プロンプトの可能性がある場合は短いタイムアウトでチェック
                            elif self._is_prompt_candidate(buffer):
                                # プロンプト候補の場合は短いタイムアウト（20ms）でチェック
                                pass

                # バッファにデータがあり、一定時間（100ms）データが来ていない場合は表示
                elif buffer and (current_time - self.last_data_time) > 0.1:
                    if not self.suppress_output:
                        if buffer.strip():  # 空でない場合のみ表示
                            # プロンプトパターンが含まれているかチェック
                            if (
                                self.prompt_pattern.search(buffer)
                                or self.basic_prompt_pattern.search(buffer)
                                or self.dos_prompt_pattern.search(buffer)
                            ):
                                self.user_input.print_receive(buffer, is_prompt=True)
                                self.prompt_detected = True
                                # UserInputHandlerにもプロンプト検出を通知
                                self.user_input.prompt_detected = True
                                # 強制モード更新を実行
                                self._force_mode_update(buffer)
                            else:
                                self.user_input.print_receive(buffer)
                    buffer = ""
                # プロンプト候補の場合、短いタイムアウト（20ms）でチェック
                elif (
                    buffer
                    and self._is_prompt_candidate(buffer)
                    and (current_time - self.last_data_time) > 0.02
                ):
                    if not self.suppress_output:
                        if buffer.strip():  # 空でない場合のみ表示
                            # プロンプトパターンが含まれているかチェック
                            if (
                                self.prompt_pattern.search(buffer)
                                or self.basic_prompt_pattern.search(buffer)
                                or self.dos_prompt_pattern.search(buffer)
                            ):
                                self.user_input.print_receive(buffer, is_prompt=True)
                                self.prompt_detected = True
                                # UserInputHandlerにもプロンプト検出を通知
                                self.user_input.prompt_detected = True
                                # 強制モード更新を実行
                                self._force_mode_update(buffer)
                            else:
                                # プロンプト候補だが完全なプロンプトでない場合は表示
                                self.user_input.print_receive(buffer)
                    buffer = ""

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

                    time.sleep(0.05)  # 50ms待機（プロンプト表示の完了を確実にする）
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

    def _detect_mode(self, prompt_text: str) -> MSXMode:
        """プロンプトからMSXモードを検出

        Args:
            prompt_text: プロンプトテキスト

        Returns:
            検出されたMSXモード
        """
        if self.basic_prompt_pattern.search(prompt_text):
            return MSXMode.BASIC
        elif self.dos_prompt_pattern.search(prompt_text):
            return MSXMode.DOS
        elif self.prompt_pattern.search(prompt_text):
            # 一般的なプロンプト（A>など）の場合は、MSX-DOSモードと推定
            return MSXMode.DOS
        else:
            return MSXMode.UNKNOWN

    def _update_mode(self, new_mode: MSXMode) -> None:
        """MSXモードを更新

        Args:
            new_mode: 新しいモード
        """
        # モードが変更された場合のみ更新（UNKNOWNから他のモードへの変更も許可）
        if new_mode.value != self.current_mode:
            self.current_mode = new_mode.value

            # UserInputHandlerにもモード変更を通知
            self.user_input.current_mode = new_mode.value
            # 補完機能も更新
            self.user_input._update_completer_mode()

    def _force_mode_update(self, prompt_text: str) -> None:
        """プロンプトから強制的にモードを更新

        Args:
            prompt_text: プロンプトテキスト
        """
        detected_mode = self._detect_mode(prompt_text)
        if detected_mode != MSXMode.UNKNOWN:
            # 強制的にモードを更新（前回のモードに関係なく）
            self.current_mode = detected_mode.value

            # UserInputHandlerにもモード変更を通知
            self.user_input.current_mode = detected_mode.value
            # 補完機能も更新
            self.user_input._update_completer_mode()

    def set_mode(self, mode: MSXMode) -> None:
        """MSXモードを強制設定

        Args:
            mode: 設定するモード
        """
        self.current_mode = mode.value
        self.user_input.current_mode = mode.value

    def _is_prompt_candidate(self, buffer: str) -> bool:
        """バッファがプロンプト候補かどうかをチェック

        Args:
            buffer: バッファの内容

        Returns:
            プロンプト候補の場合はTrue
        """
        # プロンプト候補のパターン
        # A>, B>, C>などの一般的なプロンプトの候補
        if re.match(r"^[A-Z]$", buffer):
            return True
        # A:>, B:>, C:>などのMSX-DOSプロンプトの候補
        if re.match(r"^[A-Z]:$", buffer):
            return True
        # Okの候補（Oのみ）
        if re.match(r"^O$", buffer, re.IGNORECASE):
            return True
        # Okの候補（Okのみ）
        if re.match(r"^Ok$", buffer, re.IGNORECASE):
            return True
        return False
