"""
Tests for keyword_loader.py
"""

import pytest
import yaml
from msx_serial.completion import keyword_loader
from pathlib import Path
from unittest.mock import patch
import io


# 正常系: importlib.resources.filesで正常に読み込める場合
def test_load_keywords_importlib_success(monkeypatch):
    dummy_yaml = (
        "BASIC:\n  description: desc\n  type: type\n  keywords:\n    - [RUN, run]\n"
    )

    class DummyFile:
        def open(self, *a, **k):
            return io.StringIO(dummy_yaml)

    class DummyResources:
        def joinpath(self, name):
            return DummyFile()

    monkeypatch.setattr("importlib.resources.files", lambda pkg: DummyResources())
    result = keyword_loader.load_keywords()
    assert "BASIC" in result
    assert result["BASIC"]["description"] == "desc"


# importlib.resources.filesがNoneを返す場合
def test_load_keywords_importlib_none(monkeypatch):
    monkeypatch.setattr("importlib.resources.files", lambda pkg: None)
    with patch.object(Path, "exists", return_value=False):
        with pytest.raises(FileNotFoundError):
            keyword_loader.load_keywords()


# importlib.resources.filesでFileNotFoundError→data_path.exists()=False
def test_load_keywords_file_not_found(monkeypatch):
    class DummyResources:
        def joinpath(self, name):
            raise FileNotFoundError()

    monkeypatch.setattr("importlib.resources.files", lambda pkg: DummyResources())
    with patch.object(Path, "exists", return_value=False):
        with pytest.raises(FileNotFoundError):
            keyword_loader.load_keywords()


# importlib.resources.filesでFileNotFoundError→data_path.exists()=True→openでYAML正常
def test_load_keywords_fallback_success(monkeypatch):
    dummy_yaml = (
        "BASIC:\n  description: desc\n  type: type\n  keywords:\n    - [RUN, run]\n"
    )

    class DummyResources:
        def joinpath(self, name):
            raise FileNotFoundError()

    monkeypatch.setattr("importlib.resources.files", lambda pkg: DummyResources())
    with (
        patch.object(Path, "exists", return_value=True),
        patch.object(Path, "open", lambda self, *a, **k: io.StringIO(dummy_yaml)),
    ):
        result = keyword_loader.load_keywords()
        assert "BASIC" in result
        assert result["BASIC"]["description"] == "desc"


# YAMLパースエラー
def test_load_keywords_yaml_error(monkeypatch):
    class DummyFile:
        def open(self, *a, **k):
            return io.StringIO("bad: [unclosed")

    class DummyResources:
        def joinpath(self, name):
            return DummyFile()

    monkeypatch.setattr("importlib.resources.files", lambda pkg: DummyResources())
    monkeypatch.setattr(
        "yaml.safe_load", lambda s: (_ for _ in ()).throw(yaml.YAMLError("parse error"))
    )
    with pytest.raises(RuntimeError) as e:
        keyword_loader.load_keywords()
    assert "キーワードファイルの読み込みに失敗" in str(e.value)
