"""
Tests for user interface module
"""

import threading
from unittest.mock import Mock, patch

from msx_serial.io.user_interface import UserInterface


class TestUserInterface:
    """Test UserInterface class"""

    def setup_method(self):
        """Setup test"""
        # パッチコンテキストを設定して、各テストでPromptSessionをモックする
        self.mock_prompt_session_patcher = patch(
            "msx_serial.io.input_session.PromptSession"
        )
        self.mock_prompt_session = self.mock_prompt_session_patcher.start()

        # PromptSessionのモックを設定
        mock_session = Mock()
        mock_session.prompt.return_value = "mocked input"
        self.mock_prompt_session.return_value = mock_session

        self.mock_connection = Mock()
        self.ui = UserInterface("#00ff00 bold", "utf-8", self.mock_connection)

    def teardown_method(self):
        """Teardown test"""
        self.mock_prompt_session_patcher.stop()

    def test_init(self):
        """Test initialization"""
        assert self.ui.current_mode == "unknown"
        assert self.ui.prompt_detected is False
        assert self.ui.display is not None
        assert self.ui.input_session is not None
        assert self.ui.command_handler is not None
        assert self.ui.data_sender is not None

    def test_update_mode(self):
        """Test mode update"""
        self.ui.update_mode("basic")
        assert self.ui.current_mode == "basic"

    def test_prompt_detected_attribute(self):
        """Test prompt detected attribute"""
        self.ui.prompt_detected = True
        assert self.ui.prompt_detected is True

    def test_print_receive_regular(self):
        """Test printing regular received text"""
        with patch.object(self.ui.display, "print_receive") as mock_print:
            self.ui.print_receive("test message")
            mock_print.assert_called_once_with("test message", False)

    def test_print_receive_prompt(self):
        """Test printing prompt text"""
        with patch.object(self.ui.display, "print_receive") as mock_print:
            self.ui.print_receive("A>", is_prompt=True)
            mock_print.assert_called_once_with("A>", True)

    def test_prompt(self):
        """Test getting user input"""
        with patch.object(self.ui.input_session, "prompt", return_value="user input"):
            result = self.ui.prompt()
            assert result == "user input"

    def test_handle_special_commands_command(self):
        """Test handling special commands that are commands"""
        mock_file_transfer = Mock()
        stop_event = threading.Event()

        with patch.object(
            self.ui.command_handler, "handle_special_commands", return_value=True
        ):
            result = self.ui.handle_special_commands(
                "@exit", mock_file_transfer, stop_event
            )
            assert result is True

    def test_handle_special_commands_not_command(self):
        """Test handling special commands that are not commands"""
        mock_file_transfer = Mock()
        stop_event = threading.Event()

        with patch.object(
            self.ui.command_handler, "handle_special_commands", return_value=False
        ):
            result = self.ui.handle_special_commands(
                "normal text", mock_file_transfer, stop_event
            )
            assert result is False

    def test_send(self):
        """Test sending data"""
        with patch.object(self.ui.data_sender, "send") as mock_send:
            self.ui.send("test data")
            mock_send.assert_called_once_with("test data")

    def test_clear_screen(self):
        """Test clearing screen"""
        with patch.object(self.ui.display, "clear_screen") as mock_clear:
            self.ui.clear_screen()
            mock_clear.assert_called_once()

    def test_refresh_dos_cache_not_dos_mode(self):
        """Test refresh_dos_cache when not in DOS mode"""
        self.ui.current_mode = "basic"

        # DOSモードでない場合はFalseを返す
        result = self.ui.refresh_dos_cache()
        assert result is False

    def test_refresh_dos_cache_no_completer(self):
        """Test refresh_dos_cache when completer is not initialized"""
        self.ui.current_mode = "dos"
        self.ui.input_session.completer = None

        # Completerが初期化されていない場合はFalseを返す
        result = self.ui.refresh_dos_cache()
        assert result is False

    def test_refresh_dos_cache_success(self):
        """Test refresh_dos_cache with successful refresh"""
        self.ui.current_mode = "dos"

        # モックのCompleterとDOSCompleterを設定
        mock_completer = Mock()
        mock_dos_completer = Mock()
        mock_filesystem_manager = Mock()
        mock_filesystem_manager.refresh_directory_cache_sync.return_value = True

        mock_dos_completer.filesystem_manager = mock_filesystem_manager
        mock_completer.dos_completer = mock_dos_completer
        self.ui.input_session.completer = mock_completer

        with patch("msx_serial.io.user_interface.logger") as mock_logger:
            result = self.ui.refresh_dos_cache()
            assert result is True
            mock_logger.info.assert_any_call("DOSファイルキャッシュを更新中...")
            mock_logger.info.assert_any_call(
                "DOSファイルキャッシュの更新が完了しました"
            )

    def test_refresh_dos_cache_failure(self):
        """Test refresh_dos_cache with failed refresh"""
        self.ui.current_mode = "dos"

        # モックのCompleterとDOSCompleterを設定
        mock_completer = Mock()
        mock_dos_completer = Mock()
        mock_filesystem_manager = Mock()
        mock_filesystem_manager.refresh_directory_cache_sync.return_value = False

        mock_dos_completer.filesystem_manager = mock_filesystem_manager
        mock_completer.dos_completer = mock_dos_completer
        self.ui.input_session.completer = mock_completer

        with patch("msx_serial.io.user_interface.logger") as mock_logger:
            result = self.ui.refresh_dos_cache()
            assert result is False
            mock_logger.info.assert_any_call("DOSファイルキャッシュを更新中...")
            mock_logger.error.assert_any_call(
                "DOSファイルキャッシュの更新に失敗しました"
            )

    def test_debug_dos_completion(self):
        """Test debug_dos_completion method"""
        # モードを設定
        self.ui.current_mode = "dos"

        # モックのCompleterとDOSCompleterを設定
        mock_completer = Mock()
        mock_dos_completer = Mock()
        mock_filesystem_manager = Mock()

        # parse_dos_command_lineの戻り値を設定
        mock_filesystem_manager.parse_dos_command_line.return_value = ("TYPE", ["T"], 5)
        mock_completer.get_completions.return_value = []  # イテラブルにする

        mock_dos_completer.filesystem_manager = mock_filesystem_manager
        mock_completer.dos_completer = mock_dos_completer
        mock_completer.current_mode = "dos"
        self.ui.input_session.completer = mock_completer

        with patch("msx_serial.io.user_interface.logger") as mock_logger:
            result = self.ui.debug_dos_completion("TYPE T")

            # デバッグ情報が出力されることを確認
            mock_logger.debug.assert_any_call("現在のモード: dos")
            mock_logger.debug.assert_any_call("Completerの現在モード: dos")

            # リストが返されることを確認
            assert isinstance(result, list)

    def test_update_dos_directory_no_completer(self):
        """Test update_dos_directory when completer is not available"""
        self.ui.input_session.completer = None

        # Completerが利用できない場合は何も起こらない
        self.ui.update_dos_directory("A:\\")
        # 例外が発生しないことを確認

    def test_update_completer_mode(self):
        """Test _update_completer_mode method"""
        with patch.object(self.ui, "update_mode") as mock_update:
            self.ui._update_completer_mode()
            mock_update.assert_called_with(self.ui.current_mode)

    def test_set_data_processor(self):
        """Test set_data_processor method"""
        mock_processor = Mock()
        self.ui.set_data_processor(mock_processor)

        # DataSenderにプロセッサーが設定されることを確認
        assert self.ui.data_sender.data_processor == mock_processor
