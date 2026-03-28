import os.path

# SSHClick stuff
from sshclick.globals import USER_SSH_CONFIG
from sshclick.sshc import SSH_Config

# Textual core
from textual.app import App, ComposeResult
from textual.widgets import Tree, Header, Footer
from textual.containers import Container
from textual.theme import Theme

# SSHTui modules
from sshclick.ssht.node_tree import SSHTree
from sshclick.ssht.data_view import SSHDataView
from sshclick.ssht.modal_delete import ModalDelete
from sshclick.ssht.modal_action import ModalAction

# Load linked utils
from sshclick.ssht.utils import run_connect

# My default theme (preparing for textual>=0.80)
# from sshclick.ssht.def_theme import sshtui_theme

# Define a "Grayscale" theme
SSHC_THEME = Theme(
    name="sshc-dark",
    primary="#444444",    # Dark Gray
    secondary="#666666",  # Medium Gray
    accent="#888888",     # Light Gray
    surface="#1e1e1e",    # Background
)

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

    def __init__(self, config_file: str = USER_SSH_CONFIG) -> None:
        super().__init__()
        self.current_node = None
        self.config_file = os.path.expanduser(config_file)
        self.sshconf = SSH_Config(file=self.config_file).read().parse()

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
        self.register_theme(SSHC_THEME)
        self.theme = "sshc-dark"  # The classic look you likely remember
        self.query_one(Tree).focus()

    def on_tree_node_highlighted(self, event):
        self.current_node = event.node.data
        # For some reason if there was no keyboard interaction, and only mouse is used
        # to expand group and select host, then NoMatch error is generated in self.query_one()
        # TODO: Recheck event orders and see if there is better way of solving it
        data_view = self.query_one_optional(SSHDataView)
        if data_view is not None:
            data_view.update(self.current_node)

    # ---------------------------------
    # Actions
    # ---------------------------------
    def action_quit(self) -> None:
        self.exit(0)

    def action_connect(self, prog: str) -> None:
        run_connect(self, prog, self.current_node)

    def action_delete(self) -> None:
        if self.current_node is not None:
            self.push_screen(ModalDelete(self.current_node))

    def action_action(self) -> None:
        self.push_screen(ModalAction(self.current_node))
