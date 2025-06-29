import unittest
from unittest.mock import MagicMock, Mock, patch

from msx_serial.connection.dummy import DummyConfig, DummyConnection
from msx_serial.core.msx_session import MSXSession
from msx_serial.io.user_interface import UserInterface
from msx_serial.transfer.file_transfer import FileTransferManager


class TestMSXTerminalWithDummy(unittest.TestCase):
    @patch("msx_serial.completion.iot_loader.IotNodes")
    @patch("msx_serial.io.input_session.PromptSession")
    def setUp(self, mock_prompt_session: MagicMock, mock_iot_nodes: MagicMock) -> None:
        # PromptSessionのモックを設定
        mock_session = Mock()
        mock_session.prompt.return_value = "mocked input"
        mock_prompt_session.return_value = mock_session

        mock_iot_nodes.return_value.get_node_names.return_value = []
        config = DummyConfig()
        self.conn = DummyConnection(config)
        self.terminal = MSXSession(
            connection=self.conn, encoding="msx-jp", prompt_style="#00ff00 bold"
        )
        self.user_interface = UserInterface("#00ff00 bold", self.conn, "msx-jp")
        self.file_transfer = FileTransferManager(self.conn, "msx-jp")
        self.file_transfer.set_terminal(self.terminal)

        self.terminal.user_interface = self.user_interface
        self.terminal.file_transfer = self.file_transfer

    def test_send_and_echo(self) -> None:
        """送信とエコーバックのテスト"""
        self.user_interface.send("TEST")
        data = self.conn.get_sent_data()
        self.assertIn(b"TEST", data[0])

    def test_exit_command(self) -> None:
        """終了コマンドのテスト"""
        stop_event = self.terminal.stop_event
        handled = self.user_interface.handle_special_commands(
            "@exit", self.file_transfer, stop_event
        )
        self.assertTrue(handled)
        self.assertTrue(stop_event.is_set())


if __name__ == "__main__":
    unittest.main()
