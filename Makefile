# MSX Serial Terminal Makefile

.PHONY: help test lint format check-version update-readme clean install dev-install build tag upload-test upload-prod release release-interactive

help:
	@echo "利用可能なコマンド:"
	@echo "  test           - テストを実行"
	@echo "  lint           - コード品質チェック"
	@echo "  format         - コードフォーマット"
	@echo "  check-version  - バージョン同期をチェック"
	@echo "  update-readme  - README.mdのバージョンを更新"
	@echo "  clean          - 一時ファイルを削除"
	@echo "  install        - パッケージをインストール"
	@echo "  dev-install    - 開発モードでインストール"
	@echo "  build          - パッケージをビルド（distディレクトリクリーン付き）"
	@echo "  tag            - 現在のバージョンでGitタグを作成"
	@echo "  upload-test    - TestPyPIにアップロード"
	@echo "  upload-prod    - PyPIにアップロード（本番）"
	@echo "  release        - リリース準備（テスト、フォーマット、バージョン更新）"
	@echo "  release-interactive - 対話的リリースプロセス"

test:
	python -m pytest

test-coverage:
	python -m pytest --cov=msx_serial --cov-report=term-missing

lint:
	mypy msx_serial/
	flake8 msx_serial/ tests/

format:
	black msx_serial/ tests/

check-version:
	python update_readme_version.py

update-readme:
	python update_readme_version.py

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .coverage htmlcov/ .pytest_cache/

install:
	pip install -e . --use-pep517

dev-install:
	pip install -e . --use-pep517
	pip install pytest pytest-cov black mypy flake8 twine build

# distディレクトリを確実にクリーンしてからビルド
build:
	@echo "🧹 distディレクトリをクリーン..."
	rm -rf dist/
	@echo "🔨 パッケージをビルド..."
	python -m build
	@echo "📦 ビルド完了: dist/"
	@ls -la dist/

# 現在のバージョンでGitタグを作成
tag:
	@echo "🏷️  Gitタグを作成..."
	@VERSION=$$(python -c "import msx_serial._version; print(msx_serial._version.__version__)"); \
	echo "バージョン: $$VERSION"; \
	if git tag -l | grep -q "^v$$VERSION$$"; then \
		echo "⚠️  タグ v$$VERSION は既に存在します"; \
		git tag -l | grep "^v$$VERSION$$"; \
	else \
		git tag -a "v$$VERSION" -m "Release v$$VERSION"; \
		echo "✅ タグ v$$VERSION を作成しました"; \
	fi

upload-test: build
	@echo "🧪 TestPyPIにアップロードします..."
	@echo "注意: これはテスト環境です"
	python -m twine upload --repository testpypi dist/*
	@echo "🔗 TestPyPI確認: https://test.pypi.org/project/msx-serial/"

upload-prod: build
	@echo "⚠️  警告: 本番PyPIにアップロードしようとしています ⚠️"
	@echo "このアクションは取り消せません！"
	@echo "続行するには 'yes' と入力してください:"
	@read confirm && [ "$$confirm" = "yes" ] || (echo "キャンセルされました" && exit 1)
	python -m twine upload dist/*
	@echo "🎉 PyPIアップロード完了!"
	@echo "🔗 PyPI確認: https://pypi.org/project/msx-serial/"

release: format lint test check-version
	@echo "✅ リリース準備完了！"
	@echo ""
	@echo "📋 推奨リリース手順:"
	@echo "1. git add -A && git commit -m 'Release準備'"
	@echo "2. git push"
	@echo "3. make tag           # Gitタグ作成"
	@echo "4. git push --tags    # タグをプッシュ"
	@echo "5. make upload-test   # TestPyPIでテスト"
	@echo "6. make upload-prod   # 本番リリース"
	@echo ""
	@echo "または: make release-interactive  # 対話的リリース"

release-interactive:
	python scripts/release.py 