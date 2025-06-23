"""Color output utilities for MSX terminal"""

from colorama import Fore, Style, init
from typing import Dict

init()

# Color mapping
COLORS: Dict[str, str] = {
    "info": Fore.CYAN,
    "warn": Fore.YELLOW,
    "error": Fore.RED,
    "exception": Fore.RED,
    "success": Fore.GREEN,
    "debug": Fore.MAGENTA,
    "trace": Fore.WHITE,
    "help": Fore.GREEN,
    "receive": Fore.GREEN,
}


def _colorize(message: str, color: str) -> str:
    """Apply color to message"""
    return f"{color}{message}{Style.RESET_ALL}"


def _print_colored(message: str, color_key: str, **kwargs) -> None:
    """Print colored message"""
    color = COLORS.get(color_key, Fore.WHITE)
    print(_colorize(message, color), **kwargs)


# Primary output functions
def print_info(message: str) -> None:
    """Print info message"""
    _print_colored(message, "info")


def print_warn(message: str) -> None:
    """Print warning message"""
    _print_colored(message, "warn")


def print_error(message: str) -> None:
    """Print error message"""
    _print_colored(message, "error")


def print_exception(title: str, exception: Exception) -> None:
    """Print exception message"""
    _print_colored(f"{title}: {str(exception)}", "exception")


def print_success(message: str) -> None:
    """Print success message"""
    _print_colored(message, "success")


def print_debug(message: str) -> None:
    """Print debug message"""
    _print_colored(message, "debug")


def print_help(message: str) -> None:
    """Print help message"""
    _print_colored(message, "help")


def print_receive(message: str, end: str = "\n") -> None:
    """Print received message"""
    _print_colored(message, "receive", end=end)


def print_prompt_receive(message: str) -> None:
    """Print prompt received message (no newline)"""
    _print_colored(message, "receive", end="", flush=True)


# String generation functions
def str_info(message: str) -> str:
    """Generate colored info string"""
    return _colorize(f"[info]{message}", COLORS["info"])


def str_warn(message: str) -> str:
    """Generate colored warning string"""
    return _colorize(f"[warn] {message}", COLORS["warn"])


def str_error(message: str) -> str:
    """Generate colored error string"""
    return _colorize(f"[error] {message}", COLORS["error"])


def str_exception(message: str, e: Exception) -> str:
    """Generate colored exception string"""
    return _colorize(f"[{message}] {e}", COLORS["exception"])


# Configuration
def set_color_config(**kwargs: str) -> None:
    """Customize colors"""
    for key, color in kwargs.items():
        if key in COLORS:
            COLORS[key] = color


# Legacy aliases for backward compatibility
def print_trace(message: str) -> None:
    """Print trace message"""
    print_debug(message)


def print_failure(message: str) -> None:
    """Print failure message"""
    print_error(message)


def print_input(message: str) -> None:
    """Print input message"""
    print_success(message)


def print_prompt(message: str) -> None:
    """Print prompt message"""
    _print_colored(message, "info", end="")


def print_receive_no_newline(message: str) -> None:
    """Print receive message without newline"""
    _print_colored(message, "receive", end="")
