from sshclick.sshc import SSH_Group, SSH_Host

from rich.rule import Rule

from textual.app import ComposeResult
from textual.widgets import Static, Label, ContentSwitcher
from textual.containers import VerticalScroll

from .group_info import SSHGroupInfo
from .host_info import SSHHostInfo


class SSHDataView(Static):
    """SSH Item data view panel"""

    def compose(self) -> ComposeResult:
        yield Label(id="data_view_header")
        yield Static(Rule(style="$text"))

        with ContentSwitcher(initial="no-view"):
            yield Static(id="no-view")
            yield SSHGroupInfo(id="group-view")
            with VerticalScroll(id="host-view"):
                yield SSHHostInfo()

    def update(self, sshitem = "") -> None:
        label: Label = self.query_one("#data_view_header") # type: ignore
        grp = self.query_one(SSHGroupInfo)
        hst = self.query_one(SSHHostInfo)

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
