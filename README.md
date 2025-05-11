# MSX Serial Terminal

MSXとのシリアル通信を行うターミナルプログラムです。

## 機能

- MSXとのシリアル通信
- 日本語文字の送受信（MSX文字コード対応）
- ファイル送信機能
- コマンド補完機能
- カラー表示

## 必要条件

- Python 3.9以上
- 必要なパッケージ（pyproject.tomlに記載）

## インストール方法

```bash
# パッケージのインストール
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

```bash
# 基本的な使用方法（--portは必須）
msx-serial --port COM3  # Windowsの場合
python -m msx_serial --port COM3  # 開発モードの場合

msx-serial --port /dev/tty.usbserial  # Linuxの場合
python -m msx_serial --port /dev/tty.usbserial  # 開発モードの場合

# ボーレートを指定
msx-serial --port COM3 --baudrate 115200  # Windowsの場合
python -m msx_serial --port COM3 --baudrate 115200  # 開発モードの場合

msx-serial --port /dev/tty.usbserial --baudrate 115200  # Linuxの場合
python -m msx_serial --port /dev/tty.usbserial --baudrate 115200  # 開発モードの場合
```

### コマンドラインオプション

- `--port`: シリアルポート（必須）
  - Windowsの場合: `COM3`など
  - Linuxの場合: `/dev/tty.usbserial`など
- `--baudrate`: ボーレート（デフォルト: 115200）
- `--encoding`: エンコーディング（デフォルト: msx-jp）

### 開発モードでの実行

開発モードで実行する場合は、以下の手順に従ってください：

1. リポジトリをクローン
```bash
git clone https://github.com/yamamo-to/msx-serial
cd msx-serial
```

2. 仮想環境を作成して有効化
```bash
python -m venv venv
.\venv\Scripts\activate  # Windowsの場合
source venv/bin/activate  # Linuxの場合
```

3. 依存関係をインストール
```bash
pip install -r requirements.txt
```

4. 開発モードでインストール
```bash
pip install -e . --use-pep517
```

5. プログラムを実行
```bash
python -m msx_serial
```

### シリアルポートの確認方法

#### Windows
1. デバイスマネージャーを開く
2. 「ポート（COMとLPT）」を展開
3. 「USB Serial Port (COM3)」などのポート名を確認

#### Linux
1. ターミナルで以下のコマンドを実行
```bash
ls /dev/tty.*
```

### コマンド一覧

- `@file`: ファイルを選択して送信
- `@bytes`: 16進数のバイト列を送信
- `@upload`: ファイルをBase64エンコードしてアップロード
- `@exit`: プログラムを終了

### 特殊キー

- `^C`: Ctrl+Cを送信
- `^[`: ESCキーを送信

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