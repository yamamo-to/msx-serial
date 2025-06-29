"""
BASICファイルシステム情報管理とファイル補完機能
"""

import logging
import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ..common.cache_manager import cached
from ..common.config_manager import ConfigManager

logger = logging.getLogger(__name__)


def normalize_filename(name: str, ext: str = "") -> str:
    """ファイル名と拡張子を正規化して返す"""
    if ext:
        return f"{name.upper()}.{ext.upper()}"
    return name.upper()


def is_basic_extension(ext: str) -> bool:
    """BASICファイル拡張子判定"""
    return ext.upper() == "BAS"


@dataclass
class BASICFileInfo:
    """BASICファイル情報"""

    name: str
    extension: str
    size: Optional[int] = None

    @property
    def full_name(self) -> str:
        """完全なファイル名を取得"""
        return normalize_filename(self.name, self.extension)

    @property
    def is_basic_file(self) -> bool:
        """BASICファイルかどうか"""
        return is_basic_extension(self.extension)


class BASICFileSystemManager:
    """BASICファイルシステム情報管理クラス"""

    def __init__(self, connection: Optional[Any] = None) -> None:
        """初期化

        Args:
            connection: MSX接続オブジェクト
        """
        self.connection = connection
        self.current_directory = "A:\\"
        self.file_cache: Dict[str, BASICFileInfo] = {}
        self.cache_timestamp: Optional[float] = None
        # 設定値から取得、なければデフォルト
        self.cache_timeout = ConfigManager().get("basic.cache_timeout", 300.0)

        # BASICコマンドの引数パターン定義
        self.basic_file_commands = {
            k: True for k in ["RUN", "LOAD", "SAVE", "MERGE", "BLOAD", "BSAVE"]
        }

    def set_connection(self, connection: Any) -> None:
        """接続オブジェクトを設定"""
        self.connection = connection

    def set_current_directory(self, directory: str) -> None:
        """現在のディレクトリを設定"""
        self.current_directory = directory.upper()
        if not self.current_directory.endswith("\\"):
            self.current_directory += "\\"

    def set_test_files(self, files: Dict[str, BASICFileInfo]) -> None:
        """テスト用ファイル情報を設定（デバッグ・テスト用）

        Args:
            files: ファイル情報辞書
        """
        self.file_cache = files
        self.cache_timestamp = time.time()

    def is_cache_valid(self) -> bool:
        """キャッシュが有効かどうかチェック"""
        if self.cache_timestamp is None:
            return False

        current_time: float = time.time()
        cache_timestamp: float = self.cache_timestamp  # type: ignore
        result: bool = current_time - cache_timestamp < self.cache_timeout
        return result

    def parse_files_output(self, files_output: str) -> Dict[str, BASICFileInfo]:
        """FILES コマンドの出力を解析してファイル情報を抽出

        Args:
            files_output: FILES コマンドの出力文字列

        Returns:
            ファイル名をキーとするBASICFileInfo辞書
        """
        files = {}
        paired_names = set()  # NAME .EXTペアで登録したNAME
        exclude_keywords = {"FILES", "OK", "READY"}  # 除外するBASICキーワード
        lines = files_output.split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # ディレクトリパス行をスキップ（A:\SAMPLE のような形式）
            if re.match(r"^[A-Z]:\\[A-Z0-9_\-]*$", line, re.IGNORECASE):
                continue
            # システムメッセージをスキップ
            lower_line = line.lower()
            if (
                lower_line.startswith("volume")
                or lower_line.startswith("directory")
                or "free" in lower_line
                or " in " in lower_line
                or lower_line.endswith(" files")
            ):
                continue
            tokens = re.split(r"\s+", line)
            i = 0
            while i < len(tokens):
                token = tokens[i]
                token_upper = token.upper()
                if token_upper in [".", ".."] or token_upper in exclude_keywords:
                    i += 1
                    continue
                # NAME .EXTペア
                if (
                    i + 1 < len(tokens)
                    and re.fullmatch(r"[A-Z0-9_\-]+", token, re.IGNORECASE)
                    and re.fullmatch(r"\.[A-Z0-9]+", tokens[i + 1], re.IGNORECASE)
                ):
                    name = token_upper
                    extension = tokens[i + 1][1:].upper()
                    full_name = normalize_filename(name, extension)
                    if name not in exclude_keywords:
                        files[full_name] = BASICFileInfo(name=name, extension=extension)
                        paired_names.add(name)
                    i += 2
                elif "." in token:
                    # すでに拡張子付き
                    parts = token.rsplit(".", 1)
                    if len(parts) == 2:
                        name, extension = parts
                        name_upper = name.upper()
                        extension_upper = extension.upper()
                        full_name = normalize_filename(name_upper, extension_upper)
                        if name_upper not in exclude_keywords:
                            files[full_name] = BASICFileInfo(
                                name=name_upper, extension=extension_upper
                            )
                            paired_names.add(name_upper)
                    i += 1
                else:
                    # 拡張子なし
                    if (
                        token_upper not in files
                        and token_upper not in paired_names
                        and token_upper not in exclude_keywords
                    ):
                        files[token_upper] = BASICFileInfo(
                            name=token_upper, extension=""
                        )
                    i += 1
        return files

    def refresh_file_cache_sync(self) -> bool:
        """ファイルキャッシュを同期的に更新

        Returns:
            更新成功かどうか
        """
        if not self.connection:
            return False

        try:
            logger.info("FILESコマンドを実行します。出力が表示されますが正常です。")
            logger.info("FILESコマンドの実行が完了するまでお待ちください...")

            # FILESコマンドを実行
            self.connection.write("FILES\r\n".encode("utf-8"))

            # 出力を待機（実際の実装では適切な待機処理が必要）
            time.sleep(2)

            return True

        except OSError as e:
            logger.error(f"FILESコマンドの実行に失敗しました: {e}")
            return False

    async def refresh_file_cache(self) -> bool:
        """ファイルキャッシュを非同期で更新

        Returns:
            更新成功かどうか
        """
        if not self.connection:
            return False

        try:
            # FILESコマンドを実行
            await self.connection.write("FILES\r\n".encode("utf-8"))
            return True

        except OSError as e:
            logger.error(f"FILESコマンドの実行に失敗しました: {e}")
            return False

    def get_cached_files(self) -> Dict[str, BASICFileInfo]:
        """キャッシュされたファイル情報を取得

        Returns:
            ファイル情報辞書
        """
        if not self.is_cache_valid():
            return {}

        return self.file_cache.copy()

    def get_completions_for_command(
        self,
        command: str,
        current_word: str,
        argument_position: int,
    ) -> List[Tuple[str, str]]:
        """コマンドに応じたファイル補完候補を取得

        Args:
            command: BASICコマンド名
            current_word: 現在入力中の単語
            argument_position: 引数の位置（0=第一引数、1=第二引数...）

        Returns:
            (補完候補, 説明)のタプルのリスト
        """
        files = self.get_cached_files()
        completions = []

        command = command.upper()
        current_word = current_word.upper()

        # コマンドに応じた補完戦略
        if command in self.basic_file_commands:
            # BASICファイルコマンド: .BASファイルを優先
            target_files: List[BASICFileInfo] = []
            for file_info in files.values():
                if file_info.full_name.startswith(current_word):
                    if file_info.is_basic_file:
                        # .BASファイルを優先
                        target_files.insert(0, file_info)
                    else:
                        # その他のファイル
                        target_files.append(file_info)
        else:
            # その他のコマンド: 全ファイル
            target_files = [
                f for f in files.values() if f.full_name.startswith(current_word)
            ]

        # 補完候補を生成
        for file_info in target_files:
            if file_info.is_basic_file:
                description = f"📄 BASICファイル ({file_info.extension})"
            else:
                description = (
                    f"📄 {file_info.extension}ファイル"
                    if file_info.extension
                    else "📄 ファイル"
                )
                if file_info.size:
                    description += f" ({file_info.size} bytes)"

            # 引用符で囲む（BASICコマンドの仕様）
            completion = f'"{file_info.full_name}"'
            completions.append((completion, description))

        # アルファベット順にソート（.BASファイルを最初に）
        completions.sort(key=lambda x: (not x[1].startswith("📄 BASIC"), x[0]))

        return completions

    def parse_basic_command_line(self, command_line: str) -> Tuple[str, List[str], int]:
        """BASICコマンドラインを解析

        Args:
            command_line: BASICコマンドライン

        Returns:
            (コマンド, 引数リスト, 現在の引数位置)のタプル
        """
        import re

        s = command_line.strip()
        if not s:
            return "", [], 0

        # 先頭の英字部分をコマンドとして抽出
        m = re.match(r"^([A-Z_][A-Z0-9_]*)(.*)$", s, re.IGNORECASE)
        if not m:
            return s, [], 0
        command = m.group(1).upper()
        rest = m.group(2).lstrip()
        args = []
        if rest:
            # 引数部分が引用符で始まる場合
            if rest.startswith('"') and rest.endswith('"') and len(rest) > 1:
                args = [rest[1:-1]]
            elif rest.startswith('"'):
                args = [rest[1:]]
            elif rest:
                args = [rest]
        return command, args, len(args)

    @cached(ttl=30)
    def get_available_drives(self) -> List[str]:
        """利用可能なドライブ一覧を取得

        Returns:
            ドライブ文字のリスト
        """
        # 通常のMSXでは A: と B: が基本
        return ["A:", "B:", "C:", "D:"]
