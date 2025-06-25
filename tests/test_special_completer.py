"""
Tests for SpecialCompleter (special_completer.py)
"""

from unittest.mock import patch
import pytest
from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.document import Document
from msx_serial.completion.completers.special_completer import SpecialCompleter


class DummyCommandType:
    def __init__(self, desc):
        self.description = desc

    def __bool__(self):
        return True

    @staticmethod
    def from_input(cmd):
        # Return DummyCommandType if command starts with @
        if cmd.startswith("@"):
            return DummyCommandType(f"desc:{cmd}")
        return None


@pytest.fixture
def completer():
    # Patch CommandType.from_input globally
    with patch(
        "msx_serial.completion.completers.special_completer.CommandType",
        DummyCommandType,
    ):
        c = SpecialCompleter(["@foo", "@bar", "@baz", "@cd", "@encode"])
        c.msx_keywords = {
            "ENCODE": {"keywords": [("UTF-8", "utf8desc"), ("SJIS", "sjisdesc")]}
        }
        yield c


def test_complete_cd_path(completer):
    # @cd のパス補完
    with patch.object(completer.path_completer, "get_completions") as mock_path:
        mock_path.return_value = iter(["/tmp", "/home"])
        doc = Document("@cd /h", cursor_position=6)
        event = CompleteEvent()
        list(completer.get_completions(doc, event))
        mock_path.assert_called()


def test_complete_encode(completer):
    # @encode の補完
    called = []

    def fake_from_input(cmd):
        called.append(cmd)
        return DummyCommandType("desc:@encode")

    with patch(
        "msx_serial.completion.completers.special_completer.CommandType.from_input",
        side_effect=fake_from_input,
    ):
        doc = Document("@encode U", cursor_position=9)
        event = CompleteEvent()
        results = list(completer.get_completions(doc, event))
        assert any(
            r.text == "UTF-8" and r.display_meta[0][1] == "utf8desc" for r in results
        )


def test_complete_other_special(completer):
    # @foo などの特殊コマンド補完
    called = []

    def fake_from_input(cmd):
        called.append(cmd)
        return DummyCommandType(f"desc:{cmd}")

    with patch(
        "msx_serial.completion.completers.special_completer.CommandType.from_input",
        side_effect=fake_from_input,
    ):
        doc = Document("@f", cursor_position=2)
        event = CompleteEvent()
        results = list(completer.get_completions(doc, event))
        assert any(r.text == "foo" and r.display[0][1] == "@foo" for r in results)
        assert all(r.display_meta[0][1].startswith("desc:@") for r in results)


def test_complete_no_at_prefix(completer):
    # @なしでも補完される
    doc = Document("b", cursor_position=1)
    event = CompleteEvent()
    results = list(completer.get_completions(doc, event))
    assert any(r.text == "bar" for r in results)


def test_complete_no_match(completer):
    # マッチしない場合
    doc = Document("@xyz", cursor_position=4)
    event = CompleteEvent()
    results = list(completer.get_completions(doc, event))
    assert results == []


def test_complete_encode_no_keywords(completer):
    # ENCODEキーワードが空の場合
    completer.msx_keywords = {"ENCODE": {"keywords": []}}
    doc = Document("@encode ", cursor_position=8)
    event = CompleteEvent()
    results = list(completer.get_completions(doc, event))
    assert results == []


def test_complete_encode_partial(completer):
    # ENCODEキーワードの部分一致
    completer.msx_keywords = {
        "ENCODE": {"keywords": [("UTF-8", "utf8desc"), ("SJIS", "sjisdesc")]}
    }
    doc = Document("@encode S", cursor_position=9)
    event = CompleteEvent()
    results = list(completer.get_completions(doc, event))
    assert any(r.text == "SJIS" for r in results)
