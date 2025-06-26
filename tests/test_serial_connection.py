"""
Test for msx_serial/connection/serial.py
"""

import unittest
from unittest.mock import Mock, patch

from msx_serial.connection.serial import SerialConfig, SerialConnection


class TestSerialConfig(unittest.TestCase):
    """SerialConfigのテスト"""

    def test_default_config(self):
        """デフォルト設定のテスト"""
        config = SerialConfig()
        self.assertEqual(config.port, "")
        self.assertEqual(config.baudrate, 115200)
        self.assertEqual(config.bytesize, 8)
        self.assertEqual(config.parity, "N")
        self.assertEqual(config.stopbits, 1)
        self.assertIsNone(config.timeout)
        self.assertFalse(config.xonxoff)
        self.assertFalse(config.rtscts)
        self.assertFalse(config.dsrdtr)

    def test_custom_config(self):
        """カスタム設定のテスト"""
        config = SerialConfig(
            port="/dev/ttyUSB0",
            baudrate=9600,
            bytesize=7,
            parity="E",
            stopbits=2,
            timeout=1.0,
            xonxoff=True,
            rtscts=True,
            dsrdtr=True,
        )
        self.assertEqual(config.port, "/dev/ttyUSB0")
        self.assertEqual(config.baudrate, 9600)
        self.assertEqual(config.bytesize, 7)
        self.assertEqual(config.parity, "E")
        self.assertEqual(config.stopbits, 2)
        self.assertEqual(config.timeout, 1.0)
        self.assertTrue(config.xonxoff)
        self.assertTrue(config.rtscts)
        self.assertTrue(config.dsrdtr)


class TestSerialConnection(unittest.TestCase):
    """SerialConnectionのテスト"""

    def setUp(self):
        """テストセットアップ"""
        self.config = SerialConfig(port="/dev/ttyUSB0", baudrate=9600)

    @patch("msx_serial.connection.serial.serial.Serial")
    def test_init_with_config(self, mock_serial):
        """設定を使った初期化のテスト"""
        mock_serial_instance = Mock()
        mock_serial.return_value = mock_serial_instance

        connection = SerialConnection(self.config)

        mock_serial.assert_called_once_with(
            port="/dev/ttyUSB0",
            baudrate=9600,
            bytesize=8,
            parity="N",
            stopbits=1,
            timeout=None,
            xonxoff=False,
            rtscts=False,
            dsrdtr=False,
        )
        self.assertEqual(connection.connection, mock_serial_instance)

    @patch("msx_serial.connection.serial.serial.Serial")
    def test_write(self, mock_serial):
        """書き込みのテスト"""
        mock_serial_instance = Mock()
        mock_serial.return_value = mock_serial_instance

        connection = SerialConnection(self.config)
        test_data = b"test data"

        connection.write(test_data)
        mock_serial_instance.write.assert_called_once_with(test_data)

    @patch("msx_serial.connection.serial.serial.Serial")
    def test_flush(self, mock_serial):
        """フラッシュのテスト"""
        mock_serial_instance = Mock()
        mock_serial.return_value = mock_serial_instance

        connection = SerialConnection(self.config)

        connection.flush()
        mock_serial_instance.flush.assert_called_once()

    @patch("msx_serial.connection.serial.serial.Serial")
    def test_read(self, mock_serial):
        """読み込みのテスト"""
        mock_serial_instance = Mock()
        mock_serial_instance.read.return_value = b"response"
        mock_serial.return_value = mock_serial_instance

        connection = SerialConnection(self.config)
        result = connection.read(10)

        mock_serial_instance.read.assert_called_once_with(10)
        self.assertEqual(result, b"response")

    @patch("msx_serial.connection.serial.serial.Serial")
    def test_in_waiting(self, mock_serial):
        """受信待ちバイト数のテスト"""
        mock_serial_instance = Mock()
        mock_serial_instance.in_waiting = 5
        mock_serial.return_value = mock_serial_instance

        connection = SerialConnection(self.config)
        result = connection.in_waiting()

        self.assertEqual(result, 5)

    @patch("msx_serial.connection.serial.serial.Serial")
    def test_close(self, mock_serial):
        """接続終了のテスト"""
        mock_serial_instance = Mock()
        mock_serial.return_value = mock_serial_instance

        connection = SerialConnection(self.config)

        connection.close()
        mock_serial_instance.close.assert_called_once()

    @patch("msx_serial.connection.serial.serial.Serial")
    def test_is_open(self, mock_serial):
        """接続状態確認のテスト"""
        mock_serial_instance = Mock()
        mock_serial_instance.is_open = True
        mock_serial.return_value = mock_serial_instance

        connection = SerialConnection(self.config)
        result = connection.is_open()

        self.assertTrue(result)

    @patch("msx_serial.connection.serial.serial.Serial")
    def test_serial_exception_handling(self, mock_serial):
        """シリアルポート例外処理のテスト"""
        from serial import SerialException

        mock_serial.side_effect = SerialException("Port not found")
        with self.assertRaises(SerialException):
            SerialConnection(self.config)


if __name__ == "__main__":
    unittest.main()
