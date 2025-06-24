#!/usr/bin/env python3
"""
Performance commands の単体試験
"""

import unittest
from unittest.mock import Mock, patch

from msx_serial.commands.performance_commands import handle_performance_command


class TestPerformanceCommands(unittest.TestCase):
    """Performance commands の単体試験"""

    def setUp(self):
        """テストの準備"""
        self.terminal = Mock()
        self.terminal.encoding = "utf-8"
        self.terminal.protocol_detector = Mock()
        self.terminal.protocol_detector.debug_mode = False
        self.terminal.toggle_debug_mode = Mock()

    @patch("msx_serial.commands.performance_commands.print_info")
    def test_handle_performance_command_no_subcommand(self, mock_print_info):
        """サブコマンドなしの@perfコマンドテスト"""
        result = handle_performance_command(self.terminal, "@perf")

        self.assertTrue(result)
        # ヘルプメッセージが表示されることを確認
        mock_print_info.assert_any_call("Performance Commands:")
        mock_print_info.assert_any_call(
            "  @perf stats         - Show performance statistics"
        )

    @patch("msx_serial.commands.performance_commands.print_info")
    def test_handle_performance_command_stats(self, mock_print_info):
        """@perf statsコマンドテスト"""
        result = handle_performance_command(self.terminal, "@perf stats")

        self.assertTrue(result)
        mock_print_info.assert_any_call("=== Performance Statistics ===")
        mock_print_info.assert_any_call("Mode: Optimized (instant processing)")
        mock_print_info.assert_any_call("Encoding: utf-8")
        mock_print_info.assert_any_call("Debug Mode: No")

    @patch("msx_serial.commands.performance_commands.print_info")
    def test_handle_performance_command_stats_debug_on(self, mock_print_info):
        """デバッグモードがONの場合の@perf statsコマンドテスト"""
        self.terminal.protocol_detector.debug_mode = True

        result = handle_performance_command(self.terminal, "@perf stats")

        self.assertTrue(result)
        mock_print_info.assert_any_call("Debug Mode: Yes")

    @patch("msx_serial.commands.performance_commands.print_info")
    def test_handle_performance_command_debug_toggle(self, mock_print_info):
        """@perf debug toggleコマンドテスト"""
        result = handle_performance_command(self.terminal, "@perf debug toggle")

        self.assertTrue(result)
        self.terminal.toggle_debug_mode.assert_called_once()

    @patch("msx_serial.commands.performance_commands.print_info")
    def test_handle_performance_command_debug_on_when_off(self, mock_print_info):
        """デバッグモードがOFFの時の@perf debug onコマンドテスト"""
        self.terminal.protocol_detector.debug_mode = False

        result = handle_performance_command(self.terminal, "@perf debug on")

        self.assertTrue(result)
        self.terminal.toggle_debug_mode.assert_called_once()

    @patch("msx_serial.commands.performance_commands.print_info")
    def test_handle_performance_command_debug_on_when_already_on(self, mock_print_info):
        """デバッグモードが既にONの時の@perf debug onコマンドテスト"""
        self.terminal.protocol_detector.debug_mode = True

        result = handle_performance_command(self.terminal, "@perf debug on")

        self.assertTrue(result)
        self.terminal.toggle_debug_mode.assert_not_called()
        mock_print_info.assert_any_call("Debug mode is already enabled")

    @patch("msx_serial.commands.performance_commands.print_info")
    def test_handle_performance_command_debug_off_when_on(self, mock_print_info):
        """デバッグモードがONの時の@perf debug offコマンドテスト"""
        self.terminal.protocol_detector.debug_mode = True

        result = handle_performance_command(self.terminal, "@perf debug off")

        self.assertTrue(result)
        self.terminal.toggle_debug_mode.assert_called_once()

    @patch("msx_serial.commands.performance_commands.print_info")
    def test_handle_performance_command_debug_off_when_already_off(
        self, mock_print_info
    ):
        """デバッグモードが既にOFFの時の@perf debug offコマンドテスト"""
        self.terminal.protocol_detector.debug_mode = False

        result = handle_performance_command(self.terminal, "@perf debug off")

        self.assertTrue(result)
        self.terminal.toggle_debug_mode.assert_not_called()
        mock_print_info.assert_any_call("Debug mode is already disabled")

    @patch("msx_serial.commands.performance_commands.print_error")
    def test_handle_performance_command_debug_invalid_mode(self, mock_print_error):
        """@perf debug 無効なモードコマンドテスト"""
        result = handle_performance_command(self.terminal, "@perf debug invalid")

        self.assertTrue(result)
        mock_print_error.assert_called_once_with(
            "Invalid debug mode. Use: on, off, or toggle"
        )

    @patch("msx_serial.commands.performance_commands.print_error")
    def test_handle_performance_command_debug_no_toggle_method(self, mock_print_error):
        """toggle_debug_modeメソッドがない場合のテスト"""
        del self.terminal.toggle_debug_mode

        result = handle_performance_command(self.terminal, "@perf debug toggle")

        self.assertTrue(result)
        mock_print_error.assert_called_once_with(
            "Debug mode not available in this terminal version"
        )

    @patch("msx_serial.commands.performance_commands.print_info")
    def test_handle_performance_command_help(self, mock_print_info):
        """@perf helpコマンドテスト"""
        result = handle_performance_command(self.terminal, "@perf help")

        self.assertTrue(result)
        mock_print_info.assert_any_call("Performance Commands:")

    @patch("msx_serial.commands.performance_commands.print_error")
    @patch("msx_serial.commands.performance_commands.print_info")
    def test_handle_performance_command_unknown(
        self, mock_print_info, mock_print_error
    ):
        """未知のサブコマンドテスト"""
        result = handle_performance_command(self.terminal, "@perf unknown")

        self.assertTrue(result)
        mock_print_error.assert_called_once_with("Unknown performance command: unknown")
        # ヘルプも表示される
        mock_print_info.assert_any_call("Performance Commands:")

    @patch("msx_serial.commands.performance_commands.print_info")
    def test_handle_performance_command_debug_default_toggle(self, mock_print_info):
        """@perf debugコマンド（引数なし、デフォルトでtoggle）テスト"""
        result = handle_performance_command(self.terminal, "@perf debug")

        self.assertTrue(result)
        self.terminal.toggle_debug_mode.assert_called_once()

    def test_terminal_without_encoding(self):
        """encodingプロパティがないターミナルでのstatsテスト"""
        self.terminal = Mock()
        del self.terminal.encoding  # encodingプロパティを削除
        self.terminal.protocol_detector = Mock()
        self.terminal.protocol_detector.debug_mode = False

        with patch(
            "msx_serial.commands.performance_commands.print_info"
        ) as mock_print_info:
            result = handle_performance_command(self.terminal, "@perf stats")

            self.assertTrue(result)
            mock_print_info.assert_any_call("Encoding: Unknown")


if __name__ == "__main__":
    unittest.main()
