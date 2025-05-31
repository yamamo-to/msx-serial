import unittest
from unittest.mock import patch, MagicMock
from msx_serial.terminal import MSXTerminal
from msx_serial.connection.dummy import DummyConfig, DummyConnection
from msx_serial.input.user_input import UserInputHandler
from msx_serial.transfer.file_transfer import FileTransferManager


class TestMSXTerminalWithDummy(unittest.TestCase):
    @patch("msx_serial.util.loader_iot_nodes.IotNodes")
    def setUp(self, mock_iot_nodes: MagicMock) -> None:
        mock_iot_nodes.return_value.get_node_names.return_value = []
        config = DummyConfig()
        self.conn = DummyConnection(config)
        self.terminal = MSXTerminal(
            config=config, encoding="msx-jp", prompt_style="#00ff00 bold"
        )
        self.user_input = UserInputHandler("#00ff00 bold", "msx-jp", self.conn)
        self.file_transfer = FileTransferManager(self.conn, "msx-jp")
        self.file_transfer.set_terminal(self.terminal)

        self.terminal.user_input = self.user_input
        self.terminal.file_transfer = self.file_transfer

    def test_send_and_echo(self) -> None:
        """送信とエコーバックのテスト"""
        self.user_input.send("TEST")
        data = self.conn.get_sent_data()
        self.assertIn(b"TEST", data[0])

    def test_exit_command(self) -> None:
        """終了コマンドのテスト"""
        stop_event = self.terminal.stop_event
        handled = self.user_input.handle_special_commands(
            "@exit", self.file_transfer, stop_event
        )
        self.assertTrue(handled)
        self.assertTrue(stop_event.is_set())


if __name__ == "__main__":
    unittest.main()
