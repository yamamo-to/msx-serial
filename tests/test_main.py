import unittest
from unittest.mock import MagicMock, Mock, patch

from msx_serial.__main__ import main


class TestMain(unittest.TestCase):
    """メインエントリーポイントのテスト"""

    @patch("msx_serial.__main__.MSXSession")
    @patch("msx_serial.__main__.ConnectionManager")
    @patch("msx_serial.__main__.detect_connection_type")
    @patch("sys.argv", ["msx-serial", "COM4"])
    def test_main_basic_usage(
        self,
        mock_detect: MagicMock,
        mock_manager_class: MagicMock,
        mock_session_class: MagicMock,
    ) -> None:
        """基本的な使用方法のテスト"""
        # detect_connection_typeのモック
        mock_config = Mock()
        mock_detect.return_value = mock_config

        # ConnectionManagerのモック
        mock_connection = Mock()
        mock_manager = Mock()
        mock_manager.connection = mock_connection
        mock_manager_class.return_value = mock_manager

        # MSXSessionのモック
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        main()

        # 正しい引数で呼ばれることを確認
        mock_detect.assert_called_once_with("COM4")
        mock_manager_class.assert_called_once_with(mock_config)
        mock_session_class.assert_called_once_with(
            connection=mock_connection,
            encoding="msx-jp",
        )
        mock_session.run.assert_called_once()
        # デバッグモードは呼ばれない
        mock_session.toggle_debug_mode.assert_not_called()

    @patch("msx_serial.__main__.MSXSession")
    @patch("msx_serial.__main__.ConnectionManager")
    @patch("msx_serial.__main__.detect_connection_type")
    @patch("sys.argv", ["msx-serial", "192.168.1.100:2223", "--encoding", "utf-8"])
    def test_main_with_encoding(
        self,
        mock_detect: MagicMock,
        mock_manager_class: MagicMock,
        mock_session_class: MagicMock,
    ) -> None:
        """エンコーディング指定のテスト"""
        mock_config = Mock()
        mock_detect.return_value = mock_config
        mock_connection = Mock()
        mock_manager = Mock()
        mock_manager.connection = mock_connection
        mock_manager_class.return_value = mock_manager
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        main()

        mock_detect.assert_called_once_with("192.168.1.100:2223")
        mock_session_class.assert_called_once_with(
            connection=mock_connection,
            encoding="utf-8",
        )

    @patch("msx_serial.__main__.MSXSession")
    @patch("msx_serial.__main__.ConnectionManager")
    @patch("msx_serial.__main__.detect_connection_type")
    @patch("sys.argv", ["msx-serial", "dummy://", "--debug"])
    def test_main_with_debug(
        self,
        mock_detect: MagicMock,
        mock_manager_class: MagicMock,
        mock_session_class: MagicMock,
    ) -> None:
        """デバッグモード有効化のテスト"""
        mock_config = Mock()
        mock_detect.return_value = mock_config
        mock_connection = Mock()
        mock_manager = Mock()
        mock_manager.connection = mock_connection
        mock_manager_class.return_value = mock_manager
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        main()

        mock_detect.assert_called_once_with("dummy://")
        mock_session_class.assert_called_once_with(
            connection=mock_connection,
            encoding="msx-jp",
        )
        mock_session.toggle_debug_mode.assert_called_once()
        mock_session.run.assert_called_once()

    @patch("msx_serial.__main__.MSXSession")
    @patch("msx_serial.__main__.ConnectionManager")
    @patch("msx_serial.__main__.detect_connection_type")
    @patch("sys.argv", ["msx-serial", "/dev/ttyUSB0", "--encoding", "ascii", "--debug"])
    def test_main_all_options(
        self,
        mock_detect: MagicMock,
        mock_manager_class: MagicMock,
        mock_session_class: MagicMock,
    ) -> None:
        """全オプション指定のテスト"""
        mock_config = Mock()
        mock_detect.return_value = mock_config
        mock_connection = Mock()
        mock_manager = Mock()
        mock_manager.connection = mock_connection
        mock_manager_class.return_value = mock_manager
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        main()

        mock_detect.assert_called_once_with("/dev/ttyUSB0")
        mock_session_class.assert_called_once_with(
            connection=mock_connection,
            encoding="ascii",
        )
        mock_session.toggle_debug_mode.assert_called_once()
        mock_session.run.assert_called_once()

    @patch("msx_serial.__main__.detect_connection_type")
    @patch("sys.argv", ["msx-serial", "invalid://connection"])
    @patch("builtins.print")
    def test_main_connection_error(
        self, mock_print: MagicMock, mock_detect: MagicMock
    ) -> None:
        """接続エラーのテスト"""
        mock_detect.side_effect = ValueError("Invalid connection")

        with self.assertRaises(SystemExit) as cm:
            main()

        self.assertEqual(cm.exception.code, 1)
        mock_print.assert_called_with("Error: Invalid connection")

    @patch("msx_serial.__main__.MSXSession")
    @patch("msx_serial.__main__.ConnectionManager")
    @patch("msx_serial.__main__.detect_connection_type")
    @patch("sys.argv", ["msx-serial", "COM4"])
    @patch("builtins.print")
    def test_main_session_error(
        self,
        mock_print: MagicMock,
        mock_detect: MagicMock,
        mock_manager_class: MagicMock,
        mock_session_class: MagicMock,
    ) -> None:
        """セッションエラーのテスト"""
        mock_config = Mock()
        mock_detect.return_value = mock_config
        mock_connection = Mock()
        mock_manager = Mock()
        mock_manager.connection = mock_connection
        mock_manager_class.return_value = mock_manager
        mock_session_class.side_effect = RuntimeError("Session failed")

        with self.assertRaises(SystemExit) as cm:
            main()

        self.assertEqual(cm.exception.code, 1)
        mock_print.assert_called_with("Error: Session failed")

    @patch("msx_serial.__main__.MSXSession")
    @patch("msx_serial.__main__.ConnectionManager")
    @patch("msx_serial.__main__.detect_connection_type")
    @patch("sys.argv", ["msx-serial", "COM4"])
    @patch("builtins.print")
    def test_main_keyboard_interrupt(
        self,
        mock_print: MagicMock,
        mock_detect: MagicMock,
        mock_manager_class: MagicMock,
        mock_session_class: MagicMock,
    ) -> None:
        """KeyboardInterrupt処理のテスト"""
        mock_config = Mock()
        mock_detect.return_value = mock_config
        mock_connection = Mock()
        mock_manager = Mock()
        mock_manager.connection = mock_connection
        mock_manager_class.return_value = mock_manager
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_session.run.side_effect = KeyboardInterrupt()

        with self.assertRaises(SystemExit) as cm:
            main()

        self.assertEqual(cm.exception.code, 0)
        mock_print.assert_called_with("\nExiting...")

    @patch("msx_serial.__main__.MSXSession")
    @patch("msx_serial.__main__.ConnectionManager")
    @patch("msx_serial.__main__.detect_connection_type")
    @patch("sys.argv", ["msx-serial", "COM4"])
    @patch("builtins.print")
    def test_main_run_keyboard_interrupt(
        self,
        mock_print: MagicMock,
        mock_detect: MagicMock,
        mock_manager_class: MagicMock,
        mock_session_class: MagicMock,
    ) -> None:
        """実行中のKeyboardInterrupt処理テスト"""
        mock_config = Mock()
        mock_detect.return_value = mock_config
        mock_connection = Mock()
        mock_manager = Mock()
        mock_manager.connection = mock_connection
        mock_manager_class.return_value = mock_manager
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        # terminal.run()でKeyboardInterruptが発生
        mock_session.run.side_effect = KeyboardInterrupt()

        with self.assertRaises(SystemExit) as cm:
            main()

        self.assertEqual(cm.exception.code, 0)
        mock_print.assert_called_with("\nExiting...")

    @patch("sys.argv", ["msx-serial"])
    def test_main_missing_connection_argument(self) -> None:
        """必須引数不足のテスト"""
        with self.assertRaises(SystemExit):
            main()

    @patch("sys.argv", ["msx-serial", "--help"])
    def test_main_help_argument(self) -> None:
        """ヘルプ引数のテスト"""
        with self.assertRaises(SystemExit):
            main()


if __name__ == "__main__":
    unittest.main()
