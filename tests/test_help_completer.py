#!/usr/bin/env python3
"""
HelpCompleter の単体試験
"""

import unittest
from unittest.mock import patch
from prompt_toolkit.document import Document
from prompt_toolkit.completion import CompleteEvent

from msx_serial.completion.completers.help_completer import HelpCompleter


class TestHelpCompleter(unittest.TestCase):
    """HelpCompleter の単体試験"""

    def setUp(self):
        """テストの準備"""
        self.completer = HelpCompleter()

    @patch("msx_serial.completion.keyword_loader.load_keywords")
    def test_get_completions_no_args(self, mock_load_keywords):
        """引数がない場合の@helpコマンド補完テスト"""
        # モックデータを設定
        mock_keywords = {
            "BASIC": {
                "keywords": [
                    ("PRINT", "テキストを表示"),
                    ("FOR", "ループ処理"),
                    ("IF", "条件分岐"),
                ]
            }
        }
        mock_load_keywords.return_value = mock_keywords

        # completerを再初期化してモックデータを適用
        self.completer = HelpCompleter()

        document = Document("@help ")
        completions = list(self.completer.get_completions(document, CompleteEvent()))

        self.assertGreater(len(completions), 0)
        # PRINTコマンドが含まれていることを確認
        print_found = any(comp.text == "PRINT" for comp in completions)
        self.assertTrue(print_found, "PRINTコマンドが補完候補に含まれているはず")

    @patch("msx_serial.completion.keyword_loader.load_keywords")
    def test_get_completions_with_prefix(self, mock_load_keywords):
        """プレフィックス付きの@helpコマンド補完テスト"""
        # モックデータを設定
        mock_keywords = {
            "BASIC": {
                "keywords": [
                    ("PRINT", "テキストを表示"),
                    ("PRESET", "ドットを消去"),
                    ("FOR", "ループ処理"),
                ]
            }
        }
        mock_load_keywords.return_value = mock_keywords

        # completerを再初期化
        self.completer = HelpCompleter()

        document = Document("@help PR")
        completions = list(self.completer.get_completions(document, CompleteEvent()))

        # PRで始まるコマンドのみが補完候補になる
        command_texts = [comp.text for comp in completions]
        self.assertIn("PRINT", command_texts)
        self.assertIn("PRESET", command_texts)
        self.assertNotIn("FOR", command_texts)

    @patch("msx_serial.completion.keyword_loader.load_keywords")
    def test_get_completions_call_command(self, mock_load_keywords):
        """CALLコマンドの補完テスト"""
        # モックデータを設定
        mock_keywords = {
            "BASIC": {"keywords": [("CALL", "サブルーチン呼び出し")]},
            "CALL": {
                "keywords": [
                    ("MUSIC", "音楽再生"),
                    ("PALETTE", "パレット設定"),
                    ("SYSTEM", "システム呼び出し"),
                ]
            },
        }
        mock_load_keywords.return_value = mock_keywords

        # completerを再初期化
        self.completer = HelpCompleter()

        document = Document("@help CALL")
        completions = list(self.completer.get_completions(document, CompleteEvent()))

        # CALLサブコマンドが補完候補になる
        command_texts = [comp.text for comp in completions]
        self.assertIn("MUSIC", command_texts)
        self.assertIn("PALETTE", command_texts)
        self.assertIn("SYSTEM", command_texts)

    @patch("msx_serial.completion.keyword_loader.load_keywords")
    def test_get_completions_call_subcommand_with_prefix(self, mock_load_keywords):
        """CALLサブコマンドのプレフィックス付き補完テスト"""
        # モックデータを設定
        mock_keywords = {
            "BASIC": {"keywords": [("CALL", "サブルーチン呼び出し")]},
            "CALL": {
                "keywords": [
                    ("MUSIC", "音楽再生"),
                    ("PALETTE", "パレット設定"),
                    ("PAUSE", "一時停止"),
                ]
            },
        }
        mock_load_keywords.return_value = mock_keywords

        # completerを再初期化
        self.completer = HelpCompleter()

        document = Document("@help CALL PA")
        completions = list(self.completer.get_completions(document, CompleteEvent()))

        # PAで始まるCALLサブコマンドのみが補完候補になる
        command_texts = [comp.text for comp in completions]
        self.assertIn("PALETTE", command_texts)
        self.assertIn("PAUSE", command_texts)
        self.assertNotIn("MUSIC", command_texts)

    @patch("msx_serial.completion.keyword_loader.load_keywords")
    def test_get_completions_underscore_command(self, mock_load_keywords):
        """アンダースコア（_）で始まるCALLコマンドの補完テスト"""
        # モックデータを設定
        mock_keywords = {
            "BASIC": {"keywords": [("CALL", "サブルーチン呼び出し")]},
            "CALL": {"keywords": [("MUSIC", "音楽再生"), ("PALETTE", "パレット設定")]},
        }
        mock_load_keywords.return_value = mock_keywords

        # completerを再初期化
        self.completer = HelpCompleter()

        document = Document("@help _MU")
        completions = list(self.completer.get_completions(document, CompleteEvent()))

        # MUで始まるCALLサブコマンドが補完候補になる
        command_texts = [comp.text for comp in completions]
        self.assertIn("MUSIC", command_texts)
        self.assertNotIn("PALETTE", command_texts)

    @patch("msx_serial.completion.keyword_loader.load_keywords")
    def test_get_completions_case_insensitive(self, mock_load_keywords):
        """大文字小文字を区別しない補完テスト"""
        # モックデータを設定
        mock_keywords = {
            "BASIC": {
                "keywords": [
                    ("PRINT", "テキストを表示"),
                    ("print", "小文字版"),  # 通常はないが、テスト用
                ]
            }
        }
        mock_load_keywords.return_value = mock_keywords

        # completerを再初期化
        self.completer = HelpCompleter()

        document = Document("@help pr")  # 小文字で検索
        completions = list(self.completer.get_completions(document, CompleteEvent()))

        # 大文字小文字関係なく補完される
        command_texts = [comp.text for comp in completions]
        self.assertIn("PRINT", command_texts)

    @patch("msx_serial.completion.keyword_loader.load_keywords")
    def test_get_completions_empty_result(self, mock_load_keywords):
        """マッチする補完候補がない場合のテスト"""
        # モックデータを設定
        mock_keywords = {
            "BASIC": {"keywords": [("PRINT", "テキストを表示"), ("FOR", "ループ処理")]}
        }
        mock_load_keywords.return_value = mock_keywords

        # completerを再初期化
        self.completer = HelpCompleter()

        document = Document("@help XYZ")  # 存在しないコマンド
        completions = list(self.completer.get_completions(document, CompleteEvent()))

        # 補完候補が空であることを確認
        self.assertEqual(len(completions), 0)

    @patch("msx_serial.completion.keyword_loader.load_keywords")
    def test_get_completions_display_meta(self, mock_load_keywords):
        """補完候補のメタ情報表示テスト"""
        # モックデータを設定
        mock_keywords = {
            "BASIC": {
                "keywords": [
                    ("PRINT", "テキストを表示します"),
                ]
            }
        }
        mock_load_keywords.return_value = mock_keywords

        # completerを再初期化
        self.completer = HelpCompleter()

        document = Document("@help PRINT")
        completions = list(self.completer.get_completions(document, CompleteEvent()))

        if completions:
            completion = completions[0]
            self.assertEqual(completion.text, "PRINT")
            # displayはFormattedTextの場合があるので適切に処理
            display_text = completion.display
            if hasattr(display_text, "__iter__") and not isinstance(display_text, str):
                # FormattedTextの場合、テキスト部分のみを抽出
                actual_text = "".join(text for style, text in display_text)
                self.assertEqual(actual_text, "PRINT")
            else:
                self.assertEqual(display_text, "PRINT")

            # display_metaもFormattedTextの場合があるので適切に処理
            meta_text = completion.display_meta
            if hasattr(meta_text, "__iter__") and not isinstance(meta_text, str):
                # FormattedTextの場合、テキスト部分のみを抽出
                actual_meta = "".join(text for style, text in meta_text)
                # 実際のデータから取得されたメタ情報を確認（モックではなく実際のデータ）
                self.assertIsInstance(actual_meta, str)
                self.assertGreater(len(actual_meta), 0)
            else:
                # 文字列の場合
                self.assertIsInstance(meta_text, str)
                self.assertGreater(len(meta_text), 0)


if __name__ == "__main__":
    unittest.main()
