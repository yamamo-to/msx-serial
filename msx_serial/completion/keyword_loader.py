import importlib
import yaml
from pathlib import Path
from typing import List, TypedDict, Dict, cast


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
    # まずimportlib.resourcesを使用して読み込みを試みる
    try:
        package = importlib.resources.files("msx_serial.data")
        if package is None:
            raise ImportError("msx_serial.dataパッケージが見つかりません")

        with package.joinpath("msx_keywords.yml").open("r", encoding="utf-8") as f:
            return cast(Dict[str, KeywordInfo], yaml.safe_load(f))
    except (AttributeError, FileNotFoundError, ImportError) as e:
        # importlib.resourcesが失敗した場合、直接ファイルパスを使用
        data_path = Path(__file__).parent.parent / "data" / "msx_keywords.yml"
        if not data_path.exists():
            raise FileNotFoundError(
                f"キーワードファイルが見つかりません: {data_path}"
            ) from e

        with data_path.open("r", encoding="utf-8") as f:
            return cast(Dict[str, KeywordInfo], yaml.safe_load(f))
    except Exception as e:
        raise RuntimeError(f"キーワードファイルの読み込みに失敗: {str(e)}") from e
