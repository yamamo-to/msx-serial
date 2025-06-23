"""
補完機能の基本クラスと共通機能
"""

from collections import defaultdict
from typing import Dict, List, Optional, Set, Iterator
from prompt_toolkit.completion import Completer, Completion

from ..keyword_loader import load_keywords
from ..iot_loader import IotNodes


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

    def _create_completion(
        self,
        text: str,
        start_position: int,
        display: Optional[str] = None,
        meta: Optional[str] = None,
    ) -> Completion:
        """Create completion with consistent formatting"""
        return Completion(
            text,
            start_position=start_position,
            display=display or text,
            display_meta=meta,
        )

    def _match_prefix(self, candidates: List[str], prefix: str) -> List[str]:
        """Filter candidates by prefix"""
        if not prefix:
            return candidates
        return [c for c in candidates if c.upper().startswith(prefix.upper())]

    def _generate_keyword_completions(
        self, context: CompletionContext, keyword_type: str
    ) -> Iterator[Completion]:
        """Generate completions for a specific keyword type"""
        if keyword_type not in self.msx_keywords:
            return

        keywords = self.msx_keywords[keyword_type]["keywords"]
        for keyword in keywords:
            name, meta = self._get_keyword_info(keyword, keyword_type)
            if name.upper().startswith(context.word.upper()):
                yield self._create_completion(
                    name, -len(context.word), display=name, meta=meta
                )
