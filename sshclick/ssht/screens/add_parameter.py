from dataclasses import dataclass

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, ContentSwitcher, Input, Label, Select, Static

from sshclick.core import ALL_PARAM_SPECS, get_param_choices, get_param_description


@dataclass
class HostParameterRequest:
    """Normalized SSH parameter values returned by the add-parameter modal."""

    name: str
    value: str


class AddParameterScreen(ModalScreen[HostParameterRequest | None]):
    """Centered modal for choosing an extra SSH parameter during host creation."""

    CSS_PATH = "../styles/add_parameter.tcss"

    DEFAULT_CSS = """
    AddParameterScreen {
        layer: overlay;
        align: center middle;
        background: rgba(17, 17, 17, 0.72);
    }
    """

    BINDINGS = [("escape", "dismiss(None)")]

    def __init__(self, initial: HostParameterRequest | None = None, excluded_params: set[str] | None = None) -> None:
        self.initial = initial
        self.excluded_params = set() if excluded_params is None else {param.lower() for param in excluded_params}
        super().__init__()

    def compose(self) -> ComposeResult:
        title = "Edit SSH parameter" if self.initial is not None else "Add SSH parameter"
        submit_label = "Save" if self.initial is not None else "Add"

        with Vertical(id="add_param_dialog"):
            yield Label(title, id="add_param_title")
            yield Label("Parameter", classes="form_label")
            yield Select(
                self._parameter_options(),
                prompt="Select SSH parameter",
                allow_blank=True,
                value=Select.NULL if self.initial is None else self.initial.name,
                id="add_param_name",
            )
            yield Static("", id="add_param_description")
            yield Label("Value", classes="form_label")
            with ContentSwitcher(initial="add_param_value_input_mode", id="add_param_value_mode"):
                with Vertical(id="add_param_value_input_mode"):
                    yield Input(placeholder="parameter value", id="add_param_value_input")
                with Vertical(id="add_param_value_select_mode"):
                    yield Select((), prompt="Select value", allow_blank=True, value=Select.NULL, id="add_param_value_select")

            yield Label(id="add_param_error")

            with Horizontal(id="add_param_buttons"):
                yield Button(submit_label, variant="primary", id="add_param_submit")
                yield Button("Cancel", variant="default", id="add_param_cancel")

    def on_mount(self) -> None:
        self.query_one("#add_param_name", Select).focus()
        if self.initial is not None:
            self.call_after_refresh(self._apply_parameter_state, self.initial.name, self.initial.value)

    @on(Select.Changed, "#add_param_name")
    def update_value_editor(self, event: Select.Changed) -> None:
        """Swap the value editor based on whether the selected parameter has fixed choices."""

        if event.value is Select.NULL:
            self.query_one("#add_param_value_mode", ContentSwitcher).current = "add_param_value_input_mode"
            self.query_one("#add_param_description", Static).update("")
            return

        self._apply_parameter_state(str(event.value))

    @on(Button.Pressed, "#add_param_submit")
    def submit(self) -> None:
        """Validate and return the chosen SSH parameter."""

        name_value = self.query_one("#add_param_name", Select).value
        if name_value is Select.NULL:
            self._set_error("Parameter is required.")
            self.query_one("#add_param_name", Select).focus()
            return

        name = str(name_value)
        choices = get_param_choices(name)
        if choices:
            value_select = self.query_one("#add_param_value_select", Select)
            if value_select.value is Select.NULL:
                self._set_error("Parameter value is required.")
                value_select.focus()
                return
            value = str(value_select.value)
        else:
            value_input = self.query_one("#add_param_value_input", Input)
            value = value_input.value.strip()
            if not value:
                self._set_error("Parameter value is required.")
                value_input.focus()
                return

        self.dismiss(HostParameterRequest(name=name, value=value))

    @on(Button.Pressed, "#add_param_cancel")
    def cancel(self) -> None:
        self.dismiss(None)

    def _set_error(self, message: str) -> None:
        self.query_one("#add_param_error", Label).update(message)

    def _apply_parameter_state(self, name: str, value: str = "") -> None:
        """Update the description and value editor for the selected SSH parameter."""

        self.query_one("#add_param_description", Static).update(get_param_description(name))
        choices = get_param_choices(name)
        switcher = self.query_one("#add_param_value_mode", ContentSwitcher)

        if choices:
            value_select = self.query_one("#add_param_value_select", Select)
            value_select.set_options([(choice, choice) for choice in choices])
            value_select.value = Select.NULL if not value else value
            switcher.current = "add_param_value_select_mode"
            return

        value_input = self.query_one("#add_param_value_input", Input)
        value_input.value = value
        switcher.current = "add_param_value_input_mode"

    def _parameter_options(self) -> list[tuple[str, str]]:
        """Return selectable SSH parameters, excluding ones already covered by fixed form fields."""

        initial_name = None if self.initial is None else self.initial.name
        return [
            (param, param)
            for param in sorted(ALL_PARAM_SPECS)
            if param.lower() not in self.excluded_params or param == initial_name
        ]
