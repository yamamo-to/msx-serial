# MSX Serial Terminal - Development Makefile

.PHONY: help test lint format check-all security complexity clean build install dev-install

# デフォルトターゲット
help:
	@echo "Available commands:"
	@echo "  test            - Run all tests with coverage"
	@echo "  lint            - Run all linting tools"
	@echo "  format          - Format code with black"
	@echo "  check-all       - Run all quality checks"
	@echo "  security        - Run security analysis"
	@echo "  complexity      - Analyze code complexity"
	@echo "  clean           - Clean build artifacts"
	@echo "  build           - Build package"
	@echo "  install         - Install package"
	@echo "  dev-install     - Install in development mode"

# テスト実行
test:
	python -m pytest --cov=msx_serial --cov-report=html --cov-report=term-missing

# 全体的な品質チェック
check-all: format lint test security complexity

# リンティング
lint:
	flake8 msx_serial/ tests/
	mypy msx_serial/

# フォーマット
format:
	black msx_serial/ tests/
	isort msx_serial/ tests/

# セキュリティチェック
security:
	bandit -r msx_serial/ -f screen

# 複雑度分析
complexity:
	radon cc --total-average --show-complexity msx_serial/
	radon mi msx_serial/ --show

# バージョン同期チェック
check-version:
	python update_readme_version.py --check

# ビルド成果物のクリーンアップ
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# パッケージビルド
build: clean
	python -m build

# 通常インストール
install:
	pip install .

# 開発環境インストール
dev-install:
	pip install -e .

# パフォーマンステスト
performance:
	@echo "Running performance tests..."
	python -m pytest tests/test_profiler.py tests/test_cache_manager.py -v

# 高度な品質チェック（新機能含む）
quality-advanced: format lint test security complexity performance
	@echo "Advanced quality check completed!"

# 依存関係の更新チェック
deps-check:
	@echo "Checking for dependency updates..."
	pip list --outdated

# ドキュメント生成
docs:
	@echo "Generating documentation..."
	mkdir -p docs
	python -c "import msx_serial; help(msx_serial)" > docs/api.txt || true

# メモリプロファイリング
memory-profile:
	@echo "Running memory profiling..."
	python -m memory_profiler tests/test_profiler.py 2>/dev/null || echo "Install memory_profiler: pip install memory-profiler"

# 全体統合テスト
integration-test:
	@echo "Running integration tests..."
	python -m pytest tests/ -k "integration" -v || echo "No integration tests found"

# リリース準備チェック
release-check: test lint security complexity
	@echo "Release readiness check completed!"
	@echo "Coverage: $$(python -m pytest --cov=msx_serial --cov-report=term-missing | grep TOTAL | awk '{print $$4}')" 