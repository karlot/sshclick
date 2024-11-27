from sshclick.sshc import SSH_Group

from rich.panel import Panel

from textual.app import ComposeResult
from textual.widgets import Static, Label

# Defaults
DEF_PANEL_COLOR = "grey42"


class SSHGroupInfo(Static):
    """Widget for SSH Group data"""

    DEFAULT_CSS = """
    .labels {
        width: 100%;
        color: $accent;
        padding: 1 1 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("Description", classes="labels")
        yield Static(Panel("...empty...", style=DEF_PANEL_COLOR), id="grp_description")

        yield Label("Extra information", classes="labels")
        yield Static(Panel("...empty...", style=DEF_PANEL_COLOR), id="grp_information")


    def update(self, group: SSH_Group) -> None:
        desc: Static = self.query_one("#grp_description") # type: ignore
        info: Static = self.query_one("#grp_information") # type: ignore

        desc.update(Panel(group.desc, border_style=DEF_PANEL_COLOR))
        info.update(Panel("\n".join(group.info), border_style=DEF_PANEL_COLOR))
