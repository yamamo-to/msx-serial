# MSXシリアルターミナル - 開発ガイド

📖 **ガイド一覧**
- [🚀 クイックスタート](../README.md) - 基本的な使い方
- [📋 詳細ガイド](USAGE.md) - 高度な機能と設定
- [🔧 開発ガイド](DEVELOPMENT.md) - 開発・貢献方法 **(このページ)**

---

## アーキテクチャ概要

### 主要コンポーネント

```
msx_serial/
├── commands/        # コマンド処理系
│   ├── handler.py       # メインコマンドハンドラー
│   ├── command_types.py # コマンド型定義
│   └── performance_commands.py # パフォーマンス関連
├── completion/      # オートコンプリート機能  
│   ├── completers/      # 各種コンプリーター
│   └── keyword_loader.py # キーワード読み込み
├── connection/      # 接続管理
│   ├── manager.py       # 接続マネージャー
│   ├── serial.py        # シリアル接続
│   └── telnet.py        # Telnet接続
├── core/           # コア機能
│   ├── msx_session.py   # MSXセッション管理
│   └── data_processor.py # データ処理
├── display/        # 表示機能
│   ├── basic_display.py    # 基本表示
│   └── enhanced_display.py # 高度表示
├── io/            # 入出力システム
│   ├── input_session.py   # 入力セッション
│   └── user_interface.py  # ユーザーインターフェース
└── common/        # 共通機能
    ├── config_manager.py  # 設定管理
    ├── cache_manager.py   # キャッシュ管理
    └── profiler.py        # パフォーマンス計測
```

### 設計原則

1. **モジュラー設計**: 機能別の明確な分離
2. **型安全性**: mypy準拠の型注釈
3. **テスト駆動**: 95%以上のテストカバレッジ  
4. **設定駆動**: ConfigManagerによる集中管理
5. **パフォーマンス重視**: Profilerによる計測とキャッシュ活用

## 開発環境構築

### 1. 必要なソフトウェア

```bash
# Python 3.9以上が必要
python --version  # Python 3.9+

# Gitが必要
git --version
```

### 2. リポジトリのクローンと環境構築

```bash
# リポジトリクローン
git clone https://github.com/your-username/msx-serial.git
cd msx-serial

# 仮想環境作成
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# 依存関係インストール
pip install -e .[dev]
```

### 3. 開発用Makeタスク

```bash
# 📋 開発タスク一覧
make help           # 全タスクの一覧表示

# 🔍 品質チェック
make check-all      # 全品質チェック実行
make test           # テスト実行（カバレッジ付き）
make lint           # flake8・mypy実行
make security       # banditセキュリティチェック
make complexity     # Radonコード複雑度測定

# 🎨 コードフォーマット
make format         # black・isort適用
make format-check   # フォーマット確認のみ

# 📦 ビルド・リリース
make build          # パッケージビルド
make release-check  # リリース準備確認

# 🚀 高度な品質チェック
make quality-advanced # 包括的品質分析
make performance    # パフォーマンステスト
make deps-check     # 依存関係更新確認
```

## テスト設計

### テスト戦略

- **ユニットテスト**: 個別関数・クラスの動作確認
- **統合テスト**: コンポーネント間の連携確認  
- **パフォーマンステスト**: レスポンス時間・メモリ使用量測定
- **セキュリティテスト**: banditによる脆弱性検出

### テスト実行

```bash
# 基本テスト実行
make test

# 詳細テスト実行
pytest -v --cov=msx_serial --cov-report=html

# 特定テストファイル実行
pytest tests/test_commands.py -v

# テストパターン指定
pytest -k "test_help" -v
```

### テストカバレッジ要件

- **全体カバレッジ**: 95%以上必須
- **新機能**: 100%カバレッジ必須
- **重要機能**: 100%カバレッジ推奨
- **レポート**: HTMLレポートで詳細確認

### 新機能テスト追加手順

1. **テストクラス作成**: `Test`で始まるクラス名
2. **テストメソッド作成**: `test_`で始まるメソッド名  
3. **正常系テスト**: 期待される動作の確認
4. **異常系テスト**: エラーハンドリングの確認
5. **境界値テスト**: 極端な値での動作確認

