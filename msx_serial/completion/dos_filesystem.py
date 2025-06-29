"""
DOSファイルシステム情報管理とファイル補完機能
"""

import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from ..common.cache_manager import cached


@dataclass
class DOSFileInfo:
    """DOSファイル情報"""

    name: str
    is_directory: bool
    size: Optional[int] = None
    date: Optional[str] = None
    time: Optional[str] = None

    @property
    def extension(self) -> str:
        """ファイル拡張子を取得"""
        if self.is_directory or "." not in self.name:
            return ""
        return self.name.split(".")[-1].upper()

    @property
    def is_executable(self) -> bool:
        """実行可能ファイルかどうか"""
        return self.extension in {"COM", "BAT", "EXE"}


class DOSFileSystemManager:
    """DOSファイルシステム情報管理クラス"""

    def __init__(self, connection: Optional[Any] = None) -> None:
        """初期化

        Args:
            connection: MSX接続オブジェクト
        """
        self.connection = connection
        self.current_directory = "A:\\"
        self.directory_cache: Dict[str, Dict[str, DOSFileInfo]] = {}
        self.cache_timestamps: Dict[str, float] = {}
        self.cache_timeout = 30.0  # 30秒でキャッシュ無効化

        # DOSコマンドの引数パターン定義（第一引数に任意のファイルを受ける）
        self.executable_commands = {
            "COPY",
            "DEL",
            "REN",
            "TYPE",
            "EDIT",
            "DEBUG",
            "LINK",
            "LOAD",
            "SAVE",
            "BLOAD",
            "BSAVE",
            "MERGE",
        }

        # 第一引数に実行ファイルを要求するコマンド
        self.run_commands = {
            "RUN": True,  # BASICファイルまたは実行ファイル
        }

    def set_connection(self, connection: Any) -> None:
        """接続オブジェクトを設定"""
        self.connection = connection

    def set_current_directory(self, directory: str) -> None:
        """現在のディレクトリを設定"""
        self.current_directory = directory.upper()
        if not self.current_directory.endswith("\\"):
            self.current_directory += "\\"

    def set_test_files(self, directory: str, files: Dict[str, DOSFileInfo]) -> None:
        """テスト用ファイル情報を設定（デバッグ・テスト用）

        Args:
            directory: ディレクトリパス
            files: ファイル情報辞書
        """
        import time

        self.directory_cache[directory.upper()] = files
        self.cache_timestamps[directory.upper()] = time.time()

    def is_cache_valid(self, directory: str) -> bool:
        """キャッシュが有効かどうかチェック"""
        if directory not in self.cache_timestamps:
            return False

        return time.time() - self.cache_timestamps[directory] < self.cache_timeout

    def parse_dir_output(self, dir_output: str) -> Dict[str, DOSFileInfo]:
        """DIR コマンドの出力を解析してファイル情報を抽出

        Args:
            dir_output: DIR コマンドの出力文字列

        Returns:
            ファイル名をキーとするDOSFileInfo辞書
        """
        files = {}

        # 実際のMSX-DOS DIR出力の分析
        # 例:
        # HELP            <dir>
        # AUTOEXEC BAT        57
        # COMMAND2 COM     14976
        # PENGUIN  S02     14343

        lines = dir_output.split("\n")

        for line in lines:
            # 先頭と末尾の空白は残す（MSX-DOSの出力フォーマットのため）
            line = line.rstrip()
            if not line:
                continue

            # システムメッセージや集計行をスキップ（単語境界を考慮）
            lower_line = line.lower().strip()
            if (
                lower_line.startswith("volume")
                or lower_line.startswith("directory")
                or "free" in lower_line
                or " in " in lower_line
                or lower_line.endswith(" files")
            ):
                continue

            # ディレクトリパターン: "HELP            <dir> "
            dir_match = re.match(r"^(\S+)\s+<dir>\s*$", line, re.IGNORECASE)
            if dir_match:
                dirname = dir_match.group(1)
                files[dirname.upper()] = DOSFileInfo(
                    name=dirname.upper(),
                    is_directory=True,
                )
                continue

            # ファイルパターン1: "AUTOEXEC BAT        57" (ファイル名 拡張子 サイズ)
            file_match = re.match(r"^(\S+)\s+(\S+)\s+(\d+)\s*$", line)
            if file_match:
                filename, extension, size_str = file_match.groups()
                # 拡張子が数字のみでない場合はファイル名.拡張子として結合
                if not extension.isdigit():
                    full_filename = f"{filename}.{extension}".upper()
                    files[full_filename] = DOSFileInfo(
                        name=full_filename,
                        is_directory=False,
                        size=int(size_str),
                    )
                    continue
                else:
                    # 拡張子が数字の場合は、それがサイズ（拡張子なしファイル）
                    files[filename.upper()] = DOSFileInfo(
                        name=filename.upper(),
                        is_directory=False,
                        size=int(extension),
                    )
                    continue

            # ファイルパターン2: 拡張子なしファイル（万一の場合）
            single_match = re.match(r"^(\S+)\s+(\d+)\s*$", line)
            if single_match:
                filename, size_str = single_match.groups()
                files[filename.upper()] = DOSFileInfo(
                    name=filename.upper(),
                    is_directory=False,
                    size=int(size_str),
                )
                continue

        return files

    def refresh_directory_cache_sync(self, directory: Optional[str] = None) -> bool:
        """指定ディレクトリのキャッシュを同期的に更新

        Args:
            directory: 更新するディレクトリパス（Noneの場合は現在のディレクトリ）

        Returns:
            更新成功かどうか
        """
        if not self.connection:
            return False

        target_dir = directory or self.current_directory

        try:
            print("DIRコマンドを実行します。出力が表示されますが正常です。")
            print("DIRコマンドの実行が完了するまでお待ちください...")

            # ディレクトリ変更が必要な場合
            if target_dir != self.current_directory:
                command_data = f"CD {target_dir}\r".encode("msx-jp")
                self.connection.write(command_data)
                self.connection.flush()
                time.sleep(0.5)

            # DIRコマンド実行（出力は通常のターミナルに表示される）
            dir_command_data = "DIR\r".encode("msx-jp")
            self.connection.write(dir_command_data)
            self.connection.flush()

            # DIRコマンドの完了を待つ
            time.sleep(2.0)

            print("DIRコマンドの実行が完了しました。")
            print("DIRコマンドの出力が自動的にキャッシュに反映されます。")

            return False  # 自動更新は失敗として、手動設定を促す

        except Exception as e:
            print(f"DOSキャッシュ更新エラー: {e}")
            return False

    async def refresh_directory_cache(self, directory: Optional[str] = None) -> bool:
        """指定ディレクトリのキャッシュを非同期で更新（将来の拡張用）

        Args:
            directory: 更新するディレクトリパス（Noneの場合は現在のディレクトリ）

        Returns:
            更新成功かどうか
        """
        # 現在は同期版を呼び出し（将来的に非同期I/Oに対応する際に拡張）
        return self.refresh_directory_cache_sync(directory)

    def get_directory_files(
        self, directory: Optional[str] = None
    ) -> Dict[str, DOSFileInfo]:
        """ディレクトリのファイル一覧を取得（キャッシュ使用）

        Args:
            directory: 取得するディレクトリパス（Noneの場合は現在のディレクトリ）

        Returns:
            ファイル名をキーとするDOSFileInfo辞書
        """
        target_dir = directory or self.current_directory

        # キャッシュが有効な場合はそれを返す
        if self.is_cache_valid(target_dir):
            return self.directory_cache.get(target_dir, {})

        # キャッシュが無効な場合は空の辞書を返す
        # （非同期でrefresh_directory_cacheを呼ぶべき）
        return {}

    def get_completions_for_command(
        self,
        command: str,
        current_word: str,
        argument_position: int,
        directory: Optional[str] = None,
    ) -> List[Tuple[str, str]]:
        """コマンドに応じたファイル補完候補を取得

        Args:
            command: DOSコマンド名
            current_word: 現在入力中の単語
            argument_position: 引数の位置（0=第一引数、1=第二引数...）
            directory: 検索するディレクトリ（Noneの場合は現在のディレクトリ）

        Returns:
            (補完候補, 説明)のタプルのリスト
        """
        files = self.get_directory_files(directory)
        completions = []

        command = command.upper()
        current_word = current_word.upper()

        # コマンドに応じた補完戦略
        if command in self.run_commands:
            # RUNコマンド: 実行ファイルとディレクトリのみ
            target_files = [
                f
                for f in files.values()
                if (f.is_executable or f.is_directory)
                and f.name.startswith(current_word)
            ]
        else:
            # その他のコマンド: 全ファイル（TYPE、COPY、DELなど）
            target_files = [
                f for f in files.values() if f.name.startswith(current_word)
            ]

        # 補完候補を生成
        for file_info in target_files:
            if file_info.is_directory:
                description = "📁 ディレクトリ"
                completion = file_info.name + "\\"
            elif file_info.is_executable:
                description = f"⚡ 実行ファイル ({file_info.extension})"
                completion = file_info.name
            else:
                description = f"📄 {file_info.extension}ファイル"
                if file_info.size:
                    description += f" ({file_info.size} bytes)"
                completion = file_info.name

            completions.append((completion, description))

        # アルファベット順にソート（ディレクトリを最初に）
        completions.sort(key=lambda x: (not x[0].endswith("\\"), x[0]))

        return completions

    @cached(ttl=30)
    def get_available_drives(self) -> List[str]:
        """利用可能なドライブ一覧を取得

        Returns:
            ドライブ文字のリスト
        """
        # 通常のMSX-DOSでは A: と B: が基本
        # 実際の実装では接続先にクエリして確認すべき
        return ["A:", "B:", "C:", "D:"]

    def parse_dos_command_line(self, command_line: str) -> Tuple[str, List[str], int]:
        """DOSコマンドラインを解析

        Args:
            command_line: 入力されたコマンドライン

        Returns:
            (コマンド名, 引数リスト, 現在の引数位置)
        """
        # 末尾スペースの有無を事前に記録
        ends_with_space = command_line.endswith(" ")

        parts = command_line.strip().split()
        if not parts:
            return "", [], 0

        command = parts[0].upper()
        args = parts[1:] if len(parts) > 1 else []

        # 現在の引数位置を判定
        # 末尾にスペースがある場合は次の引数
        current_arg_pos = len(args)
        if ends_with_space:
            current_arg_pos += 1

        return command, args, current_arg_pos
