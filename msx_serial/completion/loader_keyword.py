import importlib
import yaml
from typing import List, TypedDict, Any


class KeywordInfo(TypedDict):
    description: str
    type: str
    keywords: List[List[str]]


def load_keywords() -> Any:
    with (
        importlib.resources.files("msx_serial.data")
        .joinpath("msx_keywords.yml")
        .open("r", encoding="utf-8") as f
    ):
        data = yaml.safe_load(f)
    return data
