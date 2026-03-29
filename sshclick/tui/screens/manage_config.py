from dataclasses import dataclass

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Select, Static

from sshclick.globals import DEFAULT_HOST_STYLE, ENABLED_HOST_STYLES


CONFIG_HOST_STYLE_DEFAULT = "__default__"


@dataclass
class ManageConfigRequest:
    """Normalized values returned by the SSHClick config editor drawer."""

    host_style: str | None


class ManageConfigScreen(ModalScreen[ManageConfigRequest | None]):
    """Right-side modal for editing SSHClick metadata config options."""

    CSS_PATH = "../styles/manage_config.tcss"
    BINDINGS = [("escape", "dismiss(None)")]


    def __init__(self, current_host_style: str | None) -> None:
        self.current_host_style = current_host_style
        super().__init__()


    def compose(self) -> ComposeResult:
        with Vertical(id="manage_config_dialog"):
            yield Label("SSHClick config", id="manage_config_title")
            yield Static(
                "Configure SSHClick metadata stored at the top of the SSH config file.",
                id="manage_config_note",
            )

            yield Label("Host display style", classes="form_label")
            yield Select(
                self._host_style_options(),
                value=self._initial_host_style_value(),
                allow_blank=False,
                id="manage_config_host_style",
            )
            yield Static(
                f"Default style when unset: {DEFAULT_HOST_STYLE}",
                id="manage_config_help",
            )

            yield Label(id="manage_config_error")

            with Horizontal(id="manage_config_buttons"):
                yield Button("Save", variant="primary", id="manage_config_submit")
                yield Button("Cancel", variant="default", id="manage_config_cancel")


    def on_mount(self) -> None:
        self.query_one("#manage_config_host_style", Select).focus()


    @on(Button.Pressed, "#manage_config_submit")
    def submit(self) -> None:
        """Return the normalized config selection from the guided form."""

        selected_value = self.query_one("#manage_config_host_style", Select).value
        if selected_value is Select.NULL:
            self._set_error("Host display style is required.")
            return

        host_style = None if selected_value == CONFIG_HOST_STYLE_DEFAULT else str(selected_value)
        self.dismiss(ManageConfigRequest(host_style=host_style))


    @on(Button.Pressed, "#manage_config_cancel")
    def cancel(self) -> None:
        self.dismiss(None)


    def _host_style_options(self) -> list[tuple[str, str]]:
        return [("Default (unset)", CONFIG_HOST_STYLE_DEFAULT), *[(style, style) for style in ENABLED_HOST_STYLES]]


    def _initial_host_style_value(self) -> str:
        return CONFIG_HOST_STYLE_DEFAULT if not self.current_host_style else self.current_host_style


    def _set_error(self, message: str) -> None:
        self.query_one("#manage_config_error", Label).update(message)
