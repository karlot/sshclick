import os

from rich.console import Console

out = Console()

# I dont really need full logging import, just output some info if currently debugging
DEBUG = True if "SSHC_DEBUG" in os.environ and os.environ["SSHC_DEBUG"] == "1" else False


def debug(msg):
    if DEBUG:
        out.print(f"[bright_blue]DEBUG[/]: {msg}")


def info(msg):
    out.print(f"[cyan]INFO[/]: {msg}")


def warn(msg):
    out.print(f"[yellow]WARN[/]: {msg}")


def error(msg):
    out.print(f"[bright_red]ERROR[/]: {msg}")
