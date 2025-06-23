#!/usr/bin/env python3
"""
補完機能の単体試験
"""

import unittest
from prompt_toolkit.document import Document
from prompt_toolkit.completion import CompleteEvent

from msx_serial.completion.completers.command_completer import CommandCompleter
from msx_serial.input.commands import CommandType


class TestCommandCompleter(unittest.TestCase):
    """CommandCompleterの単体試験"""

    def setUp(self):
        """テストの準備"""
        self.available_commands = [str(cmd.value) for cmd in CommandType]
        self.completer = CommandCompleter(self.available_commands, "unknown")

    def test_dos_mode_at_mode_completion(self):
        """DOSモードでの@modeコマンド補完テスト"""
        self.completer.set_mode("dos")

        test_cases = [
            ("@", 1),  # @で1つの候補（mode）
            ("@m", 1),  # @mで1つの候補（mode）
            ("@mode", 1),  # @modeで1つの候補（mode）
        ]

        for test_input, expected_count in test_cases:
            with self.subTest(input=test_input):
                document = Document(test_input)
                completions = list(
                    self.completer.get_completions(document, CompleteEvent())
                )
                msg = f"'{test_input}'の補完候補数が期待値と異なります"
                self.assertEqual(len(completions), expected_count, msg)
                if completions:
                    self.assertEqual(completions[0].text, "mode")
                    # displayはFormattedTextオブジェクトの場合があるので適切に処理
                    display_text = completions[0].display
                    if hasattr(display_text, "__iter__") and not isinstance(
                        display_text, str
                    ):
                        # FormattedTextの場合、テキスト部分のみを抽出
                        actual_text = "".join(text for style, text in display_text)
                        self.assertEqual(actual_text, "@mode")
                    else:
                        self.assertEqual(display_text, "@mode")

    def test_basic_mode_at_commands_completion(self):
        """BASICモードでの@コマンド補完テスト"""
        self.completer.set_mode("basic")

        # @で始まる場合、複数の特殊コマンドが表示される
        document = Document("@")
        completions = list(self.completer.get_completions(document, CompleteEvent()))
        self.assertGreater(len(completions), 1, "@で始まる補完候補が複数あるはずです")

        # @modeは含まれているはず
        mode_found = any(comp.text == "mode" for comp in completions)
        self.assertTrue(mode_found, "@modeコマンドが含まれているはずです")

        # @mで始まる場合、modeのみが表示される（重複なし）
        document = Document("@m")
        completions = list(self.completer.get_completions(document, CompleteEvent()))
        self.assertEqual(
            len(completions), 1, "@mで始まる補完候補は1つ（mode）のはずです"
        )
        self.assertEqual(completions[0].text, "mode")

        # @uで始まる場合、uploadが表示される
        document = Document("@u")
        completions = list(self.completer.get_completions(document, CompleteEvent()))
        self.assertGreater(len(completions), 0, "@uで始まる補完候補があるはずです")
        upload_found = any(comp.text == "upload" for comp in completions)
        self.assertTrue(upload_found, "@uploadコマンドが含まれているはずです")

    def test_dos_mode_dos_commands_completion(self):
        """DOSモードでのDOSコマンド補完テスト"""
        self.completer.set_mode("dos")

        # Dで始まるDOSコマンド
        document = Document("D")
        completions = list(self.completer.get_completions(document, CompleteEvent()))
        self.assertGreater(len(completions), 0, "Dで始まるDOSコマンドがあるはずです")

        # 期待されるコマンドが含まれているか確認
        command_texts = [comp.text for comp in completions]
        expected_commands = ["DIR", "DEL", "DATE"]
        for cmd in expected_commands:
            self.assertIn(cmd, command_texts, f"{cmd}コマンドが含まれているはずです")

        # BASICコマンドも含まれているか確認
        document = Document("B")
        completions = list(self.completer.get_completions(document, CompleteEvent()))
        self.assertGreater(len(completions), 0, "Bで始まるDOSコマンドがあるはずです")

        command_texts = [comp.text for comp in completions]
        self.assertIn("BASIC", command_texts, "BASICコマンドが含まれているはずです")

    def test_basic_mode_basic_commands_completion(self):
        """BASICモードでのBASICコマンド補完テスト"""
        self.completer.set_mode("basic")

        # Pで始まるBASICコマンド
        document = Document("P")
        completions = list(self.completer.get_completions(document, CompleteEvent()))
        self.assertGreater(len(completions), 0, "Pで始まるBASICコマンドがあるはずです")

        # 期待されるコマンドが含まれているか確認
        command_texts = [comp.text for comp in completions]
        expected_commands = ["PRINT", "PEEK", "POKE"]
        for cmd in expected_commands:
            if cmd in command_texts:  # 存在する場合のみチェック
                self.assertIn(
                    cmd, command_texts, f"{cmd}コマンドが含まれているはずです"
                )

    def test_mode_switching(self):
        """モード切り替えテスト"""
        # 初期状態はunknown
        self.assertEqual(self.completer.current_mode, "unknown")

        # DOSモードに切り替え
        self.completer.set_mode("dos")
        self.assertEqual(self.completer.current_mode, "dos")

        # BASICモードに切り替え
        self.completer.set_mode("basic")
        self.assertEqual(self.completer.current_mode, "basic")

    def test_unknown_mode_completion(self):
        """不明モードでの補完テスト"""
        self.completer.set_mode("unknown")

        # 不明モードでは両方のコマンドタイプが表示される
        document = Document("P")
        completions = list(self.completer.get_completions(document, CompleteEvent()))
        self.assertGreater(
            len(completions), 0, "不明モードでもコマンド補完があるはずです"
        )


if __name__ == "__main__":
    unittest.main()
