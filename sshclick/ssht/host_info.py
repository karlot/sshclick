from sshclick.sshc import SSH_Host

from rich.panel import Panel
from rich.table import Table
from rich import box

from textual.app import ComposeResult
from textual.widgets import Static, Label

# Defaults
DEF_PANEL_COLOR = "grey42"
DEF_IPARAM_COLOR = "yellow"


class SSHHostInfo(Static):
    """Widget for SSH Host data"""

    DEFAULT_CSS = """
    .labels {
        width: 100%;
        color: $accent;
        padding: 1 1 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("Details", classes="labels")
        yield Static(Panel("...empty...", style=DEF_PANEL_COLOR), id="hst_details")

        yield Label("Extra information", classes="labels")
        yield Static(Panel("...empty...", style=DEF_PANEL_COLOR), id="hst_information")

        yield Label("SSH Parameters", classes="labels")
        yield Static(Panel("...empty...", style=DEF_PANEL_COLOR), id="hst_parameters")


    def update(self, host: SSH_Host) -> None:
        det: Static = self.query_one("#hst_details") # type: ignore
        info: Static = self.query_one("#hst_information") # type: ignore
        params: Static = self.query_one("#hst_parameters") # type: ignore
        
        det.update(Panel(
            f"[b]Group[/b]: {host.group}\n"
            f"[b]Type[/b]:  {host.type}",
            border_style=DEF_PANEL_COLOR
        ))
        info.update(Panel("\n".join(host.info), border_style=DEF_PANEL_COLOR) if host.info else Panel("...empty...", style=DEF_PANEL_COLOR))

        param_table = Table(box=box.ROUNDED, style=DEF_PANEL_COLOR, show_header=True, show_edge=True, expand=True)
        param_table.add_column("Param")
        param_table.add_column("Value")
        param_table.add_column("Inherited-from")

        # Add rows for SSH Config parameter table
        for key, value in host.params.items():
            output_value = value if not isinstance(value, list) else "\n".join(value)
            param_table.add_row(key, output_value)

        # Add rows for inherited SSH Config parameters
        for pattern, pattern_params in host.inherited_params:
            for param, value in pattern_params.items():
                if not param in host.params:
                    output_value = value if not isinstance(value, list) else "\n".join(value)
                    param_table.add_row(param, output_value, pattern, style=DEF_IPARAM_COLOR)

        params.update(param_table) # type: ignore