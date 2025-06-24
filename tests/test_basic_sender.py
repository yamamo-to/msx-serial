#!/usr/bin/env python3
"""
Basic sender の単体試験
"""

import unittest
from unittest.mock import patch, Mock

from msx_serial.transfer.basic_sender import load_template, send_basic_program


class TestBasicSender(unittest.TestCase):
    """Basic sender の単体試験"""

    @patch("msx_serial.transfer.basic_sender.resources")
    def test_load_template_success(self, mock_resources):
        """テンプレート読み込み成功テスト"""
        # モックの設定
        mock_file = Mock()
        mock_file.read_text.return_value = "test template content"
        mock_files = Mock()
        mock_files.joinpath.return_value = mock_file
        mock_resources.files.return_value = mock_files

        result = load_template("test.bas")

        self.assertEqual(result, "test template content")
        mock_resources.files.assert_called_once_with("msx_serial.transfer")
        mock_files.joinpath.assert_called_once_with("test.bas")
        mock_file.read_text.assert_called_once_with(encoding="utf-8")

    @patch("msx_serial.transfer.basic_sender.resources")
    def test_load_template_file_not_found(self, mock_resources):
        """テンプレートファイルが見つからない場合のテスト"""
        # FileNotFoundErrorを発生させる
        mock_file = Mock()
        mock_file.read_text.side_effect = FileNotFoundError("File not found")
        mock_files = Mock()
        mock_files.joinpath.return_value = mock_file
        mock_resources.files.return_value = mock_files

        result = load_template("nonexistent.bas")

        self.assertIsNone(result)

    def test_send_basic_program_simple(self):
        """シンプルなBASICプログラム送信テスト"""
        # テンプレート内容を直接設定
        program_template = '10 PRINT "Hello {{ name }}!"\n20 END'
        variables = {"name": "World"}

        with patch("msx_serial.transfer.basic_sender.load_template") as mock_load:
            mock_load.return_value = program_template

            result = send_basic_program("hello.bas", variables)

            expected = '10 PRINT "Hello World!"\r\n20 END\r\n'
            self.assertEqual(result, expected)
            mock_load.assert_called_once_with("hello.bas")

    def test_send_basic_program_with_whitespace(self):
        """空白を含むBASICプログラム送信テスト"""
        # 各行の末尾に空白があるテンプレート
        program_template = '10 PRINT "Test"   \n20 FOR I=1 TO 10  \n30 NEXT I\n40 END  '
        variables = {}

        with patch("msx_serial.transfer.basic_sender.load_template") as mock_load:
            mock_load.return_value = program_template

            result = send_basic_program("test.bas", variables)

            # 各行の末尾の空白が削除されることを確認
            expected = '10 PRINT "Test"\r\n20 FOR I=1 TO 10\r\n30 NEXT I\r\n40 END\r\n'
            self.assertEqual(result, expected)

    def test_send_basic_program_empty_lines(self):
        """空行を含むBASICプログラム送信テスト"""
        program_template = '10 PRINT "Start"\n\n20 PRINT "End"\n'
        variables = {}

        with patch("msx_serial.transfer.basic_sender.load_template") as mock_load:
            mock_load.return_value = program_template

            result = send_basic_program("empty_lines.bas", variables)

            # 空行も含めて適切に処理されることを確認
            expected = '10 PRINT "Start"\r\n\r\n20 PRINT "End"\r\n'
            self.assertEqual(result, expected)

    def test_send_basic_program_multiple_variables(self):
        """複数変数を使用するBASICプログラム送信テスト"""
        program_template = """10 REM {{ title }}
20 PRINT "{{ message }}"
30 FOR I=1 TO {{ count }}
40 PRINT "{{ item }} ";I
50 NEXT I
60 END"""
        variables = {
            "title": "Test Program",
            "message": "Hello MSX!",
            "count": "5",
            "item": "Item",
        }

        with patch("msx_serial.transfer.basic_sender.load_template") as mock_load:
            mock_load.return_value = program_template

            result = send_basic_program("multi_var.bas", variables)

            expected_lines = [
                "10 REM Test Program",
                '20 PRINT "Hello MSX!"',
                "30 FOR I=1 TO 5",
                '40 PRINT "Item ";I',
                "50 NEXT I",
                "60 END",
            ]
            expected = "\r\n".join(expected_lines) + "\r\n"
            self.assertEqual(result, expected)

    def test_send_basic_program_no_variables(self):
        """変数なしのBASICプログラム送信テスト"""
        program_template = '10 PRINT "Static content"\n20 END'
        variables = {}

        with patch("msx_serial.transfer.basic_sender.load_template") as mock_load:
            mock_load.return_value = program_template

            result = send_basic_program("static.bas", variables)

            expected = '10 PRINT "Static content"\r\n20 END\r\n'
            self.assertEqual(result, expected)

    def test_send_basic_program_line_endings(self):
        """改行コードの統一テスト"""
        # 異なる改行コードが混在するテンプレート
        program_template = (
            '10 PRINT "Line1"\r\n20 PRINT "Line2"\n30 PRINT "Line3"\r40 END'
        )
        variables = {}

        with patch("msx_serial.transfer.basic_sender.load_template") as mock_load:
            mock_load.return_value = program_template

            result = send_basic_program("mixed_endings.bas", variables)

            # すべて\r\nに統一されることを確認
            expected = (
                '10 PRINT "Line1"\r\n20 PRINT "Line2"\r\n30 PRINT "Line3"\r\n40 END\r\n'
            )
            self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
