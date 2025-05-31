"""
MSXシリアルターミナルのメインエントリーポイント
"""

import sys
from msx_serial.terminal import MSXTerminal
from msx_serial.connection.connection import detect_connection_type
from msx_serial.ui.color_output import print_exception


def main() -> int:
    """メイン関数"""
    import argparse

    parser = argparse.ArgumentParser(description="MSXシリアルターミナル")
    parser.add_argument(
        "connection",
        type=str,
        help="接続先 (例: COM4, /dev/ttyUSB0, 192.168.1.100:2223)",
    )
    parser.add_argument(
        "--encoding", type=str, default="msx-jp", help="エンコーディング"
    )
    args = parser.parse_args()

    try:
        # 接続タイプを自動判定
        config = detect_connection_type(args.connection)

        terminal = MSXTerminal(
            config,
            encoding=args.encoding,
            prompt_style="#00ff00 bold",
        )
        terminal.run()
        return 0
    except ValueError as e:
        print_exception("エラー", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
