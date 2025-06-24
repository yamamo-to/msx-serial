import unittest
from unittest.mock import patch, MagicMock, Mock, call

from msx_serial.core.optimized_session import MSXSession
from msx_serial.connection.dummy import DummyConfig
from msx_serial.protocol.msx_detector import MSXMode


class TestMSXSession(unittest.TestCase):
    """MSXSessionの包括的なテスト"""

    @patch("msx_serial.completion.iot_loader.IotNodes")
    @patch("msx_serial.io.input_session.PromptSession")
    def setUp(self, mock_prompt_session: MagicMock, mock_iot_nodes: MagicMock) -> None:
        """各テストの準備"""
        # PromptSessionのモック設定
        mock_session = Mock()
        mock_session.prompt.return_value = "test input"
        mock_prompt_session.return_value = mock_session

        # IotNodesのモック設定
        mock_iot_nodes.return_value.get_node_names.return_value = []

        # DummyConfigでセッションを初期化
        self.config = DummyConfig()
        self.session = MSXSession(
            config=self.config, encoding="msx-jp", prompt_style="#00ff00 bold"
        )

    def test_init_default_parameters(self) -> None:
        """初期化のデフォルトパラメータテスト"""
        self.assertEqual(self.session.encoding, "msx-jp")
        self.assertFalse(self.session.stop_event.is_set())
        self.assertFalse(self.session.suppress_output)
        self.assertFalse(self.session.prompt_detected)
        self.assertEqual(self.session.last_data_time, 0)

    def test_init_performance_settings(self) -> None:
        """パフォーマンス設定の初期値テスト"""
        self.assertEqual(self.session.receive_delay, 0.0001)
        self.assertEqual(self.session.batch_size, 1)
        self.assertEqual(self.session.timeout_check_interval, 0.01)

    def test_init_components(self) -> None:
        """各コンポーネントの初期化テスト"""
        self.assertIsNotNone(self.session.connection_manager)
        self.assertIsNotNone(self.session.protocol_detector)
        self.assertIsNotNone(self.session.data_processor)
        self.assertIsNotNone(self.session.display)
        self.assertIsNotNone(self.session.user_interface)
        self.assertIsNotNone(self.session.file_transfer)

    def test_init_with_custom_parameters(self) -> None:
        """カスタムパラメータでの初期化テスト"""
        config = DummyConfig()
        with (
            patch("msx_serial.completion.iot_loader.IotNodes"),
            patch("msx_serial.io.input_session.PromptSession"),
        ):
            session = MSXSession(
                config=config, encoding="utf-8", prompt_style="#ff0000"
            )
            self.assertEqual(session.encoding, "utf-8")

    @patch("msx_serial.core.optimized_session.print_info")
    @patch("threading.Thread")
    def test_run_normal_flow(
        self, mock_thread: MagicMock, mock_print_info: MagicMock
    ) -> None:
        """正常な実行フローのテスト"""
        # スレッド開始をモック
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance

        # _input_loopをモック（即座に終了）
        with patch.object(self.session, "_input_loop") as mock_input_loop:
            self.session.run()

            # print_infoが呼ばれることを確認
            mock_print_info.assert_called_with("Starting MSX Terminal Session")

            # スレッドが開始されることを確認
            mock_thread.assert_called_once()
            mock_thread_instance.start.assert_called_once()

            # input_loopが呼ばれることを確認
            mock_input_loop.assert_called_once()

    @patch("msx_serial.core.optimized_session.print_info")
    @patch("threading.Thread")
    def test_run_keyboard_interrupt(
        self, mock_thread: MagicMock, mock_print_info: MagicMock
    ) -> None:
        """KeyboardInterrupt処理のテスト"""
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance

        # _input_loopでKeyboardInterruptを発生
        with patch.object(self.session, "_input_loop", side_effect=KeyboardInterrupt):
            self.session.run()

            # 正しいメッセージが表示されることを確認
            calls = [
                call("Starting MSX Terminal Session"),
                call("\nExiting on Ctrl+C..."),
            ]
            mock_print_info.assert_has_calls(calls)

    @patch("msx_serial.core.optimized_session.print_info")
    @patch("threading.Thread")
    def test_run_cleanup(
        self, mock_thread: MagicMock, mock_print_info: MagicMock
    ) -> None:
        """終了時のクリーンアップ処理テスト"""
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance

        # displayにflushメソッドを追加
        self.session.display.flush = Mock()

        with patch.object(self.session, "_input_loop"):
            self.session.run()

            # stop_eventがセットされることを確認
            self.assertTrue(self.session.stop_event.is_set())

            # displayのflushが呼ばれることを確認
            self.session.display.flush.assert_called_once()

    def test_process_incoming_data_no_data(self) -> None:
        """データなしの場合の_process_incoming_dataテスト"""
        # in_waitingが0を返すようにモック
        self.session.connection_manager.connection.in_waiting = Mock(return_value=0)

        result = self.session._process_incoming_data()
        self.assertFalse(result)

    def test_process_incoming_data_with_data(self) -> None:
        """データありの場合の_process_incoming_dataテスト"""
        # データが利用可能な状態をモック
        self.session.connection_manager.connection.in_waiting = Mock(return_value=1)
        self.session.connection_manager.connection.read = Mock(return_value=b"A")

        # data_processorのモック
        mock_output = [("text", False)]
        self.session.data_processor.process_data = Mock(return_value=mock_output)

        # _display_outputのモック
        with patch.object(self.session, "_display_output") as mock_display:
            result = self.session._process_incoming_data()

            self.assertTrue(result)
            self.assertGreater(self.session.last_data_time, 0)
            mock_display.assert_called_once_with("text", False)

    def test_process_incoming_data_empty_read(self) -> None:
        """空のreadの場合の_process_incoming_dataテスト"""
        self.session.connection_manager.connection.in_waiting = Mock(return_value=1)
        self.session.connection_manager.connection.read = Mock(return_value=b"")

        result = self.session._process_incoming_data()
        self.assertFalse(result)

    def test_process_incoming_data_decode_error(self) -> None:
        """デコードエラーの場合の_process_incoming_dataテスト"""
        self.session.connection_manager.connection.in_waiting = Mock(return_value=1)
        # Create a mock that raises UnicodeDecodeError when read
        mock_data = Mock()
        mock_data.decode.side_effect = UnicodeDecodeError(
            "msx-jp", b"\xff", 0, 1, "invalid start byte"
        )
        self.session.connection_manager.connection.read = Mock(return_value=mock_data)

        with patch(
            "msx_serial.core.optimized_session.print_exception"
        ) as mock_print_exc:
            result = self.session._process_incoming_data()

            self.assertFalse(result)
            mock_print_exc.assert_called_once()

    def test_process_incoming_data_suppressed_output(self) -> None:
        """出力が抑制されている場合のテスト"""
        self.session.suppress_output = True
        self.session.connection_manager.connection.in_waiting = Mock(return_value=1)
        self.session.connection_manager.connection.read = Mock(return_value=b"A")

        with patch.object(self.session, "_display_output") as mock_display:
            result = self.session._process_incoming_data()

            self.assertTrue(result)
            mock_display.assert_not_called()

    def test_check_timeouts_suppressed_output(self) -> None:
        """出力が抑制されている場合の_check_timeoutsテスト"""
        self.session.suppress_output = True
        self.session._check_timeouts()
        # 例外が発生しないことを確認

    def test_check_timeouts_normal_timeout(self) -> None:
        """通常のタイムアウト処理テスト"""
        # タイムアウト結果をモック
        self.session.data_processor.check_timeout = Mock(
            return_value=("timeout_text", True)
        )

        with patch.object(self.session, "_display_output") as mock_display:
            self.session._check_timeouts()
            mock_display.assert_called_with("timeout_text", True)

    def test_check_timeouts_prompt_candidate(self) -> None:
        """プロンプト候補タイムアウト処理テスト"""
        # プロンプト候補結果をモック
        self.session.data_processor.check_timeout = Mock(return_value=None)
        self.session.data_processor.check_prompt_candidate = Mock(
            return_value=("prompt_text", True)
        )

        with patch.object(self.session, "_display_output") as mock_display:
            self.session._check_timeouts()
            mock_display.assert_called_with("prompt_text", True)

    def test_check_timeouts_buffer_content(self) -> None:
        """バッファコンテンツ処理テスト"""
        # バッファの状態をモック
        self.session.data_processor.check_timeout = Mock(return_value=None)
        self.session.data_processor.check_prompt_candidate = Mock(return_value=None)
        self.session.data_processor.buffer.has_content = Mock(return_value=True)
        self.session.data_processor.buffer.get_content = Mock(
            return_value="Microsoft BASIC Ok"
        )
        self.session.data_processor.buffer.clear = Mock()
        self.session.protocol_detector.detect_prompt = Mock(return_value=True)

        with (
            patch.object(self.session, "_display_output") as mock_display,
            patch.object(self.session, "_is_basic_startup", return_value=True),
        ):
            self.session._check_timeouts()

            mock_display.assert_called_with("Microsoft BASIC Ok", True)
            self.session.data_processor.buffer.clear.assert_called_once()

    def test_is_basic_startup_true_cases(self) -> None:
        """BASIC起動シーケンス検出のテスト（True cases）"""
        test_cases = [
            "Microsoft BASIC Ok",
            "MSX BASIC version 2.0 Ok",
            "Copyright (C) 1985 Microsoft Ok",
            "BASIC 2.0 Ok",
        ]

        for content in test_cases:
            with self.subTest(content=content):
                result = self.session._is_basic_startup(content)
                self.assertTrue(result)

    def test_is_basic_startup_false_cases(self) -> None:
        """BASIC起動シーケンス検出のテスト（False cases）"""
        test_cases = [
            "BASIC",  # Okで終わらない
            "Ok",  # BASICキーワードがない
            "Microsoft",  # Okで終わらない
            "Some other text Ok",  # BASICキーワードがない
        ]

        for content in test_cases:
            with self.subTest(content=content):
                result = self.session._is_basic_startup(content)
                self.assertFalse(result)

    def test_display_output_empty_text(self) -> None:
        """空のテキストの_display_outputテスト"""
        with patch.object(self.session.user_interface, "print_receive") as mock_print:
            self.session._display_output("", False)
            mock_print.assert_not_called()

    def test_display_output_with_text(self) -> None:
        """テキストありの_display_outputテスト"""
        with patch.object(self.session.user_interface, "print_receive") as mock_print:
            self.session._display_output("test text", False)
            mock_print.assert_called_once_with("test text", False)

    def test_display_output_prompt_with_text(self) -> None:
        """プロンプトありテキストの_display_outputテスト"""
        with (
            patch.object(self.session.user_interface, "print_receive") as mock_print,
            patch.object(self.session, "_update_prompt_state") as mock_update,
        ):
            self.session._display_output("Ok", True)

            mock_print.assert_called_once_with("Ok", True)
            mock_update.assert_called_once_with("Ok")

    def test_display_output_prompt_empty_text(self) -> None:
        """空テキストのプロンプト処理テスト"""
        self.session.data_processor.last_prompt_content = "saved_prompt"

        with (
            patch.object(self.session.user_interface, "print_receive") as mock_print,
            patch.object(self.session, "_update_prompt_state") as mock_update,
        ):
            self.session._display_output("", True)

            mock_print.assert_not_called()
            mock_update.assert_called_once_with("saved_prompt")

    def test_update_prompt_state_basic(self) -> None:
        """基本的なプロンプト状態更新テスト"""
        self.session.protocol_detector.detect_mode = Mock(return_value=MSXMode.DOS)
        self.session.protocol_detector.current_mode = "basic"
        self.session.protocol_detector.debug_mode = False

        with patch.object(self.session.user_interface, "update_mode") as mock_update:
            self.session._update_prompt_state("A>")

            self.assertTrue(self.session.prompt_detected)
            self.assertTrue(self.session.user_interface.prompt_detected)
            self.assertEqual(self.session.protocol_detector.current_mode, "dos")
            mock_update.assert_called_once_with("dos")

    def test_update_prompt_state_unknown_mode(self) -> None:
        """不明モードの場合のプロンプト状態更新テスト"""
        self.session.protocol_detector.detect_mode = Mock(return_value=MSXMode.UNKNOWN)
        original_mode = self.session.protocol_detector.current_mode

        with patch.object(self.session.user_interface, "update_mode") as mock_update:
            self.session._update_prompt_state("unknown prompt")

            # モードが変更されないことを確認
            self.assertEqual(self.session.protocol_detector.current_mode, original_mode)
            mock_update.assert_not_called()

    @patch("msx_serial.core.optimized_session.print_info")
    def test_update_prompt_state_debug_mode(self, mock_print_info: MagicMock) -> None:
        """デバッグモード時のプロンプト状態更新テスト"""
        self.session.protocol_detector.detect_mode = Mock(return_value=MSXMode.BASIC)
        self.session.protocol_detector.current_mode = "dos"
        self.session.protocol_detector.debug_mode = True

        with patch.object(self.session.user_interface, "update_mode"):
            self.session._update_prompt_state("Ok")

            mock_print_info.assert_called_with("[MSX Debug] Mode updated: dos -> basic")

    def test_set_mode(self) -> None:
        """set_modeのテスト"""
        with patch.object(self.session.user_interface, "update_mode") as mock_update:
            self.session.set_mode("dos")

            self.assertEqual(self.session.protocol_detector.current_mode, "dos")
            mock_update.assert_called_once_with("dos")

    @patch("msx_serial.core.optimized_session.print_info")
    def test_toggle_debug_mode_enable(self, mock_print_info: MagicMock) -> None:
        """デバッグモード有効化テスト"""
        self.session.protocol_detector.debug_mode = False

        self.session.toggle_debug_mode()

        self.assertTrue(self.session.protocol_detector.debug_mode)
        mock_print_info.assert_called_with("Debug mode enabled")

    @patch("msx_serial.core.optimized_session.print_info")
    def test_toggle_debug_mode_disable(self, mock_print_info: MagicMock) -> None:
        """デバッグモード無効化テスト"""
        self.session.protocol_detector.debug_mode = True

        self.session.toggle_debug_mode()

        self.assertFalse(self.session.protocol_detector.debug_mode)
        mock_print_info.assert_called_with("Debug mode disabled")

    @patch("msx_serial.core.optimized_session.print_info")
    def test_toggle_debug_mode_no_attribute(self, mock_print_info: MagicMock) -> None:
        """debug_mode属性がない場合のテスト"""
        # debug_mode属性を削除
        if hasattr(self.session.protocol_detector, "debug_mode"):
            delattr(self.session.protocol_detector, "debug_mode")

        self.session.toggle_debug_mode()

        self.assertTrue(self.session.protocol_detector.debug_mode)
        mock_print_info.assert_called_with("Debug mode enabled")

    @patch("time.sleep")
    def test_input_loop_normal_flow(self, mock_sleep: MagicMock) -> None:
        """正常な入力ループフローのテスト"""
        # プロンプト状態を設定
        self.session.prompt_detected = True

        # user_interfaceのモック設定
        self.session.user_interface.prompt = Mock(side_effect=["test", "@exit"])
        self.session.user_interface.handle_special_commands = Mock(
            side_effect=[False, True]
        )
        self.session.user_interface.send = Mock()

        # ループを実行（2回目で終了）
        self.session._input_loop()

        # sleepが呼ばれることを確認
        mock_sleep.assert_called_with(0.005)

        # prompt_detectedがリセットされることを確認
        self.assertFalse(self.session.prompt_detected)

        # sendが呼ばれることを確認
        self.session.user_interface.send.assert_called_once_with("test")

    @patch("msx_serial.core.optimized_session.print_info")
    def test_input_loop_keyboard_interrupt(self, mock_print_info: MagicMock) -> None:
        """入力ループでのKeyboardInterrupt処理テスト"""
        self.session.user_interface.prompt = Mock(side_effect=KeyboardInterrupt)

        self.session._input_loop()

        mock_print_info.assert_called_with("Ctrl+C detected. Exiting...")

    @patch("msx_serial.core.optimized_session.print_exception")
    def test_input_loop_exception(self, mock_print_exception: MagicMock) -> None:
        """入力ループでの例外処理テスト"""
        test_exception = Exception("test error")
        self.session.user_interface.prompt = Mock(side_effect=test_exception)

        self.session._input_loop()

        mock_print_exception.assert_called_with("Input error", test_exception)

    @patch("time.time")
    @patch("time.sleep")
    @patch("msx_serial.core.optimized_session.print_exception")
    def test_receive_loop_normal_operation(
        self,
        mock_print_exception: MagicMock,
        mock_sleep: MagicMock,
        mock_time: MagicMock,
    ) -> None:
        """受信ループの正常動作テスト"""
        # タイムアウトチェック間隔を短縮してテストしやすくする
        self.session.timeout_check_interval = 0.001

        call_count = 0

        def time_side_effect():
            nonlocal call_count
            call_count += 1
            # タイムアウトチェック間隔を満たすための時間経過をシミュレート
            return call_count * 0.002

        mock_time.side_effect = time_side_effect

        # _process_incoming_dataのモック（最初はデータなし、その後停止）
        process_call_count = 0

        def process_data_side_effect():
            nonlocal process_call_count
            process_call_count += 1
            if process_call_count >= 3:  # 3回目で停止
                self.session.stop_event.set()
            return False  # データなし

        with (
            patch.object(
                self.session,
                "_process_incoming_data",
                side_effect=process_data_side_effect,
            ),
            patch.object(self.session, "_check_timeouts") as mock_check_timeouts,
        ):

            self.session._receive_loop()

            # タイムアウトチェックが呼ばれることを確認
            mock_check_timeouts.assert_called()

    @patch("msx_serial.core.optimized_session.print_exception")
    def test_receive_loop_exception_handling(
        self, mock_print_exception: MagicMock
    ) -> None:
        """受信ループの例外処理テスト"""
        test_exception = Exception("test error")

        with patch.object(
            self.session, "_process_incoming_data", side_effect=test_exception
        ):
            self.session._receive_loop()

            mock_print_exception.assert_called_with("Receive error", test_exception)

    @patch("time.sleep")
    def test_receive_loop_adaptive_delay(self, mock_sleep: MagicMock) -> None:
        """受信ループの適応的遅延テスト"""
        call_count = 0

        def mock_process_data():
            nonlocal call_count
            call_count += 1
            if call_count <= 3:
                return False  # データなし
            else:
                self.session.stop_event.set()
                return False

        with (
            patch.object(
                self.session, "_process_incoming_data", side_effect=mock_process_data
            ),
            patch.object(self.session, "_check_timeouts"),
        ):
            self.session._receive_loop()

            # sleepが呼ばれることを確認（適応的遅延）
            self.assertTrue(mock_sleep.called)

    @patch("time.sleep")
    def test_receive_loop_long_consecutive_empty_reads(
        self, mock_sleep: MagicMock
    ) -> None:
        """長時間のデータなし状態での適応的遅延テスト"""
        call_count = 0

        def mock_process_data():
            nonlocal call_count
            call_count += 1
            if call_count <= 7:  # 5回以上空読み込みをシミュレート
                return False  # データなし
            else:
                self.session.stop_event.set()
                return False

        with (
            patch.object(
                self.session, "_process_incoming_data", side_effect=mock_process_data
            ),
            patch.object(self.session, "_check_timeouts"),
        ):
            self.session._receive_loop()

            # sleepが異なる値で呼ばれることを確認
            sleep_calls = mock_sleep.call_args_list
            self.assertTrue(
                any(call[0][0] == 0.0001 for call in sleep_calls)
            )  # 初期の短い遅延
            self.assertTrue(
                any(call[0][0] == 0.001 for call in sleep_calls)
            )  # 長期間後の遅延

    @patch("time.sleep")
    def test_receive_loop_data_then_no_data(self, mock_sleep: MagicMock) -> None:
        """データありからデータなしへの遷移テスト"""
        call_count = 0

        def mock_process_data():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return True  # 最初はデータあり
            elif call_count <= 3:
                return False  # その後データなし
            else:
                self.session.stop_event.set()
                return False

        with (
            patch.object(
                self.session, "_process_incoming_data", side_effect=mock_process_data
            ),
            patch.object(self.session, "_check_timeouts"),
        ):
            self.session._receive_loop()

            # データありの場合、consecutive_empty_readsがリセットされ、
            # その後のデータなしで短い遅延が使われることを確認
            sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
            self.assertIn(0.0001, sleep_calls)  # 短い遅延が使われている


if __name__ == "__main__":
    unittest.main()
