import os, subprocess

# SSHClick stuff
from sshclick.globals import USER_SSH_CONFIG, SSH_CONNECT_TIMEOUT
from sshclick.sshc import SSH_Config, SSH_Host, HostType

# Textual core
from textual.app import App, ComposeResult
from textual.reactive import reactive
from textual.widgets import Tree, Header, Footer
from textual.containers import Container

# SSHTui modules
from sshclick.ssht.node_tree import SSHTree
from sshclick.ssht.data_view import SSHDataView
from sshclick.ssht.modal_delete import ModalDelete
from sshclick.ssht.modal_action import ModalAction

# Load linked utils
from sshclick.ssht.utils import run_connect

# My default theme (preparing for textual>=0.80)
# from sshclick.ssht.def_theme import sshtui_theme

# Defaults
DEFAULT_CONNECT_OPTS = {
    "ConnectTimeout": SSH_CONNECT_TIMEOUT,  # Add explicit timeout option
}


class SSHTui(App):
    TITLE = "SSHClick"
    SUB_TITLE = "TUI"

    BINDINGS = [
        ("q",      "quit",            "Quit"),
        ("escape", "quit",            "Quit"),
        ("a",      "action",          "Action"),
        ("s",      "connect('ssh')",  "SSH"),
        ("f",      "connect('sftp')", "SFTP"),
        # ("c",      "create",          "Create"),
        # ("e",      "edit",            "Edit"),
        ("d",      "delete",          "Delete"),
        ("delete", "delete",          "Delete"),
    ]

    DEFAULT_CSS = """
    SSHTree {
        /*scrollbar-gutter: stable;*/
        overflow: auto;
        width: 36;
        height: 100%;
        dock: left;
    }

    SSHDataView {
        width: 100%;
        height: 100%;
        padding: 1 2;
        content-align: center middle;
        background: $surface;
    }

    ModalDelete {
        align: center middle;
    }
    ModalAction {
        align: center middle;
    }
    """

    # Reactive loading of SSH Configuration
    sshconf = reactive(SSH_Config(file=os.path.expanduser(USER_SSH_CONFIG)).read().parse())

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container():
            yield SSHTree(self.sshconf)
            yield SSHDataView()
        yield Footer()

    # ---------------------------------
    # Events
    # ---------------------------------
    def on_mount(self, _) -> None:
        self.query_one(Tree).focus()

    def on_tree_node_highlighted(self, event):
        self.current_node = event.node.data
        self.query_one(SSHDataView).update(self.current_node)

    # ---------------------------------
    # Actions
    # ---------------------------------
    def action_quit(self) -> None:
        self.exit(0)

    def action_connect(self, prog: str) -> None:
        run_connect(self, prog, self.current_node)

    def action_delete(self) -> None:
        if self.current_node != None:
            self.push_screen(ModalDelete(self.current_node))

    def action_action(self) -> None:
        self.push_screen(ModalAction(self.current_node))
