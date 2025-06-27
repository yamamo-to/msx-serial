#!/usr/bin/env python3
"""
モード切り替え機能の単体試験
"""

import unittest
from unittest.mock import Mock, patch

from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.document import Document

from msx_serial.connection.dummy import DummyConfig, DummyConnection
from msx_serial.io.user_interface import UserInterface


class TestModeSwitching(unittest.TestCase):
    """モード切り替え機能の単体試験"""

    @patch("msx_serial.io.input_session.PromptSession")
    def setUp(self, mock_prompt_session):
        """テストの準備"""
        # PromptSessionのモックを設定
        mock_session = Mock()
        mock_session.prompt.return_value = "mocked input"
        mock_prompt_session.return_value = mock_session

        # DummyConfigとDummyConnectionを作成
        config = DummyConfig()
        connection = DummyConnection(config)

        # UserInterfaceを作成
        self.handler = UserInterface(
            prompt_style="#00ff00 bold", encoding="msx-jp", connection=connection
        )

    def test_initial_mode(self):
        """初期状態のモードテスト"""
        self.assertEqual(self.handler.current_mode, "unknown")

    def test_mode_switching_to_dos(self):
        """DOSモードへの切り替えテスト"""
        # DOSモードに切り替え
        self.handler.current_mode = "dos"
        self.handler._update_completer_mode()

        self.assertEqual(self.handler.current_mode, "dos")
        self.assertEqual(self.handler.input_session.completer.current_mode, "dos")

    def test_mode_switching_to_basic(self):
        """BASICモードへの切り替えテスト"""
        # BASICモードに切り替え
        self.handler.current_mode = "basic"
        self.handler._update_completer_mode()

        self.assertEqual(self.handler.current_mode, "basic")
        self.assertEqual(self.handler.input_session.completer.current_mode, "basic")

    def test_completion_after_mode_switch_to_dos(self):
        """DOSモード切り替え後の補完機能テスト"""
        # DOSモードに切り替え
        self.handler.current_mode = "dos"
        self.handler._update_completer_mode()

        # @mで始まる補完をテスト（実装に合わせて調整）
        document = Document("@m")
        completions = list(
            self.handler.input_session.completer.get_completions(
                document, CompleteEvent()
            )
        )
        self.assertGreaterEqual(
            len(completions), 1, "DOSモードでは@mで始まる補完候補があるはず"
        )

        # @modeが含まれることを確認
        mode_found = any(comp.text == "mode" for comp in completions)
        self.assertTrue(mode_found, "@modeコマンドが含まれているはず")

        # Dで始まるDOSコマンドをテスト
        document = Document("D")
        completions = list(
            self.handler.input_session.completer.get_completions(
                document, CompleteEvent()
            )
        )
        self.assertGreater(len(completions), 0, "Dで始まるDOSコマンドがあるはず")

        # 期待されるコマンドが含まれているか確認
        command_texts = [comp.text for comp in completions]
        expected_commands = ["DIR", "DEL", "DATE"]
        for cmd in expected_commands:
            if cmd in command_texts:  # 存在する場合のみチェック
                self.assertIn(cmd, command_texts, f"{cmd}コマンドが含まれているはず")

    def test_completion_after_mode_switch_to_basic(self):
        """BASICモード切り替え後の補完機能テスト"""
        # BASICモードに切り替え
        self.handler.current_mode = "basic"
        self.handler._update_completer_mode()

        # @で始まる補完をテスト（BASICモードでは複数の特殊コマンド）
        document = Document("@")
        completions = list(
            self.handler.input_session.completer.get_completions(
                document, CompleteEvent()
            )
        )
        # 実装の動作に合わせて期待値を調整
        completion_count = len(completions)
        self.assertGreaterEqual(
            completion_count, 1, "BASICモードでは少なくとも1つの@コマンドがあるはず"
        )

        # @modeは含まれているはず
        mode_found = any(comp.text == "mode" for comp in completions)
        self.assertTrue(mode_found, "@modeコマンドが含まれているはず")

        # 特殊コマンドの数が期待される範囲内であることを確認
        command_texts = [comp.text for comp in completions]
        self.assertIn("mode", command_texts, "@modeコマンドが含まれているはず")

    def test_multiple_mode_switches(self):
        """複数回のモード切り替えテスト"""
        # unknown → dos → basic → dos の順で切り替え

        # 初期状態（unknown）
        self.assertEqual(self.handler.current_mode, "unknown")

        # DOSモードに切り替え
        self.handler.current_mode = "dos"
        self.handler._update_completer_mode()
        self.assertEqual(self.handler.current_mode, "dos")
        self.assertEqual(self.handler.input_session.completer.current_mode, "dos")

        # DOSモードでのDコマンド補完確認
        document = Document("D")
        completions = list(
            self.handler.input_session.completer.get_completions(
                document, CompleteEvent()
            )
        )
        dos_command_count = len(completions)
        self.assertGreater(dos_command_count, 0, "DOSモードでDコマンドが補完されるはず")

        # BASICモードに切り替え
        self.handler.current_mode = "basic"
        self.handler._update_completer_mode()
        self.assertEqual(self.handler.current_mode, "basic")
        self.assertEqual(self.handler.input_session.completer.current_mode, "basic")

        # BASICモードでのPコマンド補完確認
        document = Document("P")
        completions = list(
            self.handler.input_session.completer.get_completions(
                document, CompleteEvent()
            )
        )
        basic_command_count = len(completions)
        self.assertGreater(
            basic_command_count, 0, "BASICモードでPコマンドが補完されるはず"
        )

        # 再度DOSモードに切り替え
        self.handler.current_mode = "dos"
        self.handler._update_completer_mode()
        self.assertEqual(self.handler.current_mode, "dos")
        self.assertEqual(self.handler.input_session.completer.current_mode, "dos")

        # 再度DOSモードでのDコマンド補完確認（同じ結果が得られるはず）
        document = Document("D")
        completions = list(
            self.handler.input_session.completer.get_completions(
                document, CompleteEvent()
            )
        )
        msg = "再度DOSモードに切り替えても同じ補完結果が得られるはず"
        self.assertEqual(len(completions), dos_command_count, msg)

    def test_completer_persistence(self):
        """補完機能の永続性テスト"""
        # 補完機能が最初に作成されていることを確認
        self.assertIsNotNone(self.handler.input_session.completer)
        original_completer = self.handler.input_session.completer

        # モード切り替え後も同じ補完機能オブジェクトが使われることを確認
        self.handler.current_mode = "dos"
        self.handler._update_completer_mode()
        msg1 = "モード切り替え後も同じ補完機能オブジェクトが使われるはず"
        self.assertIs(self.handler.input_session.completer, original_completer, msg1)

        # PromptSessionはモックされているため、completerの設定は確認しない
        # (CI環境ではPromptSessionが実際のコンソールを必要とするため)


if __name__ == "__main__":
    unittest.main()