## 品質管理

### 品質ゲート

新機能・変更は以下の品質ゲートを通過する必要があります：

```bash
# 1. 全テスト通過
make test
# ✅ 548/548 tests passed, 95%+ coverage

# 2. コード品質チェック
make lint  
# ✅ flake8: no errors, mypy: no errors

# 3. セキュリティチェック
make security
# ✅ bandit: no high-risk issues

# 4. 複雑度チェック  
make complexity
# ✅ Radon average grade: A (< 10)

# 5. フォーマットチェック
make format-check
# ✅ black, isort: no changes needed
```

### コード複雑度管理

- **関数複雑度**: C評価（15以上）で分割検討
- **平均複雑度**: A評価（10未満）維持
- **クラス複雑度**: B評価（20未満）推奨
- **ファイル複雑度**: 500行以下推奨

### セキュリティ要件

- **except文**: 空のexcept禁止、必ずログ記録
- **入力検証**: 全外部入力の検証実装
- **機密情報**: ハードコード禁止、環境変数使用
- **依存関係**: 既知脆弱性なしの確認

## コードスタイル

### PEP 8準拠

```python
# ✅ 良い例
def calculate_transfer_rate(data_size: int, duration: float) -> float:
    """データ転送速度を計算する。
    
    Args:
        data_size: データサイズ（バイト）
        duration: 転送時間（秒）
        
    Returns:
        転送速度（バイト/秒）
        
    Raises:
        ValueError: durationが0以下の場合
    """
    if duration <= 0:
        raise ValueError("転送時間は正の値である必要があります")
    return data_size / duration

# ❌ 悪い例  
def calc(d,t):
    return d/t  # エラーハンドリングなし、型注釈なし、ドキュメントなし
```

### 型注釈規約

```python
from typing import Optional, List, Dict, Any
from pathlib import Path

# 関数の型注釈
def process_command(
    command: str, 
    args: List[str], 
    config: Optional[Dict[str, Any]] = None
) -> bool:
    """コマンド処理を実行する。"""
    pass

# クラスの型注釈
class ConnectionManager:
    def __init__(self, uri: str) -> None:
        self._connection: Optional[BaseConnection] = None
        self._config: Dict[str, Any] = {}
```

### Enum設計規約

```python
from enum import Enum
from typing import Tuple

class MSXMode(Enum):
    """MSX動作モード。"""
    
    BASIC = ("basic", "Ok", "BASICモード")
    DOS = ("dos", r"[A-Z][:>]", "DOS/CMDモード")  
    UNKNOWN = ("unknown", "", "不明モード")
    
    def __init__(self, mode: str, pattern: str, description: str) -> None:
        self.mode = mode
        self.pattern = pattern  
        self.description = description
    
    @property
    def value(self) -> str:
        """モード名を返す。"""
        return self.mode
```

## 貢献方法

### 1. Issue作成

```markdown
## 概要
機能の概要や問題の説明

## 期待する動作
どのような動作を期待するか

## 現在の動作  
現在どのような動作をするか

## 環境
- OS: macOS 14.5
- Python: 3.11.9
- msx-serial: v0.2.17.dev8
```

### 2. Pull Request作成

```bash
# 開発ブランチ作成
git checkout -b feature/new-command

# 開発・テスト実装
# ... coding ...

# 品質チェック実行
make check-all

# コミット  
git add .
git commit -m "新機能: @uploadコマンドの追加

- base64エンコーディングによるバイナリファイル転送
- プログレスバー表示機能  
- エラーハンドリング強化
- テストカバレッジ100%"

# プッシュ・PR作成
git push origin feature/new-command
```

### 3. コミットメッセージ規約

```
種類: 簡潔な変更内容（50文字以内）

詳細な変更内容の説明：
- 追加した機能
- 修正した問題
- 影響範囲
- 注意事項

関連Issue: #123
```

