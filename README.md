# MSXシリアルターミナル

[![CI](https://github.com/yamamo-to/msx-serial/actions/workflows/ci.yml/badge.svg)](https://github.com/yamamo-to/msx-serial/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/msx-serial.svg)](https://badge.fury.io/py/msx-serial)

シリアル接続やTelnetを通じてMSXと通信するための高性能ターミナルプログラムです。リアルタイム文字表示、自動モード検出、日本語テキストサポートを特徴としています。

## 📖 ドキュメント一覧

- [🚀 クイックスタート](README.md) - 基本的な使い方 **(このページ)**
- [📋 詳細ガイド](docs/USAGE.md) - 高度な機能と設定
- [🔧 開発ガイド](docs/DEVELOPMENT.md) - 開発・貢献方法
- [🤖 AI貢献度](docs/AI_CONTRIBUTION.md) - AI開発の透明性
- [📈 更新履歴](docs/CHANGELOG.md) - バージョン履歴

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
📄 **BASICファイル補完**: FILESコマンド自動キャッシュによる.BASファイル優先補完  
⚡ **高いテストカバレッジ**: 95%のコードカバレッジと722のテストケース  
🤖 **AI開発支援**: 開発効率向上のためのAI貢献度管理

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

# A>プロンプトでの実行ファイル優先補完
A> <Tab>            # .COM/.EXE/.BATファイルとディレクトリを優先表示
A>SC<Tab>           # SCANDISK（コマンド）とSC2VIEW.COM（ファイル）を同時表示
```

### BASICファイル補完機能

MSX BASICモードでファイル名の自動補完が利用可能：

```bash
# FILESコマンドを実行すると自動的にキャッシュが更新される
FILES

# ファイル名補完（Tabキー）
RUN <Tab>           # .BASファイルを優先して補完
LOAD <Tab>          # .BASファイルを優先して補完
SAVE <Tab>          # .BASファイルを優先して補完

# 引用符付きで自動補完される
RUN "TEST.BAS"      # 引用符は自動で追加される
```

## 📋 詳細情報

詳細な使用方法、開発方法、AI貢献度については以下のドキュメントをご覧ください：

- **[📋 詳細ガイド](docs/USAGE.md)** - コマンド一覧、高度な機能、トラブルシューティング
- **[🔧 開発ガイド](docs/DEVELOPMENT.md)** - アーキテクチャ、品質管理、貢献方法
- **[🤖 AI貢献度](docs/AI_CONTRIBUTION.md)** - AI開発の透明性と貢献状況
- **[📈 更新履歴](docs/CHANGELOG.md)** - バージョン別の変更点

## 📄 ライセンス

このプロジェクトはMITライセンスのもとで公開されています。

## 🙏 謝辞

このプロジェクトは以下の素晴らしいリソースから多大な恩恵を受けています：

- **MSX0からコンソール経由でのファイル転送技術**: [@enu7](https://qiita.com/enu7)による[base64を使ったファイル転送実装](https://qiita.com/enu7/items/2fd917c41514f6ea71b1)
- **MSX BASICコマンドリファレンス**: [fu-sen/MSX-BASIC](https://github.com/fu-sen/MSX-BASIC)プロジェクト

関係者の皆様に深く感謝いたします。
