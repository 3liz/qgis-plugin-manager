"""Simple façade to console output"""

import sys

verbose = False


def set_verbose_mode(enable: bool):
    global verbose
    verbose = enable
    if verbose:
        print("=Verbose mode activated", file=sys.stderr)


def echo(s: str):
    print(s)


def info(s: str):
    print(s, file=sys.stderr)


def debug(s: str, *args, **kwargs):
    if verbose:
        print(f"\033[34m{s.format(*args, **kwargs)}\033[0m", file=sys.stderr)


def format_success(s: str) -> str:
    return f"\033[92m{s}\033[0m"


def success(s: str):
    print(format_success(s), file=sys.stderr)


def format_alert(s: str) -> str:
    return f"\033[93m{s}\033[0m"


def alert(s: str):
    print(format_alert(s), file=sys.stderr)


def format_critical(s: str) -> str:
    return f"\033[91m{s}\033[0m"


def critical(s: str):
    print(format_critical(s), file=sys.stderr)
