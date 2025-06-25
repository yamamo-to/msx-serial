#!/usr/bin/env python3
"""
安全なリリースプロセス管理スクリプト
"""
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description, capture_output=True):
    """コマンドを実行し、結果を表示"""
    print(f"\n🔄 {description}...")
    result = subprocess.run(cmd, shell=True, capture_output=capture_output, text=True)

    if result.returncode != 0:
        print(f"❌ エラー: {description}")
        if capture_output:
            print(f"標準出力: {result.stdout}")
            print(f"エラー出力: {result.stderr}")
        return False

    print(f"✅ 完了: {description}")
    if capture_output and result.stdout.strip():
        print(f"出力: {result.stdout.strip()}")
    return True


def get_current_version():
    """現在のバージョンを取得"""
    version_file = Path("msx_serial/_version.py")
    if not version_file.exists():
        print("❌ バージョンファイルが見つかりません")
        return None

    content = version_file.read_text()
    import re

    match = re.search(r"__version__ = version = '([^']+)'", content)
    if match:
        return match.group(1)
    return None


def check_git_status():
    """Gitの状態をチェック"""
    result = subprocess.run(
        "git status --porcelain", shell=True, capture_output=True, text=True
    )
    if result.stdout.strip():
        print("⚠️  警告: コミットされていない変更があります:")
        print(result.stdout)
        return False
    return True


def check_git_tag_exists(version):
    """指定されたバージョンのGitタグが存在するかチェック"""
    result = subprocess.run(
        f"git tag -l | grep -q '^v{version}$'", shell=True, capture_output=True
    )
    return result.returncode == 0


def confirm_action(message):
    """ユーザーに確認を求める"""
    response = input(f"{message} (yes/no): ").strip().lower()
    return response == "yes"


def main():
    print("🚀 MSX Serial Terminal リリースプロセス")
    print("=" * 50)

    # バージョン確認
    version = get_current_version()
    if not version:
        sys.exit(1)

    print(f"📦 現在のバージョン: {version}")

    # 開発バージョンかチェック
    is_dev_version = "dev" in version
    if is_dev_version:
        print("⚠️  開発バージョンです")
        if not confirm_action("開発バージョンをリリースしますか？"):
            print("キャンセルされました")
            sys.exit(0)

    # Git状態チェック
    if not check_git_status():
        if not confirm_action("コミットされていない変更がありますが続行しますか？"):
            print("キャンセルされました")
            sys.exit(0)

    # リリース準備
    print("\n📋 リリース準備を開始します...")
    steps = [
        ("black msx_serial/ tests/", "コードフォーマット"),
        ("mypy msx_serial/", "型チェック"),
        ("python -m pytest", "テスト実行"),
        ("python update_readme_version.py", "README.mdバージョン更新"),
    ]

    for cmd, desc in steps:
        if not run_command(cmd, desc):
            print(f"❌ {desc}で失敗しました")
            sys.exit(1)

    print("\n✅ すべてのチェックが完了しました！")

    # Gitコミットとタグ
    if confirm_action("変更をコミットしてタグを作成しますか？"):
        # コミット
        if not run_command("git add -A", "変更をステージング"):
            sys.exit(1)

        commit_msg = f"Release v{version}"
        if not run_command(f'git commit -m "{commit_msg}"', "変更をコミット"):
            print("ℹ️  コミットする変更がないか、既にコミット済みです")

        # タグ作成
        if check_git_tag_exists(version):
            print(f"⚠️  タグ v{version} は既に存在します")
        else:
            if run_command(
                f'git tag -a "v{version}" -m "Release v{version}"',
                f"タグ v{version} を作成",
            ):
                print(f"✅ タグ v{version} を作成しました")

        # プッシュ
        if confirm_action("GitHubにプッシュしますか？"):
            run_command("git push", "変更をプッシュ")
            run_command("git push --tags", "タグをプッシュ")

    # ビルド
    print("\n🔨 パッケージビルドを開始します...")
    if not run_command("rm -rf dist/", "distディレクトリをクリーン"):
        sys.exit(1)

    if not run_command("python -m build", "パッケージをビルド"):
        sys.exit(1)

    # distディレクトリの内容を表示
    run_command("ls -la dist/", "ビルド結果を表示", capture_output=False)

    # TestPyPIアップロード確認
    if confirm_action("TestPyPIにアップロードしますか？"):
        if run_command(
            "python -m twine upload --repository testpypi dist/*",
            "TestPyPIアップロード",
        ):
            print("✅ TestPyPIアップロード完了")
            print("🔗 TestPyPIで確認: https://test.pypi.org/project/msx-serial/")

            if confirm_action("本番PyPIにアップロードしますか？"):
                if confirm_action(
                    "⚠️  最終確認: 本当に本番PyPIにアップロードしますか？"
                ):
                    if run_command(
                        "python -m twine upload dist/*", "本番PyPIアップロード"
                    ):
                        print("🎉 リリース完了！")
                        print("🔗 PyPI: https://pypi.org/project/msx-serial/")
                        print(
                            f"🏷️  GitHub Release: https://github.com/yamamo-to/msx-serial/releases/tag/v{version}"
                        )

    print("\n📋 手動で実行する場合:")
    print("1. make tag")
    print("2. git push --tags")
    print("3. make upload-test")
    print("4. make upload-prod")


if __name__ == "__main__":
    main()
