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
            (f"[b]AltHost[/b]: " + ", ".join(host.alt_names) + "\n" if host.alt_names else "") +
            f"[b]Group[/b]:   {host.group}\n"
            f"[b]Type[/b]:    {host.type.value}",
            border_style=DEF_PANEL_COLOR
        ))
        info.update(Panel("\n".join(host.info), border_style=DEF_PANEL_COLOR) if host.info else Panel("...empty...", style=DEF_PANEL_COLOR))

        #// Prepare table with params and append it to the group
        #// -----------------------------------------------------------------------
        param_table = Table(box=box.ROUNDED, style=DEF_PANEL_COLOR, show_header=True, show_edge=True, expand=True)
        param_table.add_column("Param", ratio=1)
        param_table.add_column("Value", ratio=1)
        param_table.add_column("Inherited-from", ratio=1)

        # Add rows for SSH Config parameters
        for param in host.get_all_params():
            value, source = host.get_applied_param(param)
            output_value = value if not isinstance(value, list) else "\n".join(value)
            if source == "local":
                param_table.add_row(param, output_value)
            elif source == "global":
                param_table.add_row(param, output_value, "global", style="green")
            else:
                param_table.add_row(param, output_value, source, style="yellow")

        params.update(param_table) # type: ignore