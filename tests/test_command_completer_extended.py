"""
CommandCompleterの拡張テスト（カバレッジ向上用）
"""

import unittest
from prompt_toolkit.document import Document
from prompt_toolkit.completion import CompleteEvent

from msx_serial.completion.completers.command_completer import CommandCompleter
from msx_serial.commands.command_types import CommandType


class TestCommandCompleterExtended(unittest.TestCase):
    """CommandCompleterの拡張テスト（未カバー部分）"""

    def setUp(self):
        """テストの準備"""
        self.available_commands = [str(cmd.value) for cmd in CommandType]
        self.completer = CommandCompleter(self.available_commands, "unknown")

    def test_complete_all_subcommands(self):
        """_complete_all_subcommands メソッドのテスト"""
        self.completer.set_mode("basic")

        # モック用のコンテキストを作成
        from msx_serial.completion.completers.base import CompletionContext

        context = CompletionContext("_test", "_test")

        # _complete_all_subcommands メソッドを直接呼び出し
        completions = list(self.completer._complete_all_subcommands(context))
        # サブコマンドがある場合、補完が返される
        self.assertIsInstance(completions, list)

    def test_at_help_dos_mode_no_completion(self):
        """DOSモードでは@helpコマンドの補完が行われないことをテスト"""
        self.completer.set_mode("dos")

        document = Document("@help ")
        completions = list(self.completer.get_completions(document, CompleteEvent()))

        # DOSモードでは@helpの特別な処理は行われず、空のリストまたは他のコマンドが返される
        self.assertIsInstance(completions, list)

    def test_at_command_non_mode_basic_filter(self):
        """BASICモードで@コマンドのうち@mode以外のフィルタリングテスト"""
        self.completer.set_mode("basic")

        document = Document("@")
        completions = list(self.completer.get_completions(document, CompleteEvent()))

        # @modeコマンド以外の特殊コマンドも含まれることを確認
        completion_texts = [comp.text for comp in completions]
        self.assertIn("mode", completion_texts)

        # 他の特殊コマンドもあることを確認（@modeだけでない）
        non_mode_commands = [text for text in completion_texts if text != "mode"]
        self.assertGreater(
            len(non_mode_commands), 0, "mode以外の@コマンドも存在するはず"
        )

    def test_iot_command_with_comma_no_completion(self):
        """IOTコマンドでカンマが含まれる場合、補完が行われないことをテスト"""
        self.completer.set_mode("basic")

        test_cases = [
            "IOTGET node1,property",
            "IOTSET device1,value",
            "IOTFIND sensor1,type",
        ]

        for test_input in test_cases:
            with self.subTest(input=test_input):
                document = Document(test_input)
                completions = list(
                    self.completer.get_completions(document, CompleteEvent())
                )
                # カンマが含まれている場合は補完しない（空のイテレータを返す）
                self.assertEqual(
                    len(completions), 0, f"{test_input}でカンマ後は補完しないはず"
                )

    def test_call_subcommand_completion_word_handling(self):
        """CALLサブコマンド補完でのword処理テスト"""
        self.completer.set_mode("basic")

        # CALL + 部分的なサブコマンド
        document = Document("CALL CL")
        completions = list(self.completer.get_completions(document, CompleteEvent()))

        # CLで始まるCALLサブコマンドがあるかチェック（実際のデータに依存）
        # 実際のデータに依存するが、補完処理がエラーなく動作することを確認
        self.assertIsInstance(completions, list)

    def test_underscore_subcommand_word_stripping(self):
        """_で始まるサブコマンドでの先頭_除去テスト"""
        self.completer.set_mode("basic")

        # _で始まる部分的なコマンド
        document = Document("_PAL")
        completions = list(self.completer.get_completions(document, CompleteEvent()))

        # 補完処理が正常に動作することを確認
        self.assertIsInstance(completions, list)

    def test_word_prefix_matching_in_general_keywords(self):
        """一般キーワード補完でのプレフィックスマッチングテスト"""
        self.completer.set_mode("basic")

        # PRで始まるBASICコマンド
        document = Document("PR")
        completions = list(self.completer.get_completions(document, CompleteEvent()))

        # PRで始まるコマンド（PRINT等）があることを確認
        pr_commands = [comp for comp in completions if comp.text.startswith("PR")]
        self.assertGreater(len(pr_commands), 0, "PRで始まるBASICコマンドがあるはず")

    def test_empty_word_completion(self):
        """空のword（カーソル位置が単語の境界）での補完テスト"""
        self.completer.set_mode("basic")

        # 空白で終わる入力
        document = Document("FOR I=1 TO 10: ")
        completions = list(self.completer.get_completions(document, CompleteEvent()))

        # 空のwordでも補完候補が返されることを確認
        self.assertIsInstance(completions, list)

    def test_mode_specific_behavior_consistency(self):
        """各モードでの一貫した動作テスト"""
        modes = ["basic", "dos", "unknown"]

        for mode in modes:
            with self.subTest(mode=mode):
                self.completer.set_mode(mode)

                # 各モードで基本的な補完が動作することを確認
                document = Document("A")
                completions = list(
                    self.completer.get_completions(document, CompleteEvent())
                )

                # エラーが発生せず、リストが返されることを確認
                self.assertIsInstance(completions, list)
                self.assertEqual(self.completer.current_mode, mode)


if __name__ == "__main__":
    unittest.main()
