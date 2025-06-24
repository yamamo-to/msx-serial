import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock, mock_open
from msx_serial.transfer.file_transfer import FileTransferManager
from msx_serial.connection.dummy import DummyConnection, DummyConfig


class TestFileTransferManagerSimple(unittest.TestCase):
    """FileTransferManagerのシンプルテスト"""

    def setUp(self) -> None:
        """各テストの準備"""
        config = DummyConfig()
        self.connection = DummyConnection(config)
        self.manager = FileTransferManager(self.connection, "utf-8")

    def test_init(self) -> None:
        """初期化のテスト"""
        self.assertEqual(self.manager.connection, self.connection)
        self.assertEqual(self.manager.encoding, "utf-8")
        self.assertEqual(self.manager.chunk_size, 1024)
        self.assertEqual(self.manager.timeout, 10.0)
        self.assertIsNone(self.manager.terminal)

    def test_set_terminal(self) -> None:
        """ターミナル設定のテスト"""
        mock_terminal = Mock()
        self.manager.set_terminal(mock_terminal)
        self.assertEqual(self.manager.terminal, mock_terminal)

    @patch("msx_serial.transfer.file_transfer.print_exception")
    def test_paste_file_not_found(self, mock_print_exception: MagicMock) -> None:
        """存在しないファイルのペーストテスト"""
        self.manager.paste_file("non_existent_file.txt")
        mock_print_exception.assert_called_once()

    def test_paste_file_success(self) -> None:
        """正常なファイルペーストのテスト"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("line1\nline2\nline3")
            temp_path = f.name

        try:
            with patch.object(self.manager, "_send_line") as mock_send_line:
                self.manager.paste_file(temp_path)
                # 少なくとも1回は呼ばれることを確認
                self.assertGreater(mock_send_line.call_count, 0)
        finally:
            Path(temp_path).unlink()

    @patch("chardet.detect")
    def test_detect_encoding(self, mock_detect: MagicMock) -> None:
        """エンコーディング検出のテスト"""
        mock_detect.return_value = {"encoding": "shift_jis"}

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content")
            temp_path = f.name

        try:
            encoding = self.manager._detect_encoding(Path(temp_path))
            self.assertEqual(encoding, "shift_jis")
        finally:
            Path(temp_path).unlink()

    @patch("chardet.detect")
    def test_detect_encoding_fallback(self, mock_detect: MagicMock) -> None:
        """エンコーディング検出のフォールバックテスト"""
        mock_detect.return_value = {}

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test content")
            temp_path = f.name

        try:
            encoding = self.manager._detect_encoding(Path(temp_path))
            self.assertEqual(encoding, "utf-8")
        finally:
            Path(temp_path).unlink()

    def test_send_line(self) -> None:
        """単一行送信のテスト"""
        with (
            patch.object(self.connection, "write") as mock_write,
            patch.object(self.connection, "flush") as mock_flush,
        ):

            self.manager._send_line("test line")
            mock_write.assert_called_once_with(b"test line")
            mock_flush.assert_called_once()

    def test_check_response_no_data(self) -> None:
        """レスポンスチェック（データなし）のテスト"""
        with patch.object(self.connection, "in_waiting", return_value=0):
            result = self.manager._check_response()
            self.assertFalse(result)

    def test_check_response_with_expected(self) -> None:
        """レスポンスチェック（期待値あり）のテスト"""
        with (
            patch.object(self.connection, "in_waiting", return_value=10),
            patch.object(self.connection, "read", return_value=b"some :? ` response"),
        ):

            result = self.manager._check_response(":? `")
            self.assertTrue(result)

    def test_check_response_decode_error(self) -> None:
        """レスポンスチェック（デコードエラー）のテスト"""
        with (
            patch.object(self.connection, "in_waiting", return_value=10),
            patch.object(self.connection, "read", return_value=b"\xff\xfe\x00\x00"),
        ):

            result = self.manager._check_response()
            self.assertFalse(result)

    @patch("time.sleep")
    @patch("msx_serial.transfer.file_transfer.print_info")
    @patch("msx_serial.transfer.file_transfer.send_basic_program")
    @patch("tqdm.tqdm")
    @patch("builtins.open", new_callable=mock_open, read_data=b"test")
    def test_upload_file_success(
        self,
        mock_file: MagicMock,
        mock_tqdm: MagicMock,
        mock_send_basic: MagicMock,
        mock_print_info: MagicMock,
        mock_sleep: MagicMock,
    ) -> None:
        """ファイルアップロード成功のテスト"""
        mock_send_basic.return_value = "BASIC program"
        mock_pbar = Mock()
        mock_tqdm.return_value.__enter__.return_value = mock_pbar

        with (
            patch.object(self.connection, "write") as mock_write,
            patch.object(self.connection, "flush"),
        ):

            self.manager.upload_file("test.txt")

            # writeが複数回呼ばれることを確認
            self.assertGreater(mock_write.call_count, 0)
            # 成功メッセージが表示されることを確認
            mock_print_info.assert_called_with("アップロード完了")

    @patch("time.sleep")
    @patch("msx_serial.transfer.file_transfer.print_exception")
    @patch("msx_serial.transfer.file_transfer.send_basic_program")
    def test_upload_file_error(
        self,
        mock_send_basic: MagicMock,
        mock_print_exception: MagicMock,
        mock_sleep: MagicMock,
    ) -> None:
        """ファイルアップロードエラーのテスト"""
        mock_send_basic.side_effect = Exception("BASIC error")

        with patch.object(self.connection, "write") as mock_write:
            self.manager.upload_file("test.txt")

            # エラーメッセージが表示されることを確認
            mock_print_exception.assert_called_once()
            # finallyブロックのクリーンアップが実行されることを確認
            mock_write.assert_called_with(b"\r\nNEW\r\n")

    @patch("time.sleep")
    @patch("msx_serial.transfer.file_transfer.print_info")
    @patch("msx_serial.transfer.file_transfer.send_basic_program")
    @patch("builtins.open", new_callable=mock_open, read_data=b"test")
    def test_upload_file_with_terminal(
        self,
        mock_file: MagicMock,
        mock_send_basic: MagicMock,
        mock_print_info: MagicMock,
        mock_sleep: MagicMock,
    ) -> None:
        """ターミナル設定ありのアップロードテスト"""
        mock_send_basic.return_value = "BASIC program"
        mock_terminal = Mock()
        self.manager.set_terminal(mock_terminal)

        with (
            patch("tqdm.tqdm"),
            patch.object(self.connection, "write"),
            patch.object(self.connection, "flush"),
        ):

            self.manager.upload_file("test.txt")

            # finallyブロックで出力抑制が解除されることを確認
            self.assertFalse(mock_terminal.suppress_output)


if __name__ == "__main__":
    unittest.main()
