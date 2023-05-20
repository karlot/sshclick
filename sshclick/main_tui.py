import os, subprocess, time
from typing import Optional

from sshclick.sshc import SSH_Config, SSH_Group, SSH_Host

from rich.rule import Rule
from rich.panel import Panel
from rich.table import Table
from rich import box

from textual.app import App, ComposeResult
from textual.widgets import Tree, Header, Footer, Static, Label, ContentSwitcher
from textual.containers import Container, VerticalScroll


USER_SSH_CONFIG   = "~/.ssh/config"
USER_DEMO_CONFIG  = "~/.ssh/config_demo"


class SSHGroupDataInfo(Static):
    """Widget for SSH Group data"""

    DEFAULT_CSS = """
    .grp_labels {
        width: 100%;
        color: $accent;
        padding: 1 1 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("Description", classes="grp_labels")
        yield Static(Panel("...empty...", style="grey42"), id="grp_description")
        yield Label("Extra information", classes="grp_labels")
        yield Static(Panel("...empty...", style="grey42"), id="grp_information")

    def update(self, group: SSH_Group) -> None:
        desc: Static = self.query_one("#grp_description") # type: ignore
        info: Static = self.query_one("#grp_information") # type: ignore
        desc.update(Panel(group.desc, border_style="grey42"))
        info.update(Panel("\n".join(group.info), border_style="grey42"))


class SSHHostDataInfo(Static):
    """Widget for SSH Host data"""

    DEFAULT_CSS = """
    .hst_labels {
        width: 100%;
        color: $accent;
        padding: 1 1 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("Details", classes="hst_labels")
        yield Static(Panel("...empty...", style="grey42"), id="hst_details")
        yield Label("Extra information", classes="hst_labels")
        yield Static(Panel("...empty...", style="grey42"), id="hst_information")
        yield Label("SSH Parameters", classes="hst_labels")
        yield Static(Panel("...empty...", style="grey42"), id="hst_parameters")

    def update(self, host: SSH_Host) -> None:
        det: Static = self.query_one("#hst_details") # type: ignore
        info: Static = self.query_one("#hst_information") # type: ignore
        params: Static = self.query_one("#hst_parameters") # type: ignore
        det.update(Panel(f"[bold]Group[/b]: {host.group}\n[bold]Type[/b]:  {host.type}", border_style="grey42"))
        info.update(Panel("\n".join(host.info), border_style="grey42") if host.info else Panel("...empty...", style="grey42"))

        param_table = Table(box=box.ROUNDED, style="grey42", show_header=True, show_edge=True, expand=True)
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
                    param_table.add_row(param, output_value, pattern, style="yellow")

        
        params.update(param_table) # type: ignore


class SSHDataView(Static):
    """SSH Item data view panel"""

    def compose(self) -> ComposeResult:
        yield Label(id="data_view_header")
        yield Static(Rule(style="$text"))

        with ContentSwitcher(initial="no-view"):
            yield Static(id="no-view")
            yield SSHGroupDataInfo(id="group-view")
            with VerticalScroll(id="host-view"):
                yield SSHHostDataInfo()

    def update(self, sshitem = "") -> None:
        label: Label = self.query_one("#data_view_header") # type: ignore
        grp = self.query_one(SSHGroupDataInfo)
        hst = self.query_one(SSHHostDataInfo)

        if isinstance(sshitem, SSH_Group):
            group: SSH_Group = sshitem
            label.update(f"Group: {group.name}")
            self.query_one(ContentSwitcher).current = "group-view"
            grp.update(group)

        elif isinstance(sshitem, SSH_Host):
            host: SSH_Host = sshitem
            label.update(f"Host: {host.name}")
            self.query_one(ContentSwitcher).current = "host-view"
            hst.update(host)

        else:
            label.update("Select node from the list")
            self.query_one(ContentSwitcher).current = "no-view"


class SSHTui(App):
    TITLE = "SSHClick"
    SUB_TITLE = "Experimental TUI"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle dark mode"),
        ("c", "connect_ssh", "SSH to host"),
        ("f", "connect_sftp", "SFTP to host"),
    ]

    CSS = """
    Screen {
        background: $surface-darken-1;
    }

    SSHDataView {
        width: 100%;
        height: 100%;
        padding: 1 2;
        background: $panel;
        content-align: center middle;
    }

    Tree {
        scrollbar-gutter: stable;
        overflow: auto;
        width: 36;
        height: 100%;
        dock: left;
        background: $surface;
    }
    """

    def __init__(self, sshconf=None):
        if isinstance(sshconf, SSH_Config):
            self.sshconf = sshconf
        else:
            USER_SSH_CONFIG = USER_DEMO_CONFIG
            self.sshconf = SSH_Config(file=os.path.expanduser(USER_SSH_CONFIG)).read().parse()
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container():
            ssh_tree = Tree(f"SSH Configuration ({len(self.sshconf.groups)} groups)", id="sshtree", data=None)
            ssh_tree.root.expand()

            for group in self.sshconf.groups:
                g = ssh_tree.root.add(f":file_folder: {group.name}", data=group, expand=False)
                for host in group.hosts + group.patterns:
                    g.add_leaf(host.name, data=host)

            yield ssh_tree
            yield SSHDataView()
        yield Footer()

    def on_mount(self, _) -> None:
        self.query_one(Tree).focus()

    def on_tree_node_highlighted(self, event):
        self.current_node = event.node.data
        self.query_one(SSHDataView).update(self.current_node)

    def action_toggle_dark(self) -> None:
        self.dark = not self.dark

    def action_quit(self) -> None:
        self.exit(0)

    def action_connect_ssh(self) -> None:
        # "Connect to" only works on normal hosts
        if isinstance(self.current_node, SSH_Host) and self.current_node.type == "normal":
            # TODO: remove hardcoded timeout option, and load it from config or global "default"
            self._run_external_cmd_with_args(f"ssh -o ConnectTimeout=5 {self.current_node.name}")

    def action_connect_sftp(self) -> None:
        # "Connect to" only works on normal hosts
        if isinstance(self.current_node, SSH_Host) and self.current_node.type == "normal":
            # TODO: remove hardcoded timeout option, and load it from config or global "default"
            self._run_external_cmd_with_args(f"sftp -o ConnectTimeout=5 {self.current_node.name}")

    def _run_external_cmd_with_args(self, command):
        # Note this is a hack since textual does not have native/better way
        # of running external applications currently, ow within window/widget
        driver = self._driver
        if driver is not None:
            driver.stop_application_mode()
            try:
                subprocess.run(command, shell=True)
                time.sleep(2)
            finally:
                self.refresh()
                driver.start_application_mode()
