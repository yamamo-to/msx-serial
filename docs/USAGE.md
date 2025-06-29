# MSXシリアルターミナル - 使用ガイド

📖 **ガイド一覧**
- [🚀 クイックスタート](../README.md) - 基本的な使い方
- [📋 詳細ガイド](USAGE.md) - 高度な機能と設定 **(このページ)**
- [🔧 開発ガイド](DEVELOPMENT.md) - 開発・貢献方法

---

## 🚀 基本的な特殊コマンド

```bash
@help                # 全コマンドのヘルプを表示
@help PRINT          # MSX BASICコマンドのヘルプ
@paste myfile.bas    # テキストファイルをMSXに貼り付け
@upload program.bas  # BASICプログラムをアップロード
@mode               # 現在のMSXモードを表示
@exit               # プログラム終了
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
| `@cd` | 現在のディレクトリを変更 | 全モード |
| `@exit` | プログラムを終了 | 全モード |

## 🔧 コマンドラインオプション

```bash
msx-serial [-h] [--encoding ENCODING] [--debug] connection

オプション:
  -h, --help           ヘルプメッセージを表示
  --encoding ENCODING  テキストエンコーディング (デフォルト: msx-jp)
  --debug              デバッグモードを有効化
```

## @helpコマンド - MSX BASICリファレンス

プログラムには160以上のMSX BASICコマンドの詳細なヘルプが内蔵されています：

### 基本的な使用例

```bash
# 一般的なBASICコマンド
@help PRINT          # 数字や文字列の出力
@help ABS            # 絶対値関数
@help FOR            # FORループ
@help INPUT          # キーボード入力

# CALLコマンド系（アンダースコア記法対応）
@help CALL MUSIC     # MSX-MUSIC初期化
@help _MUSIC         # 短縮形（CALLコマンドと同等）
@help CALL PALETTE   # パレット設定
@help _PALETTE       # 短縮形

# ファイル操作コマンド
@help BLOAD          # バイナリファイル読み込み
@help BSAVE          # バイナリファイル保存
@help FILES          # ファイル一覧表示

# グラフィックスコマンド
@help CIRCLE         # 円描画
@help LINE           # 直線描画
@help PAINT          # 塗りつぶし
```

**ヘルプ機能特徴:**
- 📖 **包括的リファレンス**: 160+のMSX BASICコマンド対応
- 🔍 **構造化表示**: 使用法・説明・例・注意を明確に整理
- 📝 **日本語対応**: 完全日本語でのコマンド説明
- ⚡ **高速検索**: コマンド名の大文字・小文字を自動変換
- 🔧 **CALL系サポート**: `@help _MUSIC` = `@help CALL MUSIC`

**リファレンス元**: [fu-sen/MSX-BASIC](https://github.com/fu-sen/MSX-BASIC)プロジェクトの包括的な情報を基に構築

## 📂 DOSファイル補完機能

MSX-DOSモードでファイル名の自動補完が利用可能です：

### 自動キャッシュ更新

```bash
# DIRコマンドを実行すると自動的にキャッシュが更新される
DIR

# ファイル名補完（Tabキー）
TYPE <Tab>          # ファイル名を補完
COPY <Tab>          # ファイル名を補完
DEL <Tab>           # ファイル名を補完
REN <Tab>           # ファイル名を補完
```

### 補完機能の特徴

- **自動キャッシュ更新**: DIRコマンド実行時に自動的にファイル一覧をキャッシュ
- **リアルタイム補完**: Tabキーで即座にファイル名を補完
- **ディレクトリ対応**: ディレクトリ名も補完対象に含む
- **拡張子認識**: ファイルの種類に応じたアイコン表示
- **サイズ表示**: ファイルサイズ情報も表示

### 対応DOSコマンド

以下のDOSコマンドでファイル名補完が利用可能：
- `TYPE` - ファイル内容表示
- `COPY` - ファイルコピー
- `DEL` - ファイル削除
- `REN` - ファイル名変更
- `LOAD` - BASICファイル読み込み
- `SAVE` - BASICファイル保存

## 📄 BASICファイル補完機能

MSX BASICモードでファイル名の自動補完が利用可能です：

### 自動キャッシュ更新

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

### 補完機能の特徴

- **.BASファイル優先**: BASICファイルを優先的に補完候補に表示
- **自動引用符処理**: ファイル名に自動的に引用符を追加
- **FILES出力解析**: FILESコマンドの出力を自動解析してキャッシュ更新
- **複数列対応**: FILES出力の複数列表示にも対応
- **実機エコー除外**: MSX実機のエコーを除外して正確な解析

## MSXモード検出

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

## 高度な機能

### パフォーマンス制御

```bash
@perf stats         # パフォーマンス統計を表示
@perf debug on      # デバッグモードを有効化
@perf debug off     # デバッグモードを無効化
@perf help          # ヘルプを表示
```

### 設定管理

```bash
@config list                        # 全設定項目を表示
@config get display.theme           # 特定設定の確認
@config set performance.delay 0.01  # 設定の変更
@config reset encoding.default      # デフォルト値に戻す
```

## トラブルシューティング

### 接続問題

**シリアル接続できない場合:**
```bash
# デバイスファイルの確認
ls /dev/tty*    # Linux/macOS
ls COM*         # Windows

# 権限の確認（Linux）
sudo usermod -a -G dialout $USER
# ログアウト/ログインが必要

# ボーレート確認
msx-serial '/dev/ttyUSB0?baudrate=9600'
```

**Telnet接続できない場合:**
```bash
# 接続テスト
telnet 192.168.1.100 2223

# ファイアウォール確認
# MSX側のTelnetサーバー設定確認
```

### エンコーディング問題

**文字化けする場合:**
```bash
@encode msx-jp      # 日本語MSX
```

## 謝辞

このプロジェクトは以下の素晴らしいリソースから多大な恩恵を受けています：

- **MSX0からコンソール経由でのファイル転送技術**: [@enu7](https://qiita.com/enu7)による[base64を使ったファイル転送実装](https://qiita.com/enu7/items/2fd917c41514f6ea71b1)から重要なインスピレーションを得ました
- **MSX BASICコマンドリファレンス**: [fu-sen/MSX-BASIC](https://github.com/fu-sen/MSX-BASIC)プロジェクトからBASICコマンドの包括的な情報を参照させていただきました

これらのリソースなしには、本プロジェクトの高品質なMSX通信とファイル転送機能の実現は困難でした。関係者の皆様に深く感謝いたします。

## 更新履歴

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