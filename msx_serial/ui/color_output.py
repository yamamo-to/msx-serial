from colorama import Fore, Style, init

init()


# 初期のデフォルト色設定
COLOR_CONFIG = {
    "info": Fore.CYAN,
    "warn": Fore.YELLOW,
    "error": Fore.RED,
    "exception": Fore.RED,
    "receive": Fore.GREEN,
    "help": Fore.LIGHTYELLOW_EX,
}


def set_color_config(**kwargs: str) -> None:
    """
    使用する色をユーザーがカスタマイズするための関数。
    例: set_color_config(info=Fore.BLUE, warn=Fore.MAGENTA)
    """
    for key, color in kwargs.items():
        if key in COLOR_CONFIG:
            COLOR_CONFIG[key] = color


# 文字列生成関数
def str_info(message: str) -> str:
    return f"{COLOR_CONFIG['info']}[info]{message}{Style.RESET_ALL}"


def str_warn(message: str) -> str:
    return f"{COLOR_CONFIG['warn']}[warn] {message}{Style.RESET_ALL}"


def str_error(message: str) -> str:
    return f"{COLOR_CONFIG['error']}[error] {message}{Style.RESET_ALL}"


def str_exception(message: str, e: Exception) -> str:
    return f"{COLOR_CONFIG['exception']}[{message}] {e}{Style.RESET_ALL}"


# 出力関数
def print_info(message: str) -> None:
    """情報メッセージを表示

    Args:
        message: 表示するメッセージ
    """
    print(f"{Fore.CYAN}{message}{Style.RESET_ALL}")


def print_warn(message: str) -> None:
    """警告メッセージを表示

    Args:
        message: 表示するメッセージ
    """
    print(f"{Fore.YELLOW}{message}{Style.RESET_ALL}")


def print_error(message: str) -> None:
    """エラーメッセージを表示

    Args:
        message: 表示するメッセージ
    """
    print(f"{Fore.RED}{message}{Style.RESET_ALL}")


def print_exception(title: str, exception: Exception) -> None:
    """例外メッセージを表示

    Args:
        title: タイトル
        exception: 例外オブジェクト
    """
    print(f"{Fore.RED}{title}: {str(exception)}{Style.RESET_ALL}")


def print_help(message: str) -> None:
    """ヘルプメッセージを表示

    Args:
        message: 表示するメッセージ
    """
    print(f"{Fore.GREEN}{message}{Style.RESET_ALL}")


def print_debug(message: str) -> None:
    """デバッグメッセージを表示

    Args:
        message: 表示するメッセージ
    """
    print(f"{Fore.MAGENTA}{message}{Style.RESET_ALL}")


def print_trace(message: str) -> None:
    """トレースメッセージを表示

    Args:
        message: 表示するメッセージ
    """
    print(f"{Fore.WHITE}{message}{Style.RESET_ALL}")


def print_success(message: str) -> None:
    """成功メッセージを表示

    Args:
        message: 表示するメッセージ
    """
    print(f"{Fore.GREEN}{message}{Style.RESET_ALL}")


def print_failure(message: str) -> None:
    """失敗メッセージを表示

    Args:
        message: 表示するメッセージ
    """
    print(f"{Fore.RED}{message}{Style.RESET_ALL}")


def print_prompt(message: str) -> None:
    """プロンプトメッセージを表示

    Args:
        message: 表示するメッセージ
    """
    print(f"{Fore.CYAN}{message}{Style.RESET_ALL}", end="")


def print_input(message: str) -> None:
    """入力メッセージを表示

    Args:
        message: 表示するメッセージ
    """
    print(f"{Fore.GREEN}{message}{Style.RESET_ALL}")


def print_receive(message: str, end: str = "\n") -> None:
    print(f"{COLOR_CONFIG['receive']}{message}{Style.RESET_ALL}", end=end)


def print_prompt_receive(message: str) -> None:
    """プロンプト受信メッセージを表示（改行付き）

    Args:
        message: 表示するメッセージ
    """
    print(f"{COLOR_CONFIG['receive']}{message}{Style.RESET_ALL}")


def print_receive_no_newline(message: str) -> None:
    """受信メッセージを改行なしで表示

    Args:
        message: 表示するメッセージ
    """
    print(f"{COLOR_CONFIG['receive']}{message}{Style.RESET_ALL}", end="")
