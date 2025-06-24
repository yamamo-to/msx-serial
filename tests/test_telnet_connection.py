import unittest
import socket
from unittest.mock import patch, MagicMock, Mock
from msx_serial.connection.telnet import TelnetConnection, TelnetConfig


class TestTelnetConfig(unittest.TestCase):
    """TelnetConfigのテスト"""

    def test_default_values(self) -> None:
        """デフォルト値のテスト"""
        config = TelnetConfig()
        self.assertEqual(config.port, 23)
        self.assertEqual(config.host, "localhost")

    def test_custom_values(self) -> None:
        """カスタム値のテスト"""
        config = TelnetConfig(host="192.168.1.100", port=2223)
        self.assertEqual(config.host, "192.168.1.100")
        self.assertEqual(config.port, 2223)


class TestTelnetConnection(unittest.TestCase):
    """TelnetConnectionのテスト"""

    @patch("socket.socket")
    def test_init_success(self, mock_socket_class: MagicMock) -> None:
        """正常な初期化のテスト"""
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket

        config = TelnetConfig(host="example.com", port=2223)
        connection = TelnetConnection(config)

        # ソケット作成と設定の確認
        mock_socket_class.assert_called_once_with(socket.AF_INET, socket.SOCK_STREAM)
        mock_socket.setsockopt.assert_any_call(
            socket.IPPROTO_TCP, socket.TCP_NODELAY, 1
        )
        mock_socket.setsockopt.assert_any_call(
            socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1
        )
        mock_socket.connect.assert_called_once_with(("example.com", 2223))
        mock_socket.setblocking.assert_called_once_with(False)

        # 初期状態の確認
        self.assertEqual(connection.host, "example.com")
        self.assertEqual(connection.port, 2223)
        self.assertTrue(connection._connected)
        self.assertEqual(len(connection._buffer), 0)

    @patch("socket.socket")
    def test_write_success(self, mock_socket_class: MagicMock) -> None:
        """正常な書き込みのテスト"""
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket

        config = TelnetConfig()
        connection = TelnetConnection(config)

        test_data = b"hello world"
        connection.write(test_data)

        mock_socket.sendall.assert_called_once_with(test_data)

    @patch("socket.socket")
    @patch("msx_serial.connection.telnet.print_exception")
    def test_write_error(
        self, mock_print_exception: MagicMock, mock_socket_class: MagicMock
    ) -> None:
        """書き込みエラーのテスト"""
        mock_socket = Mock()
        mock_socket.sendall.side_effect = socket.error("Connection lost")
        mock_socket_class.return_value = mock_socket

        config = TelnetConfig()
        connection = TelnetConnection(config)

        connection.write(b"test")

        mock_print_exception.assert_called_once()
        self.assertFalse(connection._connected)

    @patch("socket.socket")
    def test_flush(self, mock_socket_class: MagicMock) -> None:
        """flushメソッドのテスト（何もしない）"""
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket

        config = TelnetConfig()
        connection = TelnetConnection(config)

        # 例外が発生しないことを確認
        connection.flush()

    @patch("socket.socket")
    @patch("select.select")
    def test_read_from_buffer(
        self, mock_select: MagicMock, mock_socket_class: MagicMock
    ) -> None:
        """バッファからの読み込みテスト"""
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        mock_select.return_value = ([], [], [])  # データなし

        config = TelnetConfig()
        connection = TelnetConnection(config)

        # バッファにデータを設定
        connection._buffer = bytearray(b"hello world")

        data = connection.read(5)
        self.assertEqual(data, b"hello")
        self.assertEqual(connection._buffer, bytearray(b" world"))

    @patch("socket.socket")
    @patch("select.select")
    def test_read_fill_buffer(
        self, mock_select: MagicMock, mock_socket_class: MagicMock
    ) -> None:
        """バッファ補充を伴う読み込みテスト"""
        mock_socket = Mock()
        mock_socket.recv.return_value = b"new data"
        mock_socket_class.return_value = mock_socket
        mock_select.return_value = ([mock_socket], [], [])  # データあり

        config = TelnetConfig()
        connection = TelnetConnection(config)

        data = connection.read(8)
        self.assertEqual(data, b"new data")
        mock_socket.recv.assert_called_with(4096)

    @patch("socket.socket")
    @patch("msx_serial.connection.telnet.print_exception")
    def test_read_error(
        self, mock_print_exception: MagicMock, mock_socket_class: MagicMock
    ) -> None:
        """読み込みエラーのテスト"""
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket

        config = TelnetConfig()
        connection = TelnetConnection(config)

        # _fill_buffer_if_neededでエラーを直接発生させる
        with patch.object(
            connection, "_fill_buffer_if_needed", side_effect=Exception("Buffer error")
        ):
            data = connection.read(10)
            self.assertEqual(data, b"")
            mock_print_exception.assert_called_once()

    @patch("socket.socket")
    @patch("select.select")
    def test_fill_buffer_if_needed_sufficient_data(
        self, mock_select: MagicMock, mock_socket_class: MagicMock
    ) -> None:
        """十分なデータがある場合のバッファ補充テスト"""
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket

        config = TelnetConfig()
        connection = TelnetConnection(config)
        connection._buffer = bytearray(b"sufficient data")

        connection._fill_buffer_if_needed(5)

        # selectが呼ばれないことを確認
        mock_select.assert_not_called()

    @patch("socket.socket")
    @patch("select.select")
    def test_fill_buffer_if_needed_connection_closed(
        self, mock_select: MagicMock, mock_socket_class: MagicMock
    ) -> None:
        """接続が閉じられた場合のバッファ補充テスト"""
        mock_socket = Mock()
        mock_socket.recv.return_value = b""  # 空のデータ = 接続終了
        mock_socket_class.return_value = mock_socket
        mock_select.return_value = ([mock_socket], [], [])

        config = TelnetConfig()
        connection = TelnetConnection(config)

        connection._fill_buffer_if_needed(10)

        self.assertFalse(connection._connected)

    @patch("socket.socket")
    @patch("select.select")
    def test_fill_buffer_if_needed_socket_error(
        self, mock_select: MagicMock, mock_socket_class: MagicMock
    ) -> None:
        """ソケットエラーの場合のバッファ補充テスト"""
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        mock_select.return_value = ([mock_socket], [], [])
        mock_socket.recv.side_effect = socket.error("Network error")

        config = TelnetConfig()
        connection = TelnetConnection(config)

        # 例外が伝播しないことを確認
        connection._fill_buffer_if_needed(10)

    @patch("socket.socket")
    @patch("select.select")
    def test_in_waiting_with_data(
        self, mock_select: MagicMock, mock_socket_class: MagicMock
    ) -> None:
        """データが利用可能な場合のin_waitingテスト"""
        mock_socket = Mock()
        mock_socket.recv.return_value = b"waiting data"
        mock_socket_class.return_value = mock_socket
        mock_select.return_value = ([mock_socket], [], [])

        config = TelnetConfig()
        connection = TelnetConnection(config)

        result = connection.in_waiting()
        self.assertEqual(result, 12)  # "waiting data"の長さ
        self.assertEqual(connection._buffer, bytearray(b"waiting data"))

    @patch("socket.socket")
    @patch("select.select")
    def test_in_waiting_no_data(
        self, mock_select: MagicMock, mock_socket_class: MagicMock
    ) -> None:
        """データが利用不可能な場合のin_waitingテスト"""
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        mock_select.return_value = ([], [], [])  # データなし

        config = TelnetConfig()
        connection = TelnetConnection(config)

        result = connection.in_waiting()
        self.assertEqual(result, 0)

    @patch("socket.socket")
    @patch("select.select")
    def test_in_waiting_connection_closed(
        self, mock_select: MagicMock, mock_socket_class: MagicMock
    ) -> None:
        """接続が閉じられた場合のin_waitingテスト"""
        mock_socket = Mock()
        mock_socket.recv.return_value = b""  # 空 = 接続終了
        mock_socket_class.return_value = mock_socket
        mock_select.return_value = ([mock_socket], [], [])

        config = TelnetConfig()
        connection = TelnetConnection(config)

        result = connection.in_waiting()
        self.assertEqual(result, 0)
        self.assertFalse(connection._connected)

    @patch("socket.socket")
    @patch("select.select")
    def test_in_waiting_exception(
        self, mock_select: MagicMock, mock_socket_class: MagicMock
    ) -> None:
        """例外発生時のin_waitingテスト"""
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket
        mock_select.side_effect = Exception("Select error")

        config = TelnetConfig()
        connection = TelnetConnection(config)
        connection._buffer = bytearray(b"existing")

        result = connection.in_waiting()
        self.assertEqual(result, 8)  # 既存バッファの長さ

    @patch("socket.socket")
    def test_close(self, mock_socket_class: MagicMock) -> None:
        """接続終了のテスト"""
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket

        config = TelnetConfig()
        connection = TelnetConnection(config)

        connection.close()

        mock_socket.close.assert_called_once()
        self.assertFalse(connection._connected)

    @patch("socket.socket")
    def test_close_with_error(self, mock_socket_class: MagicMock) -> None:
        """接続終了時のエラー処理テスト"""
        mock_socket = Mock()
        mock_socket.close.side_effect = Exception("Close error")
        mock_socket_class.return_value = mock_socket

        config = TelnetConfig()
        connection = TelnetConnection(config)

        # 例外が伝播しないことを確認
        connection.close()
        self.assertFalse(connection._connected)

    @patch("socket.socket")
    def test_is_open_true(self, mock_socket_class: MagicMock) -> None:
        """接続開状態のテスト"""
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket

        config = TelnetConfig()
        connection = TelnetConnection(config)

        self.assertTrue(connection.is_open())

    @patch("socket.socket")
    def test_is_open_false(self, mock_socket_class: MagicMock) -> None:
        """接続閉状態のテスト"""
        mock_socket = Mock()
        mock_socket_class.return_value = mock_socket

        config = TelnetConfig()
        connection = TelnetConnection(config)
        connection._connected = False

        self.assertFalse(connection.is_open())


if __name__ == "__main__":
    unittest.main()
