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
        source_refs = group.source_refs if group.source_refs else [(host.source_file, host.source_line) for host in group.hosts + group.patterns if host.source_file]
        source_lines = [f"{source_file}:{source_line}" for source_file, source_line in source_refs if source_file]

        description = group.desc if group.desc else "...empty..."
        if source_lines:
            description = f"[b]Defined in[/b]:\n" + "\n".join(source_lines) + "\n\n" + description

        desc.update(Panel(description, border_style=DEF_PANEL_COLOR))
        info.update(Panel("\n".join(group.info), border_style=DEF_PANEL_COLOR))
