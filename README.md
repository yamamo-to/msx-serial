# MSXシリアルターミナル

[![CI](https://github.com/yamamo-to/msx-serial/actions/workflows/ci.yml/badge.svg)](https://github.com/yamamo-to/msx-serial/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/msx-serial.svg)](https://badge.fury.io/py/msx-serial)

MSXとのシリアル通信またはtelnet接続を行うターミナルプログラムです。日本語文字の送受信やファイル転送機能を備えています。

## インストール

```bash
pip install msx-serial
```

## 使い方

### 基本的な使い方

```bash
# シリアル接続
msx-serial COM1
msx-serial /dev/ttyUSB0
msx-serial /dev/tty.usbserial-12345678901
msx-serial 'serial:///dev/tty.usbserial-12345678901?baudrate=115200'

# Telnet接続
msx-serial 192.168.86.30:2223
msx-serial telnet://192.168.86.30:2223
```

### コマンドラインオプション

```
usage: msx-serial [-h] [--encoding ENCODING] connection

MSXシリアルターミナル

positional arguments:
  connection           接続先 (例: COM1, /dev/ttyUSB0, 192.168.1.100:2223, telnet://192.168.1.100:2223, serial:///COM1?baudrate=9600)

options:
  -h, --help           ヘルプメッセージを表示して終了
  --encoding ENCODING  エンコーディング (デフォルト: msx-jp)
```

### 特殊コマンド

- `@paste`: テキストファイルを読み込んで貼り付け
- `@upload`: ファイルをアップロード
- `@cd`: カレントディレクトリを変更
- `@encode`: 送受信時の文字コードを指定（msx-jp, msx-intl, msx-br, shift-jis）
- `@help`: コマンドのヘルプを表示
- `@exit`: プログラムを終了

特殊コマンドの詳細な使用方法は `@help` コマンドで確認できます。

## 主な機能

- MSXとのシリアル通信
- 日本語文字の送受信（MSX文字コード対応）
- ファイル送信機能
- コマンド補完機能
- カラー表示

## 文字コード対応

- UTF-8からMSX文字コードへの変換
- MSX文字コードからUTF-8への変換
- グラフィックキャラクタ対応
- 濁点・半濁点対応

## 開発者向け情報

### 必要条件

- Python 3.9以上
- 必要なパッケージ（pyproject.tomlに記載）

### 開発環境のセットアップ

```bash
# リポジトリのクローン
git clone https://github.com/yamamo-to/msx-serial
cd msx-serial

# 仮想環境の作成と有効化
python -m venv venv
.\venv\Scripts\activate  # Windowsの場合
source venv/bin/activate  # Linuxの場合

# 開発モードでインストール
pip install -e . --use-pep517
```

### プロジェクト構造

```
msx_serial/
├── connection/    # 通信関連のモジュール
├── completion/    # コマンド補完機能
├── data/          # データファイル（文字コード変換テーブルなど）
├── input/         # 入力処理関連
├── transfer/      # ファイル転送機能
├── ui/            # ユーザーインターフェース
└── man/           # マニュアル
```

### 主要モジュールの説明

- `connection/`: シリアル通信とtelnet接続の実装
- `completion/`: コマンド補完機能の実装
- `input/`: キー入力処理とコマンド解析
- `transfer/`: ファイル転送機能の実装
- `ui/`: ターミナルUIの実装
- `data/`: 文字コード変換テーブルなどの静的データ

### 依存関係

- Python 3.9以上
- colorama: ターミナルのカラー表示
- prompt-toolkit: 対話型コマンドラインインターフェース
- pyserial: シリアル通信
- PyYAML: YAMLファイルの読み込み
- chardet: 文字エンコーディングの検出
- msx-charset: MSX文字コードの変換

## 謝辞

BASE64によるアップロードは下記の記事を参考にさせていただきました。
https://qiita.com/enu7/items/23cab122141fb8d07c6d

MSX-BASICのコマンドリファレンスは下記のリポジトリをAIによりman形式に変換させていただきました。
https://github.com/fu-sen/MSX-BASIC

## ライセンス

MIT License
