import signal
import subprocess
from collections.abc import Sequence
from contextlib import nullcontext
from typing import ContextManager, Protocol


class SupportsSuspend(Protocol):
    """Protocol for UI objects that can temporarily hand terminal control away."""

    def suspend(self) -> ContextManager[object]:
        """Return a context manager that suspends the UI while a child command runs."""
        ...


def run_interactive_command(argv: Sequence[str], tui: SupportsSuspend | None = None) -> int:
    """
    Run an interactive child command with inherited terminal IO.

    When a TUI instance is provided, the UI is suspended first so the child
    process can take over the terminal cleanly. The parent temporarily ignores
    Ctrl-C and Ctrl-\ while waiting, which keeps those signals directed at the
    interactive child instead of tearing down SSHClick itself.
    """
    suspend_context = tui.suspend() if tui is not None else nullcontext()

    with suspend_context:
        original_sigint = signal.getsignal(signal.SIGINT)
        original_sigquit = signal.getsignal(signal.SIGQUIT)
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGQUIT, signal.SIG_IGN)
        try:
            return subprocess.run(list(argv), check=False).returncode
        finally:
            signal.signal(signal.SIGINT, original_sigint)
            signal.signal(signal.SIGQUIT, original_sigquit)


def run_captured_command(argv: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(argv), capture_output=True, text=True, check=False)
