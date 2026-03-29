from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Label, OptionList, Static
from textual.widgets.option_list import Option

from sshclick.core import HostType, SSH_Group
from sshclick.ssht.state import SSHNode


class ActionMenuScreen(ModalScreen[str | None]):
    """Centered action picker for the current tree selection."""

    DEFAULT_CSS = """
    ActionMenuScreen {
        layer: overlay;
        align: center middle;
        background: rgba(17, 17, 17, 0.72);
    }
    """

    BINDINGS = [("escape", "dismiss(None)")]

    def __init__(self, node: SSHNode, *, is_read_only: bool, read_only_reason: str) -> None:
        self.node = node
        self.is_read_only = is_read_only
        self.read_only_reason = read_only_reason
        super().__init__()

    def compose(self) -> ComposeResult:
        context = "No active selection" if self.node is None else f"Selected: {self.node.name}"
        note = self.read_only_reason if self.is_read_only and self.read_only_reason else ""

        with Vertical(id="action_menu_dialog"):
            yield Label("Actions", id="action_menu_title")
            yield Static(context, id="action_menu_context")
            if self.is_read_only:
                yield Static(note, id="action_menu_note")
            yield OptionList(*self._build_options(), id="action_menu_options")


    def on_mount(self) -> None:
        self.query_one(OptionList).focus()


    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        if event.option_id == "act_close":
            self.dismiss(None)
            return
        self.dismiss(event.option_id)


    def _build_options(self) -> list[Option | None]:
        """Return the option list that matches the current selection."""

        if self.node is None:
            return [
                Option("Create new host", id="act_create_host", disabled=True),
                Option("Create new group", id="act_create_group", disabled=True),
                None,
                Option("Reload configuration", id="act_reload"),
                Option("Close", id="act_close"),
            ]

        if isinstance(self.node, SSH_Group):
            return [
                Option("Edit current group", id="act_edit_group", disabled=self.is_read_only),
                Option("Delete current group", id="act_delete_group", disabled=self.is_read_only or self.node.name == "default"),
                None,
                Option("Create new host", id="act_create_host", disabled=self.is_read_only),
                Option("Create new group", id="act_create_group", disabled=self.is_read_only),
                None,
                Option("Reload configuration", id="act_reload"),
                Option("Close", id="act_close"),
            ]

        return [
            Option("SSH to current host", id="act_ssh", disabled=self.node.type != HostType.NORMAL),
            Option("SFTP to current host", id="act_sftp", disabled=self.node.type != HostType.NORMAL),
            Option("Copy SSH key to current host", id="act_copy_key", disabled=self.node.type != HostType.NORMAL),
            Option("Reset local fingerprints for host", id="act_reset_fp", disabled=self.node.type != HostType.NORMAL),
            None,
            Option("Edit current host", id="act_edit_host", disabled=self.is_read_only),
            Option("Delete current host", id="act_delete_host", disabled=self.is_read_only),
            None,
            Option("Create new host", id="act_create_host", disabled=self.is_read_only),
            Option("Create new group", id="act_create_group", disabled=self.is_read_only),
            None,
            Option("Reload configuration", id="act_reload"),
            Option("Close", id="act_close"),
        ]
