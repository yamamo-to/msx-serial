import importlib
import yaml
from typing import Dict, List, Union, TypedDict


class KeywordInfo(TypedDict):
    description: str
    type: str
    keywords: List[Union[str, tuple[str, str]]]


def load_keywords() -> Dict[str, KeywordInfo]:
    # with open(yaml_path, "r", encoding="utf-8") as f:
    with (
        importlib.resources.files("msx_serial.data")
        .joinpath("msx_keywords.yml")
        .open("r", encoding="utf-8") as f
    ):
        data = yaml.safe_load(f)
    return data
