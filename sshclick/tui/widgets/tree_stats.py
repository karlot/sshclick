from textual.widgets import Static

from sshclick.tui.state import TUIState


class TreeStats(Static):
    """Small summary block rendered below the navigation tree."""

    def update_state(self, state: TUIState) -> None:
        """Refresh the tree-related totals shown in the left pane."""

        self.update(
            f"[b]Groups   :[/] {len(state.sshconf.groups)}\n"
            f"[b]Hosts    :[/] {state.host_count}\n"
            f"[b]Patterns :[/] {state.pattern_count}\n"
            f"[b]Includes :[/] {state.include_count}"
        )
