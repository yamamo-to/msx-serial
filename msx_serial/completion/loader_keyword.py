import importlib
import yaml
from pathlib import Path
from typing import List, TypedDict, Any, Dict


class KeywordInfo(TypedDict):
    description: str
    type: str
    keywords: List[List[str]]


def load_keywords() -> Dict[str, KeywordInfo]:
    """MSXキーワードを読み込む

    Returns:
        Dict[str, KeywordInfo]: キーワード情報の辞書

    Raises:
        FileNotFoundError: キーワードファイルが見つからない場合
        yaml.YAMLError: YAMLファイルの解析に失敗した場合
    """
    try:
        # まずimportlib.resourcesを使用して読み込みを試みる
        try:
            with (
                importlib.resources.files("msx_serial.data")
                .joinpath("msx_keywords.yml")
                .open("r", encoding="utf-8") as f
            ):
                return yaml.safe_load(f)
        except (AttributeError, FileNotFoundError):
            # importlib.resourcesが失敗した場合、直接ファイルパスを使用
            data_path = Path(__file__).parent.parent / "data" / "msx_keywords.yml"
            with data_path.open("r", encoding="utf-8") as f:
                return yaml.safe_load(f)
    except Exception as e:
        raise RuntimeError(f"キーワードファイルの読み込みに失敗: {str(e)}")
