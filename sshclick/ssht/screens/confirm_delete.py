from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label

from sshclick.core import SSH_Group, SSH_Host


class ConfirmDeleteScreen(ModalScreen[bool]):
    """Simple confirmation modal for destructive delete actions."""

    DEFAULT_CSS = """
    ConfirmDeleteScreen {
        layer: overlay;
        align: center middle;
        background: rgba(17, 17, 17, 0.72);
    }
    """

    BINDINGS = [("escape", "dismiss(False)")]

    def __init__(self, node: SSH_Host | SSH_Group) -> None:
        self.node = node
        super().__init__()

    def compose(self) -> ComposeResult:
        node_type = "host" if isinstance(self.node, SSH_Host) else "group"
        with Vertical(id="confirm_delete_dialog"):
            yield Label(f"Delete SSH {node_type} '{self.node.name}'?", id="confirm_delete_label")
            with Horizontal(id="confirm_delete_buttons"):
                yield Button("Delete", variant="error", id="confirm_delete_yes")
                yield Button("Cancel", variant="primary", id="confirm_delete_no")

    @on(Button.Pressed, "#confirm_delete_yes")
    def confirm_yes(self) -> None:
        self.dismiss(True)

    @on(Button.Pressed, "#confirm_delete_no")
    def confirm_no(self) -> None:
        self.dismiss(False)
