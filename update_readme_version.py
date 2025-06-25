#!/usr/bin/env python3
"""
README.mdの更新履歴のバージョンを自動更新するスクリプト
"""
import re
from pathlib import Path


def get_current_version():
    """現在のバージョンを_version.pyから取得"""
    version_file = Path("msx_serial/_version.py")
    if not version_file.exists():
        raise FileNotFoundError("バージョンファイルが見つかりません")

    content = version_file.read_text(encoding="utf-8")
    match = re.search(r"__version__ = version = '([^']+)'", content)
    if match:
        return match.group(1)
    raise ValueError("バージョンが取得できませんでした")


def update_readme_version():
    """README.mdの更新履歴のバージョンを更新"""
    readme_file = Path("README.md")
    if not readme_file.exists():
        raise FileNotFoundError("README.mdが見つかりません")

    current_version = get_current_version()
    content = readme_file.read_text(encoding="utf-8")

    # 最新バージョンのエントリを探す
    version_pattern = r"### v(\d+\.\d+\.\d+(?:\.dev\d+)?)"
    matches = list(re.finditer(version_pattern, content))

    if matches:
        # 最初に見つかったバージョンを現在のバージョンに更新
        first_match = matches[0]
        old_version = first_match.group(1)

        if old_version != current_version:
            print(f"バージョンを更新: v{old_version} -> v{current_version}")
            content = content.replace(f"### v{old_version}", f"### v{current_version}")
            readme_file.write_text(content, encoding="utf-8")
            return True
        else:
            print(f"バージョンは既に最新です: v{current_version}")
            return False
    else:
        print("更新履歴にバージョン情報が見つかりませんでした")
        return False


if __name__ == "__main__":
    try:
        updated = update_readme_version()
        if updated:
            print("README.mdを更新しました")
        else:
            print("更新の必要はありませんでした")
    except Exception as e:
        print(f"エラー: {e}")
        exit(1)
