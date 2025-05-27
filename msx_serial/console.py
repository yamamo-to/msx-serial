from colorama import Fore, Style as ColorStyle


def str_info(message):
    return f"{Fore.CYAN}[info]{message}{ColorStyle.RESET_ALL}"


def str_warn(message):
    return f"{Fore.YELLOW}[warn] {message}{ColorStyle.RESET_ALL}"


def str_error(message):
    return f"{Fore.RED}[error] {message}{ColorStyle.RESET_ALL}"


def str_exception(message, e):
    return f"{Fore.RED}[{message}] {e}{ColorStyle.RESET_ALL}"


def print_info(message, end=""):
    print(str_info(message), end=end)


def print_warn(message, end=""):
    print(str_warn(message), end=end)


def print_error(message, end=""):
    print(str_error(message), end=end)


def print_exception(message, e, end=""):
    print(str_exception(message, e), end=end)


def print_receive(message, end=""):
    print(f"{Fore.GREEN}{message}{ColorStyle.RESET_ALL}", end=end)
