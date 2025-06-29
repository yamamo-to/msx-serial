# MSXシリアルターミナル - 開発ガイド

📖 **ガイド一覧**
- [🚀 クイックスタート](../README.md) - 基本的な使い方
- [📋 詳細ガイド](USAGE.md) - 高度な機能と設定
- [🔧 開発ガイド](DEVELOPMENT.md) - 開発・貢献方法 **(このページ)**

---

## 🏗️ アーキテクチャ概要

### 主要コンポーネント

- **MSXSession**: 高速応答メインターミナルセッション
- **ConnectionManager**: 統合接続処理 (Serial/Telnet/Dummy)
- **MSXProtocolDetector**: プロンプトからの自動モード検出
- **CommandCompleter**: コンテキスト対応コマンド補完
- **FileTransferManager**: ファイルアップロードと貼り付け操作

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

## 🧪 テスト

```bash
# 基本テスト実行
pip install -e .[dev]
pytest

# カバレッジ付き実行
pytest --cov=msx_serial --cov-report=html
```

**テスト統計:**
- 総テスト数: 718件
- コードカバレッジ: 95%
- テスト成功率: 100%

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

## 🤝 貢献

プルリクエストや課題報告を歓迎します。

### 品質要件

新機能追加・変更時は以下の品質要件を満たしてください：

```bash
make check-all       # 全品質チェック実行
make test           # テストカバレッジ95%以上（現在95%達成）
make lint           # flake8・mypy全エラー解消  
make security       # bandit高リスク問題なし
make complexity     # Radon平均A評価
make format         # black・isortフォーマット適用
```

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

## 品質管理

### 品質ゲート

新機能・変更は以下の品質ゲートを通過する必要があります：

```bash
# 1. 全テスト通過
make test
# ✅ 718/718 tests passed, 95%+ coverage

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
    """
    if duration <= 0:
        raise ValueError("転送時間は正の値である必要があります")
    
    return data_size / duration


# ❌ 悪い例
def calc_rate(ds,dur):
    return ds/dur
```

### 型注釈

```python
# ✅ 良い例
from typing import Optional, List, Dict, Any

def process_data(
    data: List[str], 
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, int]:
    """データを処理して結果を返す。"""
    pass


# ❌ 悪い例
def process_data(data, config=None):
    pass
```

### ドキュメント

```python
# ✅ 良い例
class FileTransferManager:
    """ファイル転送を管理するクラス。
    
    シリアル接続を通じてMSXにファイルを転送する機能を提供します。
    
    Attributes:
        connection: MSXとの接続オブジェクト
        cache: 転送キャッシュ
    """
    
    def __init__(self, connection: Connection) -> None:
        """FileTransferManagerを初期化する。
        
        Args:
            connection: MSXとの接続オブジェクト
        """
        self.connection = connection
        self.cache: Dict[str, Any] = {}
```

## 📄 ライセンス

このプロジェクトはMITライセンスのもとで公開されています。

## 🙏 謝辞

このプロジェクトは以下の素晴らしいリソースから多大な恩恵を受けています：

- **MSX0からコンソール経由でのファイル転送技術**: [@enu7](https://qiita.com/enu7)による[base64を使ったファイル転送実装](https://qiita.com/enu7/items/2fd917c41514f6ea71b1)
- **MSX BASICコマンドリファレンス**: [fu-sen/MSX-BASIC](https://github.com/fu-sen/MSX-BASIC)プロジェクト

関係者の皆様に深く感謝いたします。 