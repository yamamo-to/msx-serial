"""
Tests for color_output.py
"""

from unittest.mock import patch

import colorama

from msx_serial.common import color_output


def test_colorize():
    result = color_output._colorize("msg", colorama.Fore.RED)
    assert result.startswith(colorama.Fore.RED)
    assert result.endswith(colorama.Style.RESET_ALL)
    assert "msg" in result


def test_print_colored_default():
    with patch("builtins.print") as mock_print:
        color_output._print_colored("msg", "info")
        mock_print.assert_called_once()
        out = mock_print.call_args[0][0]
        assert colorama.Fore.CYAN in out
        assert "msg" in out


def test_print_colored_unknown_key():
    with patch("builtins.print") as mock_print:
        color_output._print_colored("msg", "unknown")
        out = mock_print.call_args[0][0]
        assert colorama.Fore.WHITE in out


def test_print_info():
    with patch("builtins.print") as mock_print:
        color_output.print_info("info")
        assert "info" in mock_print.call_args[0][0]


def test_print_warn():
    with patch("builtins.print") as mock_print:
        color_output.print_warn("warn")
        assert "warn" in mock_print.call_args[0][0]


def test_print_error():
    with patch("builtins.print") as mock_print:
        color_output.print_error("error")
        assert "error" in mock_print.call_args[0][0]


def test_print_exception():
    with patch("builtins.print") as mock_print:
        color_output.print_exception("EXC", Exception("fail"))
        out = mock_print.call_args[0][0]
        assert "EXC: fail" in out


def test_print_success():
    with patch("builtins.print") as mock_print:
        color_output.print_success("ok")
        assert "ok" in mock_print.call_args[0][0]


def test_print_debug():
    with patch("builtins.print") as mock_print:
        color_output.print_debug("debug")
        assert "debug" in mock_print.call_args[0][0]


def test_print_help():
    with patch("builtins.print") as mock_print:
        color_output.print_help("help")
        assert "help" in mock_print.call_args[0][0]


def test_print_receive():
    with patch("builtins.print") as mock_print:
        color_output.print_receive("recv", end="!")
        mock_print.assert_called_once()
        assert "recv" in mock_print.call_args[0][0]
        assert mock_print.call_args[1]["end"] == "!"


def test_print_prompt_receive():
    with patch("builtins.print") as mock_print:
        color_output.print_prompt_receive("prompt")
        mock_print.assert_called_once()
        assert mock_print.call_args[1]["end"] == ""
        assert mock_print.call_args[1]["flush"] is True


def test_str_info():
    s = color_output.str_info("abc")
    assert "[info]abc" in s
    assert colorama.Fore.CYAN in s


def test_str_warn():
    s = color_output.str_warn("abc")
    assert "[warn] abc" in s
    assert colorama.Fore.YELLOW in s


def test_str_error():
    s = color_output.str_error("abc")
    assert "[error] abc" in s
    assert colorama.Fore.RED in s


def test_str_exception():
    s = color_output.str_exception("oops", Exception("fail"))
    assert "[oops] fail" in s
    assert colorama.Fore.RED in s


def test_set_color_config():
    orig = color_output.COLORS["info"]
    color_output.set_color_config(info=colorama.Fore.GREEN)
    assert color_output.COLORS["info"] == colorama.Fore.GREEN
    # 戻す
    color_output.set_color_config(info=orig)


def test_set_color_config_invalid_key():
    # 無効なキーは無視される
    before = color_output.COLORS.copy()
    color_output.set_color_config(unknown=colorama.Fore.BLUE)
    assert color_output.COLORS == before
