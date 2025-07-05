#!/usr/bin/env python3
"""MODE 80実行後のDIR出力解析デバッグ"""

import re
from msx_serial.completion.dos_filesystem import DOSFileSystemManager

def debug_parse():
    """解析デバッグ"""
    manager = DOSFileSystemManager()
    
    # テストケースの実際のデータ
    dir_output = """
 Volume in drive A: has no name
 Directory of A:\\

HELP            <dir>  23-08-05  7:13a
UTILS           <dir>  23-08-05  7:13a
AUTOEXEC BAT        57 88-07-21 11:01p
COMMAND2 COM     14976 88-10-25  3:04p
MSXDOS2  SYS      4480 88-10-14  3:12p
REBOOT   BAT        57 88-07-21 11:01p
SAMPLE          <dir>  25-05-30 12:55a
TEST     BAS       401 25-06-02  1:54a
 10K in 8 files        321K free
    """

    print("=== テストケース: MODE 80実行後 ===")
    lines = dir_output.split("\n")
    
    for i, line in enumerate(lines):
        line = line.rstrip()
        if not line:
            continue
            
        print(f"Line {i}: '{line}'")
        print(f"  Length: {len(line)}")
        print(f"  Repr: {repr(line)}")
        
        # システムメッセージや集計行をスキップ
        lower_line = line.lower().strip()
        if (
            lower_line.startswith("volume")
            or lower_line.startswith("directory")
            or "free" in lower_line
            or " in " in lower_line
            or lower_line.endswith(" files")
        ):
            print(f"  -> Skipped (system message)")
            continue

        # 実際の行を詳しく分析
        print(f"  Analysis:")
        print(f"    Starts with space: {line.startswith(' ')}")
        print(f"    Parts: {line.split()}")
        
        # ディレクトリパターン2: "HELP            <dir>  23-08-05  7:13a"
        dir_pattern2 = r"^(\S+)\s+<dir>\s+\d{2}-\d{2}-\d{2}\s+\d{1,2}:\d{2}[ap]m\s*$"
        dir_match_with_date = re.match(dir_pattern2, line, re.IGNORECASE)
        if dir_match_with_date:
            print(f"  -> Directory (pattern 2): {dir_match_with_date.group(1)}")
            continue

        # ファイルパターン2: "AUTOEXEC BAT        57 88-07-21 11:01p"
        file_pattern2 = r"^(\S+)\s+(\S+)\s+(\d+)\s+\d{2}-\d{2}-\d{2}\s+\d{1,2}:\d{2}[ap]m\s*$"
        file_match_with_date = re.match(file_pattern2, line)
        if file_match_with_date:
            filename, extension, size_str = file_match_with_date.groups()
            print(f"  -> File (pattern 2): {filename}.{extension} ({size_str})")
            continue

        print(f"  -> No match")
        print(f"  Testing patterns:")
        print(f"    Dir pattern 2: {bool(re.match(dir_pattern2, line, re.IGNORECASE))}")
        print(f"    File pattern 2: {bool(re.match(file_pattern2, line))}")
        
        # 実際の正規表現テスト
        print(f"  Regex tests:")
        print(f"    ^(\S+)\s+<dir>\s+\d{{2}}-\d{{2}}-\d{{2}}\s+\d{{1,2}}:\d{{2}}[ap]m\s*$: {bool(re.match(r'^(\S+)\s+<dir>\s+\d{2}-\d{2}-\d{2}\s+\d{1,2}:\d{2}[ap]m\s*$', line, re.IGNORECASE))}")
        print(f"    ^(\S+)\s+(\S+)\s+(\d+)\s+\d{{2}}-\d{{2}}-\d{{2}}\s+\d{{1,2}}:\d{{2}}[ap]m\s*$: {bool(re.match(r'^(\S+)\s+(\S+)\s+(\d+)\s+\d{2}-\d{2}-\d{2}\s+\d{1,2}:\d{2}[ap]m\s*$', line))}")

if __name__ == "__main__":
    debug_parse() 