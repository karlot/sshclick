from dataclasses import dataclass

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, ContentSwitcher, Input, Label, OptionList, Select, Static, Switch

from sshclick.core import HostType, PARAMS_WITH_ALLOWED_MULTIPLE_VALUES, SSH_Config, SSH_Group, SSH_Host
from sshclick.ssht.utils import discover_identity_files

from .add_parameter import AddParameterScreen, HostParameterRequest

FIXED_CREATE_HOST_PARAMS = {"hostname", "port", "user", "identityfile"}


@dataclass
class CreateHostRequest:
    """Normalized values returned by the create-host drawer."""

    name: str
    hostname: str
    port: str
    user: str
    identity_file: str
    group_name: str
    info_line: str
    create_group: bool
    extra_parameters: list[tuple[str, str]]


class CreateHostScreen(ModalScreen[CreateHostRequest | None]):
    """Right-side modal for creating a new host or pattern definition from the TUI."""

    CSS_PATH = "../styles/create_host.tcss"

    BINDINGS = [("escape", "dismiss(None)")]

    def __init__(self, sshconf: SSH_Config, current_node: SSH_Group | SSH_Host | None) -> None:
        self.sshconf = sshconf
        self.current_node = current_node
        self.identity_options = discover_identity_files(sshconf.ssh_config_file)
        self.extra_parameters: list[tuple[str, str]] = []
        self.editing_extra_parameter_index: int | None = None
        super().__init__()

    def compose(self) -> ComposeResult:
        default_group = self._default_group_name()

        with Vertical(id="create_host_dialog"):
            yield Label("Create SSH entry", id="create_host_title")
            yield Label("Detected type: Host", id="create_host_detected_type")

            yield Label("Name", classes="form_label")
            yield Input(placeholder="host alias or pattern such as lab-*", id="create_host_name")

            yield Label("Info line", classes="form_label")
            yield Input(placeholder="optional host note", id="create_host_info")

            yield Label("Hostname / Port", classes="form_label")
            with Horizontal(id="create_host_endpoint_row"):
                yield Input(placeholder="hostname or IP address", id="create_host_address")
                yield Input(placeholder="22", id="create_host_port", type="integer")

            yield Label("User", classes="form_label")
            yield Input(placeholder="ssh user", id="create_host_user")

            yield Label("Identity file", classes="form_label")
            yield Select(
                self.identity_options,
                prompt="Select identity file",
                allow_blank=True,
                value=Select.NULL,
                id="create_host_identity",
            )

            yield Label("Group", classes="form_label")
            with Vertical(id="create_host_group_section"):
                with Horizontal(id="create_host_group_switch_row"):
                    yield Label("Create new group", id="create_host_group_switch_label")
                    yield Switch(value=False, id="create_host_create_group")

                with ContentSwitcher(initial="create_host_group_existing_mode", id="create_host_group_mode"):
                    with Vertical(id="create_host_group_existing_mode"):
                        yield Select(
                            [(group.name, group.name) for group in self.sshconf.groups],
                            value=default_group,
                            allow_blank=False,
                            id="create_host_group_select",
                        )
                    with Vertical(id="create_host_group_new_mode"):
                        yield Input(value=default_group, placeholder="new group name", id="create_host_group_input")

            yield Label("Additional SSH parameters", classes="form_label")
            with Horizontal(id="create_host_param_buttons"):
                yield Button("Add parameter", variant="primary", id="create_host_add_param")
                yield Button("Edit selected", variant="primary", id="create_host_edit_param")
                yield Button("Remove selected", variant="primary", id="create_host_remove_param")
            yield Static("No additional parameters added.", id="create_host_extra_params_empty")
            yield OptionList(id="create_host_extra_params")

            yield Label(id="create_host_error")

            with Horizontal(id="create_host_buttons"):
                yield Button("Create", variant="primary", id="create_host_submit")
                yield Button("Cancel", variant="default", id="create_host_cancel")

    def on_mount(self) -> None:
        self.query_one("#create_host_name", Input).focus()

    @on(Button.Pressed, "#create_host_submit")
    def submit(self) -> None:
        """Validate the guided form and return normalized host creation values."""

        name = self.query_one("#create_host_name", Input).value.strip()
        group_name = self._selected_group_name()
        create_group = self.query_one("#create_host_create_group", Switch).value

        if not name:
            self._set_error("Host name is required.")
            self.query_one("#create_host_name", Input).focus()
            return
        if self.sshconf.check_host_by_name(name):
            self._set_error(f"Host '{name}' already exists.")
            self.query_one("#create_host_name", Input).focus()
            return
        if not group_name:
            self._set_error("Target group is required.")
            self._focus_group_field()
            return
        if not create_group and not self.sshconf.check_group_by_name(group_name):
            self._set_error(f"Group '{group_name}' does not exist.")
            self._focus_group_field()
            return

        identity_value = self.query_one("#create_host_identity", Select).value
        identity_file = "" if identity_value is Select.NULL else str(identity_value)

        self.dismiss(
            CreateHostRequest(
                name=name,
                hostname=self.query_one("#create_host_address", Input).value.strip(),
                port=self.query_one("#create_host_port", Input).value.strip(),
                user=self.query_one("#create_host_user", Input).value.strip(),
                identity_file=identity_file,
                group_name=group_name,
                info_line=self.query_one("#create_host_info", Input).value.strip(),
                create_group=create_group,
                extra_parameters=list(self.extra_parameters),
            )
        )

    @on(Button.Pressed, "#create_host_cancel")
    def cancel(self) -> None:
        self.dismiss(None)

    @on(Switch.Changed, "#create_host_create_group")
    def toggle_group_mode(self, event: Switch.Changed) -> None:
        """Swap between existing-group selection and new-group text entry."""

        switcher = self.query_one("#create_host_group_mode", ContentSwitcher)
        switcher.current = "create_host_group_new_mode" if event.value else "create_host_group_existing_mode"

    @on(Input.Changed, "#create_host_name")
    def update_detected_type(self, event: Input.Changed) -> None:
        """Reflect the inferred OpenSSH entry type from the current name."""

        detected_type = self._detected_host_type(event.value)
        self.query_one("#create_host_detected_type", Label).update(f"Detected type: {detected_type.value.title()}")

    @on(Button.Pressed, "#create_host_add_param")
    def add_parameter(self) -> None:
        """Open the guided extra-parameter modal."""

        self.editing_extra_parameter_index = None
        self.app.push_screen(AddParameterScreen(excluded_params=FIXED_CREATE_HOST_PARAMS), self._handle_parameter_result)

    @on(Button.Pressed, "#create_host_edit_param")
    def edit_parameter(self) -> None:
        """Edit the currently highlighted extra SSH parameter with the same guided modal."""

        option_list = self.query_one("#create_host_extra_params", OptionList)
        if option_list.option_count == 0 or option_list.highlighted is None:
            return

        self.editing_extra_parameter_index = option_list.highlighted
        name, value = self.extra_parameters[option_list.highlighted]
        self.app.push_screen(
            AddParameterScreen(HostParameterRequest(name=name, value=value), excluded_params=FIXED_CREATE_HOST_PARAMS),
            self._handle_parameter_result,
        )

    @on(Button.Pressed, "#create_host_remove_param")
    def remove_parameter(self) -> None:
        """Remove the currently highlighted extra SSH parameter."""

        option_list = self.query_one("#create_host_extra_params", OptionList)
        if option_list.option_count == 0 or option_list.highlighted is None:
            return

        del self.extra_parameters[option_list.highlighted]
        option_list.remove_option_at_index(option_list.highlighted)
        self._refresh_extra_parameter_list()

    def _handle_parameter_result(self, request: HostParameterRequest | None) -> None:
        """Validate and store an extra SSH parameter returned by the picker modal."""

        if request is None:
            self.editing_extra_parameter_index = None
            return

        editing_index = self.editing_extra_parameter_index
        param_key = request.name.lower()
        duplicate_count = sum(
            1
            for index, (name, _value) in enumerate(self.extra_parameters)
            if name.lower() == param_key and index != editing_index
        )
        if duplicate_count and param_key not in PARAMS_WITH_ALLOWED_MULTIPLE_VALUES:
            self._set_error(f"Parameter '{request.name}' is already defined in this form.")
            return

        if param_key == "hostname" and self.query_one("#create_host_address", Input).value.strip():
            self._set_error("Use the Hostname / IP field instead of adding HostName again.")
            return
        if param_key == "port" and self.query_one("#create_host_port", Input).value.strip():
            self._set_error("Use the Port field instead of adding Port again.")
            return
        if param_key == "user" and self.query_one("#create_host_user", Input).value.strip():
            self._set_error("Use the User field instead of adding User again.")
            return
        if param_key == "identityfile" and self.query_one("#create_host_identity", Select).value is not Select.NULL:
            self._set_error("Use the Identity file field instead of adding IdentityFile again.")
            return

        if editing_index is not None:
            self.extra_parameters[editing_index] = (request.name, request.value)
        else:
            self.extra_parameters.append((request.name, request.value))
            editing_index = len(self.extra_parameters) - 1

        self.editing_extra_parameter_index = None
        self._set_error("")
        self._refresh_extra_parameter_list(editing_index)

    def _default_group_name(self) -> str:
        if isinstance(self.current_node, SSH_Group):
            return self.current_node.name
        if isinstance(self.current_node, SSH_Host) and self.sshconf.check_group_by_name(self.current_node.group):
            return self.current_node.group
        if self.sshconf.check_group_by_name("default"):
            return "default"
        return self.sshconf.groups[0].name if self.sshconf.groups else "default"

    def _selected_group_name(self) -> str:
        if self.query_one("#create_host_create_group", Switch).value:
            return self.query_one("#create_host_group_input", Input).value.strip()

        group_value = self.query_one("#create_host_group_select", Select).value
        return "" if group_value is Select.NULL else str(group_value).strip()

    def _focus_group_field(self) -> None:
        if self.query_one("#create_host_create_group", Switch).value:
            self.query_one("#create_host_group_input", Input).focus()
        else:
            self.query_one("#create_host_group_select", Select).focus()

    def _detected_host_type(self, name: str) -> HostType:
        return HostType.PATTERN if "*" in name else HostType.NORMAL

    def _set_error(self, message: str) -> None:
        self.query_one("#create_host_error", Label).update(message)

    def _refresh_extra_parameter_list(self, highlight_index: int | None = None) -> None:
        """Refresh the extra-parameter preview list after add/remove actions."""

        option_list = self.query_one("#create_host_extra_params", OptionList)
        empty_state = self.query_one("#create_host_extra_params_empty", Static)

        if not self.extra_parameters:
            option_list.display = False
            empty_state.display = True
            return

        option_list.display = True
        empty_state.display = False
        option_list.set_options([f"{name} = {value}" for name, value in self.extra_parameters])
        if option_list.option_count == 0:
            return
        if highlight_index is None:
            option_list.highlighted = option_list.option_count - 1
        else:
            option_list.highlighted = min(highlight_index, option_list.option_count - 1)
