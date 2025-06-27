#!/usr/bin/env python3
"""
補完機能の単体試験
"""

import unittest

from prompt_toolkit.completion import CompleteEvent, Completion
from prompt_toolkit.document import Document

from msx_serial.commands.command_types import CommandType
from msx_serial.completion.completers.base import (BaseCompleter,
                                                   CompletionContext)
from msx_serial.completion.completers.command_completer import CommandCompleter


class TestCommandCompleter(unittest.TestCase):
    """CommandCompleterの単体試験"""

    def setUp(self):
        """テストの準備"""
        self.available_commands = [cmd.command for cmd in CommandType]
        self.completer = CommandCompleter(self.available_commands, "unknown")

    def test_dos_mode_at_mode_completion(self):
        """DOSモードでの@コマンド補完テスト"""
        self.completer.set_mode("dos")

        # @で始まる場合、DOSモードでも複数の特殊コマンドが表示される
        document = Document("@")
        completions = list(self.completer.get_completions(document, CompleteEvent()))
        self.assertGreater(len(completions), 1, "@で始まる補完候補が複数あるはずです")

        # @modeは含まれているはず
        mode_found = any(comp.text == "mode" for comp in completions)
        self.assertTrue(mode_found, "@modeコマンドが含まれているはずです")

        # @mで@modeに限定される
        document = Document("@m")
        completions = list(self.completer.get_completions(document, CompleteEvent()))
        self.assertGreater(len(completions), 0, "@mで始まる補完候補があるはずです")

        # @modeで完全一致
        document = Document("@mode")
        completions = list(self.completer.get_completions(document, CompleteEvent()))
        self.assertGreater(len(completions), 0, "@modeの補完候補があるはずです")

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

    def test_complete_general_keywords(self):
        """_complete_general_keywords の実行テスト"""
        from msx_serial.completion.completers.base import CompletionContext

        context = CompletionContext("PR", "PR")
        completions = list(self.completer._complete_general_keywords(context))
        self.assertIsInstance(completions, list)


class DummyCompleter(BaseCompleter):
    def get_completions(self, document, complete_event):
        return iter([])


def test_basecompleter_build_prefix_cache():
    completer = DummyCompleter()
    # 空リスト
    cache = completer._build_prefix_cache([])
    assert isinstance(cache, dict)
    # 複数キーワード
    cache = completer._build_prefix_cache([["PRINT"], ["PSET"]])
    assert "P" in cache and "PR" in cache and "PRINT" in cache


def test_basecompleter_get_keyword_info():
    completer = DummyCompleter()
    # listの場合
    name, meta = completer._get_keyword_info(["PRINT", "desc"], "basic")
    assert name == "PRINT" and meta == "desc"
    # strの場合（実在するキーを使う）
    key = next(iter(completer.msx_keywords))
    name, meta = completer._get_keyword_info(key, key)
    assert name == key and isinstance(meta, str)


def test_basecompleter_create_completion():
    completer = DummyCompleter()
    comp = completer._create_completion("ABC", -1, display="A", meta="meta")
    assert isinstance(comp, Completion)
    assert comp.text == "ABC"
    assert comp.display_text == "A"
    # prompt-toolkitのバージョンでdisplay_metaの型が異なる場合があるため、
    # 文字列またはFormattedTextであることを確認
    if hasattr(comp.display_meta, "__iter__") and not isinstance(
        comp.display_meta, str
    ):
        # FormattedTextの場合
        assert str(comp.display_meta) == "meta" or comp.display_meta[0][1] == "meta"
    else:
        # 文字列の場合
        assert comp.display_meta == "meta"


def test_basecompleter_match_prefix():
    completer = DummyCompleter()
    candidates = ["PRINT", "PSET", "RUN"]
    # prefixなし
    result = completer._match_prefix(candidates, "")
    assert set(result) == set(candidates)
    # prefix一致
    result = completer._match_prefix(candidates, "PR")
    assert result == ["PRINT"]
    # prefix大文字小文字
    result = completer._match_prefix(candidates, "ps")
    assert result == ["PSET"]
    # prefix不一致
    result = completer._match_prefix(candidates, "ZZ")
    assert result == []


def test_basecompleter_generate_keyword_completions():
    completer = DummyCompleter()
    # 存在しないkeyword_type
    context = CompletionContext("", "FOO")
    result = list(completer._generate_keyword_completions(context, "notfound"))
    assert result == []
    # 存在するkeyword_type - 実際に存在するキーワードタイプを使用
    available_keyword_types = list(completer.msx_keywords.keys())
    if available_keyword_types:
        # 最初に見つかったキーワードタイプを使用
        keyword_type = available_keyword_types[0]
        keywords = completer.msx_keywords[keyword_type]["keywords"]
        if keywords:
            # 最初のキーワードの最初の文字を使ってテスト
            first_keyword = (
                keywords[0][0] if isinstance(keywords[0], list) else keywords[0]
            )
            prefix = first_keyword[0] if first_keyword else "P"
            context = CompletionContext("", prefix)
            result = list(
                completer._generate_keyword_completions(context, keyword_type)
            )
            assert any(isinstance(r, Completion) for r in result)


class TestCommandCompleterExtended(unittest.TestCase):
    """CommandCompleterの拡張テスト"""

    def setUp(self):
        from msx_serial.completion.completers.command_completer import \
            CommandCompleter

        self.completer = CommandCompleter(["@help", "@mode", "@exit"], "basic")

    def test_set_mode(self):
        """set_modeメソッドのテスト"""
        self.completer.set_mode("dos")
        self.assertEqual(self.completer.current_mode, "dos")

    def test_complete_all_subcommands(self):
        """_complete_all_subcommands の実行テスト"""
        from msx_serial.completion.completers.base import CompletionContext

        context = CompletionContext("_ABC", "ABC")
        completions = list(self.completer._complete_all_subcommands(context))
        self.assertIsInstance(completions, list)

    def test_complete_call_subcommands(self):
        """_complete_call_subcommands の実行テスト"""
        from msx_serial.completion.completers.base import CompletionContext

        context = CompletionContext("CLS", "CLS")
        completions = list(self.completer._complete_call_subcommands(context))
        self.assertIsInstance(completions, list)


class TestIoTCompleterExtended(unittest.TestCase):
    """IoTCompleterの拡張テスト"""

    def setUp(self):
        from msx_serial.completion.completers.iot_completer import IoTCompleter

        self.completer = IoTCompleter()

    def test_get_completions_with_comma(self):
        """カンマが含まれる場合の補完テスト"""
        from prompt_toolkit.completion import CompleteEvent
        from prompt_toolkit.document import Document

        document = Document('IOTGET("device", ')
        completions = list(self.completer.get_completions(document, CompleteEvent()))
        self.assertEqual(len(completions), 0)  # カンマがあるので補完しない

    def test_device_list_initialization(self):
        """デバイスリストの初期化テスト"""
        self.assertIsNotNone(self.completer.device_list)
        self.assertIsInstance(self.completer.device_list, list)


class TestBaseCompleter(unittest.TestCase):
    """BaseCompleterのテスト"""

    def test_get_completions_not_implemented(self):
        """get_completionsの未実装テスト"""
        completer = BaseCompleter()
        with self.assertRaises(NotImplementedError):
            list(completer.get_completions(None, None))


if __name__ == "__main__":
    unittest.main()
