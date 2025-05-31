"""補完機能のテスト"""

import unittest
from prompt_toolkit.document import Document
from prompt_toolkit.completion import CompleteEvent
from msx_serial.completion.completers.command_completer import CommandCompleter


class TestCommandCompleter(unittest.TestCase):
    """CommandCompleterのテスト"""

    def setUp(self) -> None:
        """テストの前準備"""
        self.completer = CommandCompleter(special_commands=["help", "cd", "encode"])

    def test_call_subcommand_completion(self) -> None:
        """CALLコマンドのサブコマンド補完テスト"""
        # CALL + スペースの後の補完
        document = Document("CALL ")
        completions = list(self.completer.get_completions(document, CompleteEvent()))

        # CALLのサブコマンドのみが補完候補として返されることを確認
        call_keywords = [
            cmd[0] for cmd in self.completer.msx_keywords["CALL"]["keywords"]
        ]
        for completion in completions:
            self.assertIn(completion.text, call_keywords)

    def test_underscore_completion(self) -> None:
        """アンダースコアで始まる場合の全サブコマンド補完テスト"""
        # _で始まる場合の補完
        document = Document("_")
        completions = list(self.completer.get_completions(document, CompleteEvent()))

        # 全サブコマンドが補完候補として返されることを確認
        all_subcommands = []
        for cmd in self.completer.sub_commands:
            all_subcommands.extend(
                [cmd[0] for cmd in self.completer.msx_keywords[cmd]["keywords"]]
            )

        for completion in completions:
            self.assertIn(completion.text, all_subcommands)

    def test_underscore_matches_call_completion(self) -> None:
        """アンダースコアで始まる場合の補完がCALLと同じであることを確認"""
        # _で始まる場合の補完
        underscore_doc = Document("_")
        underscore_completions = list(
            self.completer.get_completions(underscore_doc, CompleteEvent())
        )

        # CALL + スペースの後の補完
        call_doc = Document("CALL ")
        call_completions = list(
            self.completer.get_completions(call_doc, CompleteEvent())
        )

        # 補完候補のテキストを比較
        underscore_texts = {c.text for c in underscore_completions}
        call_texts = {c.text for c in call_completions}

        self.assertEqual(underscore_texts, call_texts)

    def test_iotget_completion(self) -> None:
        """IOTGETコマンドの補完テスト"""
        # CALL IOTGET("の後の補完
        document = Document('CALL IOTGET("')
        completions = list(self.completer.get_completions(document, CompleteEvent()))

        # IOTノードの補完候補が返されることを確認
        iot_nodes = self.completer.device_list
        for completion in completions:
            self.assertIn(completion.text, iot_nodes)

    def test_basic_keyword_completion(self) -> None:
        """BASICキーワードの補完テスト"""
        # 通常のBASICキーワード補完
        document = Document("PR")
        completions = list(self.completer.get_completions(document, CompleteEvent()))

        # BASICキーワードのみが補完候補として返されることを確認
        basic_keywords = [
            cmd[0] for cmd in self.completer.msx_keywords["BASIC"]["keywords"]
        ]
        for completion in completions:
            self.assertIn(completion.text, basic_keywords)

    def test_help_command_completion(self) -> None:
        """@helpコマンドの補完テスト"""
        # @helpの補完
        document = Document("@help")
        completions = list(self.completer.get_completions(document, CompleteEvent()))

        # @helpの補完候補が返されることを確認
        self.assertTrue(len(completions) > 0)

    def test_special_command_completion(self) -> None:
        """特殊コマンドの補完テスト"""
        # @で始まる特殊コマンドの補完
        document = Document("@")
        completions = list(self.completer.get_completions(document, CompleteEvent()))

        # 特殊コマンドが補完候補として返されることを確認
        special_commands = ["help", "cd", "encode", "exit", "paste", "upload"]
        for completion in completions:
            self.assertIn(completion.text, special_commands)


if __name__ == "__main__":
    unittest.main()
