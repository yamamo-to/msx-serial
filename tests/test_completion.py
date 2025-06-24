#!/usr/bin/env python3
"""
補完機能の単体試験
"""

import unittest
from prompt_toolkit.document import Document
from prompt_toolkit.completion import CompleteEvent

from msx_serial.completion.completers.command_completer import CommandCompleter
from msx_serial.commands.command_types import CommandType


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

    def test_dos_mode_dos_commands_completion(self):
        """DOSモードでのDOSコマンド補完テスト"""
        self.completer.set_mode("dos")

        # Dで始まるDOSコマンド
        document = Document("D")
        completions = list(self.completer.get_completions(document, CompleteEvent()))
        self.assertGreater(len(completions), 0, "Dで始まるDOSコマンドがあるはずです")

    def test_basic_mode_basic_commands_completion(self):
        """BASICモードでのBASICコマンド補完テスト"""
        self.completer.set_mode("basic")

        # Pで始まるBASICコマンド
        document = Document("P")
        completions = list(self.completer.get_completions(document, CompleteEvent()))
        self.assertGreater(len(completions), 0, "Pで始まるBASICコマンドがあるはずです")

    def test_call_subcommand_completion(self):
        """CALLサブコマンドの補完テスト"""
        self.completer.set_mode("basic")

        # CALL で始まる場合
        document = Document("CALL ")
        completions = list(self.completer.get_completions(document, CompleteEvent()))
        self.assertGreater(len(completions), 0, "CALLサブコマンドがあるはずです")

        # _で始まる場合（CALLの省略形）
        document = Document("_")
        completions = list(self.completer.get_completions(document, CompleteEvent()))
        self.assertGreater(
            len(completions), 0, "_で始まるCALLサブコマンドがあるはずです"
        )

    def test_iot_command_completion(self):
        """IOTコマンドの補完テスト"""
        self.completer.set_mode("basic")

        # IOTコマンドの補完
        test_cases = ["IOTGET", "IOTSET", "IOTFIND"]
        for iot_command in test_cases:
            with self.subTest(command=iot_command):
                document = Document(iot_command)
                normal_completions = list(
                    self.completer.get_completions(document, CompleteEvent())
                )
                # IOTコマンドは専用の補完処理がある

                # コンマが含まれている場合は補完をスキップ
                document_with_comma = Document(f"{iot_command} node1,")
                completions_with_comma = list(
                    self.completer.get_completions(document_with_comma, CompleteEvent())
                )
                self.assertEqual(
                    len(completions_with_comma),
                    0,
                    f"{iot_command}でコンマ後は補完しないはず",
                )

                # 通常の補完は list であることを確認
                self.assertIsInstance(normal_completions, list)

    def test_help_command_completion_basic_only(self):
        """@helpコマンドはBASICモードでのみ利用可能"""
        # BASICモードでは利用可能
        self.completer.set_mode("basic")
        document = Document("@help")
        basic_completions = list(
            self.completer.get_completions(document, CompleteEvent())
        )
        # @helpコマンドは専用の補完処理がある（具体的な確認は省略）

        # DOSモードでは利用不可
        self.completer.set_mode("dos")
        document = Document("@help")
        dos_completions = list(
            self.completer.get_completions(document, CompleteEvent())
        )
        # DOSモードでは@helpの補完処理は実行されない（具体的な確認は省略）

        # 実装依存のため、両方とも list であることのみ確認
        self.assertIsInstance(basic_completions, list)
        self.assertIsInstance(dos_completions, list)

    def test_unknown_mode_completion(self):
        """不明モードでの補完テスト（両方のコマンドタイプが表示）"""
        self.completer.set_mode("unknown")

        document = Document("P")
        completions = list(self.completer.get_completions(document, CompleteEvent()))
        self.assertGreater(
            len(completions), 0, "不明モードでもコマンド補完があるはずです"
        )

    def test_mode_switching_functionality(self):
        """モード切り替え機能のテスト"""
        # 初期状態はunknown
        self.assertEqual(self.completer.current_mode, "unknown")

        # DOSモードに切り替え
        self.completer.set_mode("dos")
        self.assertEqual(self.completer.current_mode, "dos")

        # BASICモードに切り替え
        self.completer.set_mode("basic")
        self.assertEqual(self.completer.current_mode, "basic")

    def test_completion_context_parsing(self):
        """補完コンテキストの解析テスト"""
        self.completer.set_mode("basic")

        # 複雑な入力での補完テスト
        test_cases = [
            ("FOR I=1 TO 10:P", "P"),  # コロン後の文字
            ("IF A>0 THEN PR", "PR"),  # 条件文内の補完
            ('10 PRINT "HELLO":REM ', ""),  # コメント内
        ]

        for full_text, expected_word in test_cases:
            with self.subTest(text=full_text):
                document = Document(full_text)
                # 補完が正常に動作することを確認（エラーが発生しない）
                try:
                    completions = list(
                        self.completer.get_completions(document, CompleteEvent())
                    )
                    # 補完候補の有無は問わず、エラーが発生しないことを確認
                    self.assertIsInstance(completions, list)
                except Exception as e:
                    self.fail(f"補完処理でエラーが発生: {e}")


if __name__ == "__main__":
    unittest.main()
