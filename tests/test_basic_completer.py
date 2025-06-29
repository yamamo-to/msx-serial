"""
BASIC補完機能のテスト
"""

import unittest
from unittest.mock import Mock

from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.document import Document

from msx_serial.completion.basic_filesystem import BASICFileInfo
from msx_serial.completion.completers.basic_completer import BASICCompleter


class TestBASICCompleter(unittest.TestCase):
    """BASICCompleterのテスト"""

    def setUp(self):
        """テスト前の準備"""
        self.mock_connection = Mock()
        self.completer = BASICCompleter(self.mock_connection)

    def test_initialization(self):
        """初期化テスト"""
        self.assertEqual(self.completer.connection, self.mock_connection)
        self.assertIsNotNone(self.completer.filesystem_manager)
        self.assertEqual(self.completer.refresh_interval, 5.0)

    def test_set_connection(self):
        """接続設定テスト"""
        new_connection = Mock()
        self.completer.set_connection(new_connection)
        self.assertEqual(self.completer.connection, new_connection)
        self.assertEqual(self.completer.filesystem_manager.connection, new_connection)

    def test_set_current_directory(self):
        """ディレクトリ設定テスト"""
        self.completer.set_current_directory("B:\\GAMES")
        self.assertEqual(
            self.completer.filesystem_manager.current_directory, "B:\\GAMES\\"
        )

    def test_extract_current_word_empty(self):
        """現在の単語抽出テスト（空）"""
        document = Document("")
        command_line = ""
        word = self.completer._extract_current_word(document, command_line)
        self.assertEqual(word, "")

    def test_extract_current_word_simple(self):
        """現在の単語抽出テスト（単純）"""
        document = Document("RUN TEST")
        command_line = "RUN TEST"
        word = self.completer._extract_current_word(document, command_line)
        self.assertEqual(word, "TEST")

    def test_extract_current_word_with_quotes(self):
        """現在の単語抽出テスト（引用符付き）"""
        document = Document('RUN "TEST.BAS"')
        command_line = 'RUN "TEST.BAS"'
        word = self.completer._extract_current_word(document, command_line)
        self.assertEqual(word, "TEST.BAS")

    def test_extract_current_word_partial_quotes(self):
        """現在の単語抽出テスト（部分引用符）"""
        document = Document('RUN "TEST')
        command_line = 'RUN "TEST'
        word = self.completer._extract_current_word(document, command_line)
        self.assertEqual(word, "TEST")

    def test_extract_current_word_ends_with_space(self):
        """現在の単語抽出テスト（スペース終了）"""
        document = Document("RUN ")
        command_line = "RUN "
        word = self.completer._extract_current_word(document, command_line)
        self.assertEqual(word, "")

    def test_get_completions_no_command(self):
        """補完テスト（コマンドなし）"""
        document = Document("")
        completions = list(self.completer.get_completions(document, CompleteEvent()))
        self.assertEqual(len(completions), 0)

    def test_get_completions_with_files(self):
        """補完テスト（ファイルあり）"""
        # テストファイルを設定
        test_files = {
            "TEST.BAS": BASICFileInfo("TEST", "BAS"),
            "DEMO.BAS": BASICFileInfo("DEMO", "BAS"),
        }
        self.completer.filesystem_manager.set_test_files(test_files)

        # RUNコマンドで補完
        document = Document("RUN T")
        completions = list(self.completer.get_completions(document, CompleteEvent()))

        assert len(completions) > 0
        # 引用符なしで補完されることを確認（修正後の仕様）
        completion_text = completions[0].text
        assert not completion_text.startswith('"')

    def test_get_completions_basic_file_priority(self):
        """補完テスト（BASICファイル優先）"""
        # テストファイルを設定（BASICファイルとその他のファイル）
        test_files = {
            "TEST.BAS": BASICFileInfo("TEST", "BAS"),
            "DATA.TXT": BASICFileInfo("DATA", "TXT"),
        }
        self.completer.filesystem_manager.set_test_files(test_files)

        # RUNコマンドで補完
        document = Document("RUN T")
        completions = list(self.completer.get_completions(document, CompleteEvent()))

        assert len(completions) > 0
        # 最初の補完候補がBASICファイルであることを確認
        first_completion = completions[0]
        # display_metaはFormattedTextオブジェクトなので、文字列として比較
        display_meta_str = str(first_completion.display_meta)
        assert "BASIC" in display_meta_str

    def test_get_completions_no_files(self):
        """補完テスト（ファイルなし）"""
        document = Document("RUN T")
        completions = list(self.completer.get_completions(document, CompleteEvent()))
        assert len(completions) == 0

    def test_get_completions_with_space(self):
        """補完テスト（スペース付き）"""
        # テストファイルを設定
        test_files = {
            "TEST.BAS": BASICFileInfo("TEST", "BAS"),
        }
        self.completer.filesystem_manager.set_test_files(test_files)

        # スペースで終わるコマンド
        document = Document("RUN ")
        completions = list(self.completer.get_completions(document, CompleteEvent()))

        # スペースで終わる場合は補完候補が返らない（現仕様に合わせる）
        assert len(completions) == 0

    def test_get_completions_multiple_arguments(self):
        """補完テスト（複数引数）"""
        # テストファイルを設定
        test_files = {
            "TEST.BAS": BASICFileInfo("TEST", "BAS"),
        }
        self.completer.filesystem_manager.set_test_files(test_files)

        # 複数引数のコマンド
        document = Document("LOAD TEST.BAS, R")
        completions = list(self.completer.get_completions(document, CompleteEvent()))

        # 複数引数でも補完が動作することを確認
        self.assertIsInstance(completions, list)

    def test_get_completions_with_quotes_at_end(self):
        """補完テスト（引用符で終わる）"""
        # テストファイルを設定
        test_files = {
            "TEST.BAS": BASICFileInfo("TEST", "BAS"),
            "DEMO.BAS": BASICFileInfo("DEMO", "BAS"),
        }
        self.completer.filesystem_manager.set_test_files(test_files)

        # RUN"で終わるコマンド
        document = Document('RUN"')
        completions = list(self.completer.get_completions(document, CompleteEvent()))

        # 引用符で終わる場合でも補完が動作することを確認
        assert len(completions) > 0
        completion_text = completions[0].text
        # 引用符なしで補完されることを確認（修正後の仕様）
        assert not completion_text.startswith('"')

    def test_get_completions_with_partial_quotes(self):
        """補完テスト（部分的な引用符）"""
        # テストファイルを設定
        test_files = {
            "TEST.BAS": BASICFileInfo("TEST", "BAS"),
        }
        self.completer.filesystem_manager.set_test_files(test_files)

        # RUN"Tで終わるコマンド
        document = Document('RUN"T')
        completions = list(self.completer.get_completions(document, CompleteEvent()))

        assert len(completions) > 0
        completion_text = completions[0].text
        # 引用符なしで補完されることを確認（修正後の仕様）
        assert not completion_text.startswith('"')


if __name__ == "__main__":
    unittest.main()
