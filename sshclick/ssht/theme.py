from textual.app import App
from textual.theme import Theme


# Default VS-dark inspired palette
SSHCLICK_DARK_THEME = Theme(
    name="SSHClick-dark",
    primary="#0E639C",
    secondary="#9CDCFE",
    accent="#4EC9B0",
    foreground="#D4D4D4",
    background="#1E1E1E",
    success="#6A9955",
    warning="#D7BA7D",
    error="#F14C4C",
    surface="#252526",
    panel="#1E1E1E",
    dark=True,
    variables={
        "sshclick-chrome": "#2D2D30",
        "sshclick-overlay": "#111111",
        "sshclick-border": "#3C3C3C",
        "sshclick-muted": "#C8C8C8",
        "sshclick-tree-cursor": "#094771",
        "sshclick-scrollbar": "#4E94CE",
        "sshclick-scrollbar-hover": "#3794FF",
        "sshclick-pattern": "#4FC1FF",
    },
)


def register_sshclick_theme(app: App) -> None:
    """Register the built-in SSHClick theme with the running app."""

    # Register once on app startup so the TUI can switch to the named theme.
    app.register_theme(SSHCLICK_DARK_THEME)
