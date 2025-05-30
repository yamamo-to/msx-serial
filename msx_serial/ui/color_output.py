from colorama import Fore, Style as ColorStyle


# 初期のデフォルト色設定
COLOR_CONFIG = {
    "info": Fore.CYAN,
    "warn": Fore.YELLOW,
    "error": Fore.RED,
    "exception": Fore.RED,
    "receive": Fore.GREEN,
    "help": Fore.LIGHTYELLOW_EX,
}


def set_color_config(**kwargs):
    """
    使用する色をユーザーがカスタマイズするための関数。
    例: set_color_config(info=Fore.BLUE, warn=Fore.MAGENTA)
    """
    for key, color in kwargs.items():
        if key in COLOR_CONFIG:
            COLOR_CONFIG[key] = color


# 文字列生成関数
def str_info(message):
    return f"{COLOR_CONFIG['info']}[info]{message}{ColorStyle.RESET_ALL}"


def str_warn(message):
    return f"{COLOR_CONFIG['warn']}[warn] {message}{ColorStyle.RESET_ALL}"


def str_error(message):
    return f"{COLOR_CONFIG['error']}[error] {message}{ColorStyle.RESET_ALL}"


def str_exception(message, e):
    return f"{COLOR_CONFIG['exception']}[{message}] {e}{ColorStyle.RESET_ALL}"


# 出力関数
def print_info(message, end="\n"):
    print(str_info(message), end=end)


def print_warn(message, end="\n"):
    print(str_warn(message), end=end)


def print_error(message, end="\n"):
    print(str_error(message), end=end)


def print_exception(message, e, end="\n"):
    print(str_exception(message, e), end=end)


def print_receive(message, end="\n"):
    print(f"{COLOR_CONFIG['receive']}{message}{ColorStyle.RESET_ALL}", end=end)


def print_help(message, end="\n"):
    print(f"{COLOR_CONFIG['help']}{message}{ColorStyle.RESET_ALL}", end=end)
