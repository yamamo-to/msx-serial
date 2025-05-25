# MSXシリアルターミナル

MSXとのシリアル通信またはtelnet接続を行うターミナルプログラム

## 機能

- MSXとのシリアル通信
- 日本語文字の送受信（MSX文字コード対応）
- ファイル送信機能
- コマンド補完機能
- カラー表示

## 必要条件

- Python 3.9以上
- 必要なパッケージ（pyproject.tomlに記載）

## インストール

```bash
pip install msx-serial
```

## 開発環境のセットアップ

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

## 使用方法

### 基本的な使い方

```bash
# シリアル接続
msx-serial serial:///COM1?baud=9600
msx-serial serial:///dev/ttyUSB0?baud=115200
msx-serial COM1 --baudrate 9600
msx-serial /dev/ttyUSB0 --baudrate 115200

# Telnet接続（URI形式）
msx-serial telnet://192.168.86.30:2223
msx-serial 192.168.86.30:2223
```

### コマンドラインオプション

```
usage: msx-serial [-h] [--baudrate BAUDRATE] [--encoding ENCODING] connection

MSXシリアルターミナル

positional arguments:
  connection           接続先 (例: COM1, /dev/ttyUSB0, 192.168.1.100:2223, telnet://192.168.1.100:2223, serial:///COM1?baud=9600)

options:
  -h, --help           ヘルプメッセージを表示して終了
  --baudrate BAUDRATE  シリアル接続時のボーレート (URI形式で指定する場合は不要)
  --encoding ENCODING  エンコーディング (デフォルト: msx-jp)
```

### 接続先の指定方法

1. URI形式
   - シリアル接続: `serial:///COM1?baud=9600`
   - Telnet接続: `telnet://192.168.1.100:2223`

2. 従来の形式
   - シリアル接続: `COM1` または `/dev/ttyUSB0`
   - Telnet接続: `192.168.1.100:2223`

### 特殊コマンド

- `@paste`: テキストファイルを送信
- `@bytes`: 16進数のバイト列を送信
- `@exit`: 終了
- `@upload`: ファイルをアップロード
- `@cd`: ディレクトリを変更

## 文字コード対応

- UTF-8からMSX文字コードへの変換
- MSX文字コードからUTF-8への変換
- グラフィックキャラクタ対応
- 濁点・半濁点対応

## 依存関係

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

## ライセンス

MIT License