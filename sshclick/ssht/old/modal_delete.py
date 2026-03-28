# from sshclick.globals import USER_SSH_CONFIG, SSH_CONNECT_TIMEOUT
from sshclick.sshc import SSH_Config, SSH_Group, SSH_Host, HostType

from textual import on
from textual.app import ComposeResult
from textual.widgets import Label, Button, Static
from textual.containers import Grid, Container, Horizontal, Vertical
from textual.screen import ModalScreen


class ModalDelete(ModalScreen[None]):
    BINDINGS = [
        ("escape", "app.pop_screen")
    ]

    DEFAULT_CSS = """
    #delete_dialog {
        padding: 0 2;
        width: 60;
        height: auto;
        border: tall $primary;
    }

    Label {
        width: 100%;
        content-align: center middle;
        margin: 0 0 2 0;
    }

    #button_row {
        height: auto;
        align: center middle;
    }
    Button {
        width: 6;
        max-width: 16;
        margin: 0 0 0 1;
    }
    """

    def __init__(self, node: SSH_Host | SSH_Group) -> None:
        self.node = node
        super().__init__()

    def compose(self) -> ComposeResult:
        if isinstance(self.node, SSH_Group) and self.node.name == "default":
            with Vertical(id="delete_dialog"):
                yield Label("You cannot delete 'default' Group!")
                with Horizontal(id="button_row"):
                    yield Button("Ok", variant="primary", id="delete_no")
        else:
            targ_type = "host" if isinstance(self.node, SSH_Host) else "group"
            with Vertical(id="delete_dialog"):
                yield Label(f"Are you sure you want to delete SSH {targ_type} '{self.node.name}'?")
                with Horizontal(id="button_row"):
                    yield Button("Yes", variant="error", id="delete_yes")
                    yield Button("No", variant="primary", id="delete_no")

    @on(Button.Pressed, "#delete_yes")
    def delete_yes(self) -> None:
        ...

    @on(Button.Pressed, "#delete_no")
    def delete_no(self) -> None:
        self.app.pop_screen()

    
