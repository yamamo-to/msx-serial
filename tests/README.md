# MSXシリアルターミナル テストスイート

## 概要

このディレクトリには、MSXシリアルターミナルプロジェクトの単体試験が含まれています。

## テストファイル

### test_completion.py

補完機能の単体試験です。以下の機能をテストしています：

#### テスト項目

1. **test_dos_mode_at_mode_completion** - DOSモードでの@modeコマンド補完
   - `@`、`@m`、`@mode`の入力に対して適切な補完候補が表示されることを確認

2. **test_basic_mode_at_commands_completion** - BASICモードでの@コマンド補完
   - `@`で始まる特殊コマンドが複数表示されることを確認
   - `@m`で始まる場合はmodeのみが表示されることを確認（重複なし）
   - `@u`で始まる場合はuploadが含まれることを確認

3. **test_dos_mode_dos_commands_completion** - DOSモードでのDOSコマンド補完
   - Dで始まるDOSコマンド（DIR、DEL、DATE）が表示されることを確認
   - BASICコマンドも含まれることを確認

4. **test_basic_mode_basic_commands_completion** - BASICモードでのBASICコマンド補完
   - Pで始まるBASICコマンド（PRINT、PEEK、POKE）が表示されることを確認

5. **test_mode_switching** - モード切り替え機能
   - 初期状態がunknownであることを確認
   - DOS/BASICモードへの切り替えが正常に動作することを確認

6. **test_unknown_mode_completion** - 不明モードでの補完
   - 不明モードでも補完機能が動作することを確認

### test_mode_switching.py

モード切り替え機能の単体試験です。以下の機能をテストしています：

#### テスト項目

1. **test_initial_mode** - 初期状態のモードテスト
   - UserInputHandlerの初期モードが"unknown"であることを確認

2. **test_mode_switching_to_dos** - DOSモードへの切り替えテスト
   - DOSモードへの切り替えが正常に動作することを確認
   - 補完機能のモードも同期して変更されることを確認

3. **test_mode_switching_to_basic** - BASICモードへの切り替えテスト
   - BASICモードへの切り替えが正常に動作することを確認
   - 補完機能のモードも同期して変更されることを確認

4. **test_completion_after_mode_switch_to_dos** - DOSモード切り替え後の補完機能テスト
   - DOSモード切り替え後に適切な補完候補が表示されることを確認
   - @modeコマンドのみが特殊コマンドとして表示されることを確認
   - DOSコマンドが正常に補完されることを確認

5. **test_completion_after_mode_switch_to_basic** - BASICモード切り替え後の補完機能テスト
   - BASICモード切り替え後に複数の特殊コマンドが表示されることを確認
   - 各種BASICモード専用コマンドが含まれることを確認

6. **test_multiple_mode_switches** - 複数回のモード切り替えテスト
   - unknown → dos → basic → dos の順序でモード切り替えを実行
   - 各ステップで適切な補完機能が提供されることを確認
   - 同じモードに戻った際に同じ結果が得られることを確認

7. **test_completer_persistence** - 補完機能の永続性テスト
   - モード切り替え時に新しい補完機能オブジェクトが作成されないことを確認
   - セッションの補完機能が正しく設定されることを確認

### test_terminal_dummy.py

ダミー接続を使用したターミナル機能のテストです。

## テスト実行方法

### 全テスト実行
```bash
python -m pytest tests/ -v
```

### 補完機能のテストのみ実行
```bash
python -m pytest tests/test_completion.py -v
```

### モード切り替えテストのみ実行
```bash
python -m pytest tests/test_mode_switching.py -v
```

### 特定のテストのみ実行
```bash
python -m pytest tests/test_completion.py::TestCommandCompleter::test_dos_mode_at_mode_completion -v
```

### カバレッジ付きでテスト実行
```bash
python -m pytest tests/ -v --cov=msx_serial
```

## テスト結果例

```
tests/test_completion.py::TestCommandCompleter::test_basic_mode_at_commands_completion PASSED        [  6%]
tests/test_completion.py::TestCommandCompleter::test_basic_mode_basic_commands_completion PASSED     [ 13%]
tests/test_completion.py::TestCommandCompleter::test_dos_mode_at_mode_completion PASSED              [ 20%]
tests/test_completion.py::TestCommandCompleter::test_dos_mode_dos_commands_completion PASSED         [ 26%]
tests/test_completion.py::TestCommandCompleter::test_mode_switching PASSED                           [ 33%]
tests/test_completion.py::TestCommandCompleter::test_unknown_mode_completion PASSED                  [ 40%]
tests/test_mode_switching.py::TestModeSwitching::test_completer_persistence PASSED                   [ 46%]
tests/test_mode_switching.py::TestModeSwitching::test_completion_after_mode_switch_to_basic PASSED   [ 53%]
tests/test_mode_switching.py::TestModeSwitching::test_completion_after_mode_switch_to_dos PASSED     [ 60%]
tests/test_mode_switching.py::TestModeSwitching::test_initial_mode PASSED                            [ 66%]
tests/test_mode_switching.py::TestModeSwitching::test_mode_switching_to_basic PASSED                 [ 73%]
tests/test_mode_switching.py::TestModeSwitching::test_mode_switching_to_dos PASSED                   [ 80%]
tests/test_mode_switching.py::TestModeSwitching::test_multiple_mode_switches PASSED                  [ 86%]

============================== 13 passed in 8.14s ==============================
```

## 注意事項

- テストはprompt-toolkitのDocumentとCompleteEventオブジェクトを使用して補完機能をシミュレートしています
- FormattedTextオブジェクトの表示テストでは、適切なテキスト抽出処理を行っています
- テストデータはYAMLファイル（dos_commands.yml）からロードされるため、データファイルが存在することが前提です
- DummyConnectionを使用することで、実際のシリアル接続なしでテストを実行できます
- モード切り替えテストでは、UserInputHandlerの内部状態の変更と補完機能の同期をテストしています 