# MSXシリアルターミナル

[![CI](https://github.com/yamamo-to/msx-serial/actions/workflows/ci.yml/badge.svg)](https://github.com/yamamo-to/msx-serial/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/msx-serial.svg)](https://badge.fury.io/py/msx-serial)

シリアル接続やTelnetを通じてMSXと通信するための高性能ターミナルプログラムです。リアルタイム文字表示、自動モード検出、日本語テキストサポートを特徴としています。

## 特徴

✨ **リアルタイム通信**: 文字単位での高速MSX通信に最適化  
🔍 **自動モード検出**: BASICとMSX-DOSモードを自動検出  
🌐 **複数接続タイプ**: シリアル、Telnet、ダミー接続に対応  
📝 **日本語テキストサポート**: MSX文字エンコーディングの完全サポート  
📁 **ファイル転送**: BASICプログラムアップロードとテキストファイル貼り付け機能  
🎯 **スマート補完**: コンテキスト対応のコマンド補完  
🎨 **カラー表示**: 美しいカラーターミナル出力  
⚡ **高いテストカバレッジ**: 95%のコードカバレッジと455のテストケース

## AI貢献について

🤖 **このリポジトリはAI（Claude）が約90%のコードを記述しています**

このプロジェクトは人間の初期実装とAIによる大幅な構造改善・機能追加の協働プロジェクトです：

- **総Pythonコード**: 11,195行
- **AI貢献**: 約10,000行（89.7%）
- **主要AI貢献**: 構造設計、テストスイート、セキュリティ改善、パフォーマンス最適化
- **人間貢献**: 初期コンセプト、要件定義、品質管理、プロジェクト管理

AIと人間のコラボレーションにより、高品質で保守性の高いコードベースを実現しています。

## インストール

```bash
pip install msx-serial
```

## 使用方法

### 基本接続

```bash
# シリアル接続
msx-serial COM1                                    # Windows
msx-serial /dev/ttyUSB0                           # Linux
msx-serial /dev/tty.usbserial-12345678901         # macOS

# パラメータ付きシリアル接続
msx-serial 'serial:///dev/ttyUSB0?baudrate=115200&bytesize=8&parity=N&stopbits=1'

# Telnet接続
msx-serial 192.168.1.100:2223
msx-serial telnet://192.168.1.100:2223

# ダミー接続（テスト用）
msx-serial dummy://
```

### コマンドラインオプション

```
使用方法: msx-serial [-h] [--encoding ENCODING] [--debug] connection

MSXシリアルターミナル

位置引数:
  connection           接続文字列 (例: COM4, /dev/ttyUSB0, 192.168.1.100:2223, dummy://)

オプション:
  -h, --help           ヘルプメッセージを表示して終了
  --encoding ENCODING  テキストエンコーディング (デフォルト: msx-jp)
  --debug              デバッグモードを有効化
```

### 特殊コマンド

| コマンド | 説明 | 利用可能モード |
|---------|------|---------------|
| `@paste` | テキストファイル内容を貼り付け | BASICモードのみ |
| `@upload` | ファイルをBASICプログラムとしてアップロード | BASICモードのみ |
| `@cd` | 現在のディレクトリを変更 | 全モード |
| `@encode` | テキストエンコーディングを設定 | 全モード |
| `@help` | コマンドヘルプを表示 | 全モード |
| `@mode` | MSXモードを表示/強制変更 | 全モード |
| `@perf` | パフォーマンス統計を表示 | 全モード |
| `@exit` | プログラムを終了 | 全モード |

詳細なコマンド使用方法は `@help` をご覧ください。

### MSXモード検出

ターミナルは自動的にMSX動作モードを検出して動作を調整します：

- **BASICモード**: `Ok` プロンプトで検出 - ファイルアップロード/貼り付けコマンドが有効
- **MSX-DOSモード**: `A>`, `B>`, `C>` 等のプロンプトで検出  
- **不明モード**: モードが検出されるまでのデフォルト状態

### モードコマンド

```bash
@mode          # 現在のMSXモードを表示
@mode basic    # BASICモードに強制変更
@mode dos      # MSX-DOSモードに強制変更  
@mode unknown  # 不明モードにリセット
```

## 接続URI形式

### シリアル接続

```bash
# 基本形式
serial:///dev/ttyUSB0

# パラメータ付き
serial:///dev/ttyUSB0?baudrate=115200&bytesize=8&parity=N&stopbits=1&timeout=1
```

**サポートされるパラメータ:**
- `baudrate`: ボーレート (デフォルト: 9600)
- `bytesize`: データビット (5, 6, 7, 8 - デフォルト: 8) 
- `parity`: パリティ (N, E, O, M, S - デフォルト: N)
- `stopbits`: ストップビット (1, 1.5, 2 - デフォルト: 1)
- `timeout`: 読み取りタイムアウト（秒）
- `xonxoff`: ソフトウェアフロー制御 (true/false)
- `rtscts`: ハードウェアフロー制御 (true/false)
- `dsrdtr`: DSR/DTRフロー制御 (true/false)

### Telnet接続

```bash
# 基本形式
telnet://hostname:port

# 例
telnet://192.168.1.100:2223
telnet://msx.local:2223
```

## テキストエンコーディング対応

MSXテキスト用にサポートされるエンコーディング:
- `msx-jp`: 日本語MSXエンコーディング (デフォルト)
- `msx-intl`: 国際MSXエンコーディング
- `msx-br`: ブラジルMSXエンコーディング  
- `shift-jis`: Shift-JISエンコーディング
- `utf-8`: UTF-8エンコーディング

エンコーディング変更: `@encode msx-jp`

## アーキテクチャ

### コアコンポーネント

- **MSXSession**: 高速応答メインターミナルセッション
- **ConnectionManager**: 統合接続処理 (Serial/Telnet/Dummy)
- **MSXProtocolDetector**: プロンプトからの自動モード検出
- **DataProcessor**: 高速表示リアルタイムデータ処理
- **CommandCompleter**: コンテキスト対応コマンド補完
- **FileTransferManager**: ファイルアップロードと貼り付け操作

### プロジェクト構造

```
msx_serial/
├── core/              # コアターミナルセッションとデータ処理
├── connection/        # 接続実装 (Serial/Telnet/Dummy)
├── protocol/          # MSXプロトコル検出とモード管理
├── display/           # ターミナル表示ハンドラー
├── completion/        # コマンド補完システム
├── commands/          # 特殊コマンドハンドラー
├── io/                # 入出力調整
├── transfer/          # ファイル転送機能
├── common/            # 共有ユーティリティとカラー出力
├── data/              # 静的データ (コマンドリスト、キーワード)
└── man/               # マニュアルページ（BASICコマンド説明）
```

### 主要設計原則

1. **高速応答**: リアルタイムMSX通信のための文字単位処理
2. **自動適応**: モード検出によってターミナル動作をMSX状態に適応
3. **統合接続**: 複数接続タイプに対する単一インターフェース
4. **コンテキスト認識**: 現在のMSXモードにコマンドと補完が適応
5. **堅牢なエラー処理**: 接続とエンコーディング問題の優雅な処理

## テスト

プロジェクトには包括的なテストスイートが含まれています：

```bash
# 全テスト実行
python -m pytest

# カバレッジ付き実行
python -m pytest --cov=msx_serial --cov-report=term-missing

# 特定テスト実行
python -m pytest tests/test_completion.py
```

**テスト統計:**
- 総テスト数: 455件
- コードカバレッジ: 95%
- テスト成功率: 100%

## 開発

### 要件

- Python 3.9+
- `pyproject.toml` に記載された依存関係

### 開発環境セットアップ

```bash
# リポジトリクローン
git clone https://github.com/yamamo-to/msx-serial
cd msx-serial

# 仮想環境作成
python -m venv venv
source venv/bin/activate  # Linux/macOS
# または
.\venv\Scripts\activate   # Windows

# 開発モードでインストール
pip install -e . --use-pep517
```

### コード品質

```bash
# コードフォーマット
black msx_serial/ tests/

# リンターチェック
flake8 msx_serial/ tests/

# 型チェック
mypy msx_serial/

# バージョン同期チェック
python update_readme_version.py
```

### 自動化

プロジェクトには開発タスクを自動化するMakefileが含まれています：

```bash
# 利用可能なコマンドを表示
make help

# リリース準備（フォーマット、テスト、バージョン同期）
make release

# 個別タスク
make test           # テスト実行
make format         # コードフォーマット
make lint           # 品質チェック
make check-version  # README.mdのバージョン同期確認
```

**自動バージョン同期**: `update_readme_version.py`スクリプトが`_version.py`からバージョンを読み取り、README.mdの更新履歴を自動的に同期します。これにより、バージョンの不整合を防げます。

### リリースプロセス

安全なリリースのために2つの方法を提供しています：

#### 1. 対話的リリース（推奨）

```bash
make release-interactive
```

このコマンドは以下を実行します：
- バージョン確認と開発バージョン警告
- Git状態チェック
- コードフォーマット、型チェック、テスト実行
- README.mdバージョン同期
- TestPyPIアップロード（オプション）
- 本番PyPIアップロード（二重確認付き）

#### 2. 手動リリース

```bash
# 1. リリース準備
make release

# 2. TestPyPIでテスト（推奨）
make upload-test

# 3. 本番PyPIリリース
make upload-prod
```

#### 安全機能

- **二重確認**: 本番アップロード前に複数回確認
- **TestPyPI**: 本番前のテスト環境でのアップロード
- **Git状態チェック**: コミットされていない変更の警告
- **開発バージョン警告**: dev版リリース時の注意喚起
- **自動バージョン同期**: README.mdとの整合性確保

## ライセンス

このプロジェクトはMITライセンスのもとで公開されています。

## 貢献

プルリクエストや課題報告を歓迎します。貢献前にテストを実行し、コード品質チェックを通過させてください。

## 謝辞

このプロジェクトは以下の素晴らしいリソースから多大な恩恵を受けています：

- **MSX0からコンソール経由でのファイル転送技術**: [@enu7](https://qiita.com/enu7)による[base64を使ったファイル転送実装](https://qiita.com/enu7/items/2fd917c41514f6ea71b1)から重要なインスピレーションを得ました
- **MSX BASICコマンドリファレンス**: [fu-sen/MSX-BASIC](https://github.com/fu-sen/MSX-BASIC)プロジェクトからBASICコマンドの包括的な情報を参照させていただきました

これらのリソースなしには、本プロジェクトの高品質なMSX通信とファイル転送機能の実現は困難でした。関係者の皆様に深く感謝いたします。

## 更新履歴

### v0.2.17.dev7
- 正規表現を使ったプロンプトパターンの最適化
- A-Zの全ドライブレター対応（A>-Z>およびA:>-Z:>）
- 統一された正規表現パターンによるパフォーマンス向上
- より保守しやすいプロンプト検出アルゴリズム
- mypyでの型チェック完全通過とblackフォーマット適用

### v0.2.16.dev2
- 包括的なテストスイート実装（455テスト、95%カバレッジ）
- blackによるコードフォーマット統一
- 不要コードの削除とクリーンアップ
- 日本語ドキュメント統一

### 主要機能
- 高速応答MSX通信
- 自動モード検出
- ファイル転送機能
- 日本語テキストサポート
- 包括的テストカバレッジ
