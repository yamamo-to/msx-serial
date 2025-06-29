# MSXシリアルターミナル

[![CI](https://github.com/yamamo-to/msx-serial/actions/workflows/ci.yml/badge.svg)](https://github.com/yamamo-to/msx-serial/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/msx-serial.svg)](https://badge.fury.io/py/msx-serial)

シリアル接続やTelnetを通じてMSXと通信するための高性能ターミナルプログラムです。リアルタイム文字表示、自動モード検出、日本語テキストサポートを特徴としています。

## 📖 ドキュメント一覧

- [🚀 クイックスタート](README.md) - 基本的な使い方 **(このページ)**
- [📋 詳細ガイド](docs/USAGE.md) - 高度な機能と設定
- [🔧 開発ガイド](docs/DEVELOPMENT.md) - 開発・貢献方法

---

## ✨ 特徴

✨ **リアルタイム通信**: 文字単位での高速MSX通信に最適化  
🔍 **自動モード検出**: BASICとMSX-DOSモードを自動検出  
🌐 **複数接続タイプ**: シリアル、Telnet、ダミー接続に対応  
📝 **日本語テキストサポート**: MSX文字エンコーディングの完全サポート  
📁 **ファイル転送**: BASICプログラムアップロードとテキストファイル貼り付け機能  
🎯 **スマート補完**: コンテキスト対応のコマンド補完  
📖 **MSX BASICヘルプ**: 160+のMSX BASICコマンドリファレンス内蔵  
📂 **DOSファイル補完**: DIRコマンド自動キャッシュによるファイル名補完  
⚡ **高いテストカバレッジ**: 95%のコードカバレッジと598のテストケース

## 🤖 AI貢献について

**このリポジトリはAI（Claude）が約90%のコードを記述しています**

このプロジェクトは人間の初期実装とAIによる大幅な構造改善・機能追加の協働プロジェクトです：

- **総Pythonコード**: 12,200行
- **AI貢献**: 約11,000行（90.2%）
- **主要AI貢献**: 構造設計、テストスイート、セキュリティ改善、パフォーマンス最適化
- **人間貢献**: 初期コンセプト、要件定義、品質管理、プロジェクト管理

AIと人間のコラボレーションにより、高品質で保守性の高いコードベースを実現しています。

## 📦 インストール

```bash
pip install msx-serial
```

## 🚀 クイックスタート

### 基本接続

```bash
# シリアル接続
msx-serial COM1                                    # Windows
msx-serial /dev/ttyUSB0                           # Linux
msx-serial /dev/tty.usbserial-12345678901         # macOS

# Telnet接続
msx-serial 192.168.1.100:2223

# ダミー接続（テスト用）
msx-serial dummy://
```

### 基本的な特殊コマンド

```bash
@help                # 全コマンドのヘルプを表示
@help PRINT          # MSX BASICコマンドのヘルプ
@paste myfile.bas    # テキストファイルをMSXに貼り付け
@upload program.bas  # BASICプログラムをアップロード
@mode               # 現在のMSXモードを表示
@refresh            # DOSファイル補完キャッシュを更新
@exit               # プログラム終了
```

### MSX BASICヘルプ機能

160以上のMSX BASICコマンドの詳細なヘルプが利用可能：

```bash
@help ABS           # 絶対値関数
@help PRINT         # 出力コマンド  
@help CALL MUSIC    # MSX-MUSIC初期化
@help _MUSIC        # 短縮形（CALLコマンドと同等）
```

### DOSファイル補完機能

MSX-DOSモードでファイル名の自動補完が利用可能：

```bash
# DIRコマンドを実行すると自動的にキャッシュが更新される
DIR

# ファイル名補完（Tabキー）
TYPE <Tab>          # ファイル名を補完
COPY <Tab>          # ファイル名を補完
DEL <Tab>           # ファイル名を補完

# 手動キャッシュ更新
@refresh            # DIRコマンドを実行してキャッシュを更新
```

## 📋 主要コマンド一覧

| コマンド | 説明 | 利用可能モード |
|---------|------|---------------|
| `@paste` | テキストファイル内容を貼り付け | BASICモードのみ |
| `@upload` | ファイルをBASICプログラムとしてアップロード | BASICモードのみ |
| `@help` | MSX BASICコマンドヘルプ表示 | 全モード |
| `@mode` | MSXモードを表示/強制変更 | 全モード |
| `@encode` | テキストエンコーディングを設定 | 全モード |
| `@perf` | パフォーマンス統計を表示 | 全モード |
| `@refresh` | DOSファイル補完キャッシュを更新 | DOSモードのみ |
| `@cd` | 現在のディレクトリを変更 | 全モード |
| `@exit` | プログラムを終了 | 全モード |

詳細なコマンド使用方法は **[📋 詳細ガイド](docs/USAGE.md)** をご覧ください。

## 🔧 コマンドラインオプション

```bash
msx-serial [-h] [--encoding ENCODING] [--debug] connection

オプション:
  -h, --help           ヘルプメッセージを表示
  --encoding ENCODING  テキストエンコーディング (デフォルト: msx-jp)
  --debug              デバッグモードを有効化
```

## 🏗️ アーキテクチャ概要

### 主要コンポーネント

- **MSXSession**: 高速応答メインターミナルセッション
- **ConnectionManager**: 統合接続処理 (Serial/Telnet/Dummy)
- **MSXProtocolDetector**: プロンプトからの自動モード検出
- **CommandCompleter**: コンテキスト対応コマンド補完
- **FileTransferManager**: ファイルアップロードと貼り付け操作

詳細なアーキテクチャは **[🔧 開発ガイド](docs/DEVELOPMENT.md)** をご参照ください。

## 🧪 テスト

```bash
# 基本テスト実行
pip install -e .[dev]
pytest

# カバレッジ付き実行
pytest --cov=msx_serial --cov-report=html
```

**テスト統計:**
- 総テスト数: 598件
- コードカバレッジ: 95%
- テスト成功率: 100%

## 🤝 貢献

プルリクエストや課題報告を歓迎します。開発方法は **[🔧 開発ガイド](docs/DEVELOPMENT.md)** をご確認ください。

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

## 📄 ライセンス

このプロジェクトはMITライセンスのもとで公開されています。

## 🙏 謝辞

このプロジェクトは以下の素晴らしいリソースから多大な恩恵を受けています：

- **MSX0からコンソール経由でのファイル転送技術**: [@enu7](https://qiita.com/enu7)による[base64を使ったファイル転送実装](https://qiita.com/enu7/items/2fd917c41514f6ea71b1)
- **MSX BASICコマンドリファレンス**: [fu-sen/MSX-BASIC](https://github.com/fu-sen/MSX-BASIC)プロジェクト

関係者の皆様に深く感謝いたします。

## 📈 更新履歴

### v0.2.20（最新）
- **DIRコマンド自動キャッシュ機能**: DIRコマンド実行時に自動的にファイル補完キャッシュを更新
- **DOSファイル補完機能**: MSX-DOSモードでTabキーによるファイル名自動補完
- **@setfilesコマンド削除**: 手動設定コマンドを削除し、自動化を実現
- **DataProcessor拡張**: DIR出力の自動収集・解析機能を追加
- **品質ゲート完全通過**: flake8・mypy・bandit・Radon全クリア

### v0.2.19
- テスト失敗修正完了：全598テスト正常パス
- テストカバレッジ95%達成（.cursorules要件クリア）
- BaseCompleterとMSXヘルプテストの品質向上
- AI貢献度90.2%に向上（+1,000行のテスト追加）
- 品質ゲート完全通過（flake8・mypy・bandit・Radon全クリア）

### v0.2.17.dev8
- 「@help ABS」MSX BASICコマンドヘルプ機能を復旧・実装
- 160以上のMSX BASICコマンドリファレンスを内蔵
- CALL系コマンドのアンダースコア記法サポート
- 複雑度C評価関数のリファクタリング完了
- テストカバレッジ87%到達、548テスト全通過

詳細な更新履歴は **[📋 詳細ガイド](docs/USAGE.md#更新履歴)** をご覧ください。
