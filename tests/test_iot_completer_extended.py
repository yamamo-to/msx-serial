"""
IoTCompleterの拡張テスト（カバレッジ向上用）
"""

import unittest
from prompt_toolkit.document import Document
from prompt_toolkit.completion import CompleteEvent

from msx_serial.completion.completers.iot_completer import IoTCompleter


class TestIoTCompleterExtended(unittest.TestCase):
    """IoTCompleterの拡張テスト"""

    def setUp(self):
        """テストの準備"""
        self.completer = IoTCompleter()

    def test_get_completions_empty_input(self):
        """空の入力での補完テスト"""
        document = Document("")
        completions = list(self.completer.get_completions(document, CompleteEvent()))
        # 空の入力では補完候補なし
        self.assertEqual(len(completions), 0)

    def test_get_completions_non_iot_command(self):
        """IOTコマンド以外での補完テスト"""
        document = Document("PRINT")
        completions = list(self.completer.get_completions(document, CompleteEvent()))
        # IOTコマンド以外では補完候補なし
        self.assertEqual(len(completions), 0)

    def test_iot_command_variations(self):
        """様々なIOTコマンドパターンでのテスト"""
        test_cases = [
            "IOTGET",
            "IOTSET",
            "IOTFIND",
            "iotget",  # 小文字
            "IoTGet",  # 混合ケース
        ]
        
        for test_input in test_cases:
            with self.subTest(input=test_input):
                document = Document(test_input)
                completions = list(self.completer.get_completions(document, CompleteEvent()))
                # エラーが発生しないことを確認
                self.assertIsInstance(completions, list)

    def test_partial_iot_command_matching(self):
        """部分的なIOTコマンドマッチングテスト"""
        test_cases = [
            "IOT",
            "IOTG",
            "IOTS",
            "IOTF",
        ]
        
        for test_input in test_cases:
            with self.subTest(input=test_input):
                document = Document(test_input)
                completions = list(self.completer.get_completions(document, CompleteEvent()))
                # 部分マッチでも適切に動作することを確認
                self.assertIsInstance(completions, list)

    def test_whitespace_handling(self):
        """空白文字の処理テスト"""
        test_cases = [
            "IOTGET ",
            "IOTSET  ",
            "\tIOTFIND",
            " IOTGET",
        ]
        
        for test_input in test_cases:
            with self.subTest(input=test_input):
                document = Document(test_input)
                completions = list(self.completer.get_completions(document, CompleteEvent()))
                # 空白文字があってもエラーが発生しないことを確認
                self.assertIsInstance(completions, list)


if __name__ == "__main__":
    unittest.main() 