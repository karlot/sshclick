from dataclasses import dataclass

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, TextArea

from sshclick.core import SSH_Config, SSH_Group, SSH_Host


@dataclass
class ManageGroupRequest:
    """Normalized values returned by the shared group management drawer."""

    name: str
    desc: str
    info_text: str
    original_name: str | None = None


class ManageGroupScreen(ModalScreen[ManageGroupRequest | None]):
    """Right-side modal for creating or editing a group definition."""

    CSS_PATH = "../styles/manage_group.tcss"
    BINDINGS = [("escape", "dismiss(None)")]

    def __init__(
        self,
        sshconf: SSH_Config,
        current_node: SSH_Group | SSH_Host | None,
        *,
        editing_group: SSH_Group | None = None,
    ) -> None:
        self.sshconf = sshconf
        self.current_node = current_node
        self.editing_group = editing_group
        super().__init__()


    def compose(self) -> ComposeResult:
        title = "Edit group" if self.editing_group is not None else "Create group"
        submit_label = "Save" if self.editing_group is not None else "Create"

        with Vertical(id="manage_group_dialog"):
            yield Label(title, id="manage_group_title")

            yield Label("Name", classes="form_label")
            yield Input(value=self._initial_name(), placeholder="group name", id="manage_group_name")

            yield Label("Description", classes="form_label")
            yield Input(value=self._initial_desc(), placeholder="short description", id="manage_group_desc")

            yield Label("Info", classes="form_label")
            yield TextArea(
                self._initial_info_text(),
                soft_wrap=True,
                show_line_numbers=False,
                compact=True,
                placeholder="optional notes, one line per item",
                id="manage_group_info",
            )

            yield Label(id="manage_group_error")

            with Horizontal(id="manage_group_buttons"):
                yield Button(submit_label, variant="primary", id="manage_group_submit")
                yield Button("Cancel", variant="default", id="manage_group_cancel")


    def on_mount(self) -> None:
        self.query_one("#manage_group_name", Input).focus()


    @on(Button.Pressed, "#manage_group_submit")
    def submit(self) -> None:
        """Validate and return normalized group values for create or edit flows."""

        name = self.query_one("#manage_group_name", Input).value.strip()
        desc = self.query_one("#manage_group_desc", Input).value.strip()
        info_text = self.query_one("#manage_group_info", TextArea).text.strip()

        if not name:
            self._set_error("Group name is required.")
            self.query_one("#manage_group_name", Input).focus()
            return

        if self.editing_group is None and self.sshconf.check_group_by_name(name):
            self._set_error(f"Group '{name}' already exists.")
            self.query_one("#manage_group_name", Input).focus()
            return

        if self.editing_group is not None and name != self.editing_group.name and self.sshconf.check_group_by_name(name):
            self._set_error(f"Group '{name}' already exists.")
            self.query_one("#manage_group_name", Input).focus()
            return

        self.dismiss(
            ManageGroupRequest(
                name=name,
                desc=desc,
                info_text=info_text,
                original_name=None if self.editing_group is None else self.editing_group.name,
            )
        )


    @on(Button.Pressed, "#manage_group_cancel")
    def cancel(self) -> None:
        self.dismiss(None)


    def _set_error(self, message: str) -> None:
        self.query_one("#manage_group_error", Label).update(message)


    def _initial_name(self) -> str:
        return "" if self.editing_group is None else self.editing_group.name


    def _initial_desc(self) -> str:
        return "" if self.editing_group is None else self.editing_group.desc


    def _initial_info_text(self) -> str:
        if self.editing_group is None or not self.editing_group.info:
            return ""
        return "\n".join(str(item) for item in self.editing_group.info)
