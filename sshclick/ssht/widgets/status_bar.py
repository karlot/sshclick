from textual.app import ComposeResult
from textual.containers import Grid
from textual.widgets import Static

from sshclick.ssht.state import TUIState


class StatusBar(Grid):
    """Compact top bar for config path and current write mode."""

    def compose(self) -> ComposeResult:
        yield Static(id="status_config")
        yield Static(id="status_mode")

    def update_state(self, state: TUIState) -> None:
        """Render the current config path and read/write mode."""

        mode_value = f"[b $warning]READ ONLY[/]" if state.is_read_only else f"[b $success]Writable[/]"

        self.query_one("#status_config", Static).update(f"[b]Config:[/] {state.config_file}")
        self.query_one("#status_mode", Static).update(f"[b]Mode:[/] {mode_value}")