**種類の例:**
- `機能`: 新機能追加
- `修正`: バグ修正  
- `改善`: 既存機能の改善
- `テスト`: テスト追加・修正
- `ドキュメント`: ドキュメント更新
- `リファクタリング`: コード整理

## リリース管理

### バージョニング

Semantic Versioning (SemVer) に準拠：

- **MAJOR**: 破壊的変更 (例: 2.0.0)
- **MINOR**: 後方互換性ありの機能追加 (例: 1.1.0)  
- **PATCH**: 後方互換性ありのバグ修正 (例: 1.0.1)
- **PRE-RELEASE**: 開発版 (例: 1.0.0.dev1)

### リリース手順

```bash
# 1. リリース準備確認
make release-check

# 2. バージョン確認  
python setup.py --version

# 3. ビルド実行
make build

# 4. テスト配布（オプション）
pip install dist/msx_serial-*.whl

# 5. PyPIアップロード（メンテナー限定）
twine upload dist/*
```

## 高度な開発機能

### プロファイリング

```python
from msx_serial.common.profiler import profiler

@profiler.measure_time
def heavy_computation() -> str:
    """重い処理の実行時間を測定。"""
    # 重い処理
    return "result"

# 使用例
result = heavy_computation()
print(f"実行時間: {profiler.get_stats()}")
```

### キャッシュ活用

```python  
from msx_serial.common.cache_manager import CacheManager

cache = CacheManager()

@cache.cached(ttl=300)  # 5分間キャッシュ
def expensive_operation(param: str) -> str:
    """高コストな処理結果をキャッシュ。"""
    # 重い処理
    return f"processed_{param}"
```

### 設定管理

```python
from msx_serial.common.config_manager import ConfigManager

config = ConfigManager()

# 設定取得
theme = config.get("display.theme", "dark")

# 設定変更
config.set("performance.delay", 0.01)

# 設定検証
config.validate_value("performance.delay", 0.01)
```

## トラブルシューティング

### 開発環境の問題

**import エラーが発生する場合:**
```bash
# editable installの再実行
pip uninstall msx-serial
pip install -e .[dev]
```

**テストが失敗する場合:**
```bash
# キャッシュクリア
pytest --cache-clear

# 仮想環境の再作成
deactivate
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -e .[dev]
```

### 品質チェックの問題

**flake8エラーの修正:**
```bash
# 自動修正可能な問題
autopep8 --in-place --aggressive file.py

# 手動修正が必要な問題
flake8 file.py --show-source
```

**mypy エラーの修正:**
```bash
# 型注釈の追加・修正
mypy file.py --show-error-codes
```

### パフォーマンス問題

**メモリ使用量の監視:**
```bash
# メモリプロファイリング
python -m memory_profiler script.py

# プロファイルの詳細分析
python -m cProfile -o profile.stats script.py
python -c "import pstats; pstats.Stats('profile.stats').sort_stats('time').print_stats(10)"
```

## AI開発の透明性

このプロジェクトではAIによるコード生成を活用しており、以下の原則に従います：

- **透明性**: AI貢献度の適切な記録・開示
- **品質保証**: 人間による添削・調整の実施
- **一貫性**: 既存コードスタイルとの整合性確保
- **測定可能性**: 品質向上への貢献の定量的測定

### AI貢献度の記録

```python
# ファイルヘッダーでAI貢献度を明記
"""
MSXシリアルターミナル - コマンドハンドラー

このファイルの開発にはAIアシスタントが貢献しています：
- コード生成: 70%
- 人間による添削: 30%
- 最終品質保証: 人間による確認済み
"""
```

## ライセンスと著作権

- **ライセンス**: MIT License
- **著作権**: プロジェクト貢献者
- **サードパーティ**: 依存関係のライセンスを尊重
- **AI生成コード**: オープンソースライセンス下で公開

### 依存関係のライセンス確認

```bash
# ライセンス一覧の確認
pip-licenses --format=table --with-license-file

# 非互換ライセンスの検出
pip-licenses --fail-on="GPL"
```

貢献いただく際は、コードがMITライセンスと互換性があることを確認してください。 