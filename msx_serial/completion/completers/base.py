"""
補完機能の基本クラスと共通機能
"""

from collections import defaultdict
from typing import Dict, List, Optional, Set
from prompt_toolkit.completion import Completer

from ...util.loader_keyword import load_keywords
from ...util.loader_iot_nodes import IotNodes


class CompletionContext:
    """補完コンテキストを管理するクラス"""

    def __init__(self, text: str, word: str) -> None:
        self.text = text
        self.word = word
        self.is_rem_or_string = False
        self.is_special_command = False
        self.is_iot_command = False
        self.current_command: Optional[str] = None


class BaseCompleter(Completer):
    """補完機能の基本クラス"""

    def __init__(self) -> None:
        """初期化"""
        self.user_variables: Set[str] = set()
        self.device_list = IotNodes().get_node_names()
        self.msx_keywords = load_keywords()
        self._initialize_caches()

    def _initialize_caches(self) -> None:
        """キーワードキャッシュを初期化"""
        self.keyword_caches: Dict[str, Dict[str, List[str]]] = defaultdict(dict)
        self.sub_commands: List[str] = []

        for key, info in self.msx_keywords.items():
            if info["type"] == "subcommand":
                self.sub_commands.append(key)
            self.keyword_caches[key] = self._build_prefix_cache(info["keywords"])

    def _build_prefix_cache(self, keywords: List[List[str]]) -> Dict[str, List[str]]:
        """プレフィックスキャッシュを構築

        Args:
            keywords: キーワードのリスト

        Returns:
            プレフィックスキャッシュ
        """
        cache: Dict[str, List[str]] = defaultdict(list)
        for keyword in keywords:
            name = keyword[0]
            for i in range(1, len(name) + 1):
                prefix = name[:i]
                cache[prefix].append(name)
        return cache

    def _get_keyword_info(self, keyword: str, key: str) -> tuple[str, str]:
        """キーワード情報を取得

        Args:
            keyword: キーワード
            key: キー

        Returns:
            (キーワード名, メタ情報)のタプル
        """
        if isinstance(keyword, list):
            return keyword[0], keyword[1]
        return keyword, self.msx_keywords[key]["description"]
