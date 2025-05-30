import unittest
from msx_serial.terminal import MSXTerminal
from msx_serial.connection.dummy import DummyConfig, DummyConnection
from msx_serial.input.user_input import UserInputHandler
from msx_serial.transfer.file_transfer import FileTransferManager


class TestMSXTerminalWithDummy(unittest.TestCase):
    def setUp(self):
        config = DummyConfig()
        self.conn = DummyConnection(config)
        self.terminal = MSXTerminal(
            config=config,
            encoding="utf-8",
            prompt_style="#00ff00 bold"
        )
        self.user_input = UserInputHandler("#00ff00 bold", "utf-8", self.conn)
        self.file_transfer = FileTransferManager(self.conn, "utf-8")
        self.file_transfer.set_terminal(self.terminal)

        self.terminal.user_input = self.user_input
        self.terminal.file_transfer = self.file_transfer

    def test_send_and_echo(self):
        test_input = 'PRINT "HELLO"'
        self.user_input.send(test_input)
        sent_data = b"".join(self.conn.get_sent_data()).decode("utf-8")
        self.assertIn(test_input, sent_data)

    def test_exit_command(self):
        stop_event = self.terminal.stop_event
        handled = self.user_input.handle_special_commands("@exit", self.file_transfer, stop_event)
        self.assertTrue(handled)
        self.assertTrue(stop_event.is_set())


if __name__ == "__main__":
    unittest.main()
