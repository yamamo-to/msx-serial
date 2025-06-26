"""MSXシリアルターミナルのメインエントリーポイント"""

import argparse
import sys

from msx_serial.connection.connection import detect_connection_type
from msx_serial.core.msx_session import MSXSession


def main() -> None:
    """メインエントリーポイント"""
    parser = argparse.ArgumentParser(description="MSX Serial Terminal")
    parser.add_argument(
        "connection",
        type=str,
        help="Connection string (e.g. COM4, /dev/ttyUSB0, 192.168.1.100:2223, dummy://)",
    )
    parser.add_argument("--encoding", default="msx-jp", help="Text encoding")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    try:
        # URIから接続タイプを検出
        config = detect_connection_type(args.connection)

        # ターミナルを作成して実行
        terminal = MSXSession(
            config=config,
            encoding=args.encoding,
        )

        if args.debug:
            terminal.toggle_debug_mode()

        terminal.run()

    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
