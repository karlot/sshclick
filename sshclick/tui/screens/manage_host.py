from dataclasses import dataclass

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, ContentSwitcher, Input, Label, OptionList, Select, Static, Switch, TextArea

from sshclick.core import ALL_PARAM_SPECS, HostType, PARAMS_WITH_ALLOWED_MULTIPLE_VALUES, SSH_Config, SSH_Group, SSH_Host
from sshclick.tui.utils import discover_identity_files

from .add_parameter import AddParameterScreen, HostParameterRequest

FIXED_MANAGE_HOST_PARAMS = {"hostname", "port", "user", "identityfile"}


@dataclass
class ManageHostRequest:
    """Normalized values returned by the shared host management drawer."""

    name: str
    hostname: str
    port: str
    user: str
    identity_file: str
    group_name: str
    info_text: str
    create_group: bool
    extra_parameters: list[tuple[str, str]]
    original_name: str | None = None


class ManageHostScreen(ModalScreen[ManageHostRequest | None]):
    """Right-side modal for creating or editing a host or pattern definition."""

    CSS_PATH = "../styles/manage_host.tcss"
    BINDINGS = [("escape", "dismiss(None)")]

    def __init__(
        self,
        sshconf: SSH_Config,
        current_node: SSH_Group | SSH_Host | None,
        *,
        editing_host: SSH_Host | None = None,
    ) -> None:
        self.sshconf = sshconf
        self.current_node = current_node
        self.editing_host = editing_host
        self.identity_options = self._build_identity_options()
        self.extra_parameters: list[tuple[str, str]] = []
        self.editing_extra_parameter_index: int | None = None
        super().__init__()

    def compose(self) -> ComposeResult:
        default_group = self._default_group_name()
        title = "Edit SSH entry" if self.editing_host is not None else "Create SSH entry"
        submit_label = "Save" if self.editing_host is not None else "Create"

        with Vertical(id="manage_host_dialog"):
            yield Label(title, id="manage_host_title")
            yield Label(f"Detected type: {self._detected_type_label(self._detected_host_type(self._initial_name()))}", id="manage_host_detected_type")

            yield Label("Name", classes="form_label")
            yield Input(value=self._initial_name(), placeholder="host alias or pattern such as lab-*", id="manage_host_name")

            yield Label("Info line", classes="form_label")
            yield TextArea(
                self._initial_info_text(),
                soft_wrap=True,
                show_line_numbers=False,
                compact=True,
                placeholder="optional notes, one line per item",
                id="manage_host_info",
            )

            yield Label("Hostname / Port", classes="form_label")
            with Horizontal(id="manage_host_endpoint_row"):
                yield Input(value=self._initial_param_value("hostname"), placeholder="hostname or IP address", id="manage_host_address")
                yield Input(value=self._initial_param_value("port"), placeholder="22", id="manage_host_port", type="integer")

            yield Label("User", classes="form_label")
            yield Input(value=self._initial_param_value("user"), placeholder="ssh user", id="manage_host_user")

            yield Label("Identity file", classes="form_label")
            yield Select(
                self.identity_options,
                prompt="Select identity file",
                allow_blank=True,
                value=self._initial_identity_value(),
                id="manage_host_identity",
            )

            yield Label("Group", classes="form_label")
            with Vertical(id="manage_host_group_section"):
                with Horizontal(id="manage_host_group_switch_row"):
                    yield Label("Create new group", id="manage_host_group_switch_label")
                    yield Switch(value=False, id="manage_host_create_group")

                with ContentSwitcher(initial="manage_host_group_existing_mode", id="manage_host_group_mode"):
                    with Vertical(id="manage_host_group_existing_mode"):
                        yield Select(
                            [(group.name, group.name) for group in self.sshconf.groups],
                            value=default_group,
                            allow_blank=False,
                            id="manage_host_group_select",
                        )
                    with Vertical(id="manage_host_group_new_mode"):
                        yield Input(value=default_group, placeholder="new group name", id="manage_host_group_input")

            yield Label("Additional SSH parameters", classes="form_label")
            with Horizontal(id="manage_host_param_buttons"):
                yield Button("Add parameter", variant="primary", id="manage_host_add_param")
                yield Button("Edit selected", variant="primary", id="manage_host_edit_param")
                yield Button("Remove selected", variant="primary", id="manage_host_remove_param")
            yield Static("No additional parameters added.", id="manage_host_extra_params_empty")
            yield OptionList(id="manage_host_extra_params")

            yield Label(id="manage_host_error")

            with Horizontal(id="manage_host_buttons"):
                yield Button(submit_label, variant="primary", id="manage_host_submit")
                yield Button("Cancel", variant="default", id="manage_host_cancel")

    def on_mount(self) -> None:
        self.extra_parameters = self._initial_extra_parameters()
        self._refresh_extra_parameter_list(0 if self.extra_parameters else None)
        self.query_one("#manage_host_name", Input).focus()

    @on(Button.Pressed, "#manage_host_submit")
    def submit(self) -> None:
        """Validate the guided form and return normalized host creation values."""

        name = self.query_one("#manage_host_name", Input).value.strip()
        group_name = self._selected_group_name()
        create_group = self.query_one("#manage_host_create_group", Switch).value

        if not name:
            self._set_error("Host name is required.")
            self.query_one("#manage_host_name", Input).focus()
            return
        if self.editing_host is None and self.sshconf.check_host_by_name(name):
            self._set_error(f"Host '{name}' already exists.")
            self.query_one("#manage_host_name", Input).focus()
            return
        if self.editing_host is not None and name != self.editing_host.name and self.sshconf.check_host_by_name(name):
            self._set_error(f"Host '{name}' already exists.")
            self.query_one("#manage_host_name", Input).focus()
            return
        if not group_name:
            self._set_error("Target group is required.")
            self._focus_group_field()
            return
        if not create_group and not self.sshconf.check_group_by_name(group_name):
            self._set_error(f"Group '{group_name}' does not exist.")
            self._focus_group_field()
            return

        identity_value = self.query_one("#manage_host_identity", Select).value
        identity_file = "" if identity_value is Select.NULL else str(identity_value)

        self.dismiss(
            ManageHostRequest(
                name=name,
                hostname=self.query_one("#manage_host_address", Input).value.strip(),
                port=self.query_one("#manage_host_port", Input).value.strip(),
                user=self.query_one("#manage_host_user", Input).value.strip(),
                identity_file=identity_file,
                group_name=group_name,
                info_text=self.query_one("#manage_host_info", TextArea).text.strip(),
                create_group=create_group,
                extra_parameters=list(self.extra_parameters),
                original_name=None if self.editing_host is None else self.editing_host.name,
            )
        )

    @on(Button.Pressed, "#manage_host_cancel")
    def cancel(self) -> None:
        self.dismiss(None)

    @on(Switch.Changed, "#manage_host_create_group")
    def toggle_group_mode(self, event: Switch.Changed) -> None:
        """Swap between existing-group selection and new-group text entry."""

        switcher = self.query_one("#manage_host_group_mode", ContentSwitcher)
        switcher.current = "manage_host_group_new_mode" if event.value else "manage_host_group_existing_mode"

    @on(Input.Changed, "#manage_host_name")
    def update_detected_type(self, event: Input.Changed) -> None:
        """Reflect the inferred OpenSSH entry type from the current name."""

        detected_type = self._detected_host_type(event.value)
        self.query_one("#manage_host_detected_type", Label).update(f"Detected type: {self._detected_type_label(detected_type)}")

    @on(Button.Pressed, "#manage_host_add_param")
    def add_parameter(self) -> None:
        """Open the guided extra-parameter modal."""

        self.editing_extra_parameter_index = None
        self.app.push_screen(AddParameterScreen(excluded_params=FIXED_MANAGE_HOST_PARAMS), self._handle_parameter_result)

    @on(Button.Pressed, "#manage_host_edit_param")
    def edit_parameter(self) -> None:
        """Edit the currently highlighted extra SSH parameter with the same guided modal."""

        option_list = self.query_one("#manage_host_extra_params", OptionList)
        if option_list.option_count == 0 or option_list.highlighted is None:
            return

        self.editing_extra_parameter_index = option_list.highlighted
        name, value = self.extra_parameters[option_list.highlighted]
        self.app.push_screen(
            AddParameterScreen(HostParameterRequest(name=name, value=value), excluded_params=FIXED_MANAGE_HOST_PARAMS),
            self._handle_parameter_result,
        )

    @on(Button.Pressed, "#manage_host_remove_param")
    def remove_parameter(self) -> None:
        """Remove the currently highlighted extra SSH parameter."""

        option_list = self.query_one("#manage_host_extra_params", OptionList)
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

        if param_key == "hostname" and self.query_one("#manage_host_address", Input).value.strip():
            self._set_error("Use the Hostname / IP field instead of adding HostName again.")
            return
        if param_key == "port" and self.query_one("#manage_host_port", Input).value.strip():
            self._set_error("Use the Port field instead of adding Port again.")
            return
        if param_key == "user" and self.query_one("#manage_host_user", Input).value.strip():
            self._set_error("Use the User field instead of adding User again.")
            return
        if param_key == "identityfile" and self.query_one("#manage_host_identity", Select).value is not Select.NULL:
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
        if self.editing_host is not None and self.sshconf.check_group_by_name(self.editing_host.group):
            return self.editing_host.group
        if isinstance(self.current_node, SSH_Group):
            return self.current_node.name
        if isinstance(self.current_node, SSH_Host) and self.sshconf.check_group_by_name(self.current_node.group):
            return self.current_node.group
        if self.sshconf.check_group_by_name("default"):
            return "default"
        return self.sshconf.groups[0].name if self.sshconf.groups else "default"

    def _selected_group_name(self) -> str:
        if self.query_one("#manage_host_create_group", Switch).value:
            return self.query_one("#manage_host_group_input", Input).value.strip()

        group_value = self.query_one("#manage_host_group_select", Select).value
        return "" if group_value is Select.NULL else str(group_value).strip()

    def _focus_group_field(self) -> None:
        if self.query_one("#manage_host_create_group", Switch).value:
            self.query_one("#manage_host_group_input", Input).focus()
        else:
            self.query_one("#manage_host_group_select", Select).focus()

    def _detected_host_type(self, name: str) -> HostType:
        return HostType.PATTERN if "*" in name else HostType.NORMAL

    def _detected_type_label(self, host_type: HostType) -> str:
        return "Pattern" if host_type == HostType.PATTERN else "Host"

    def _set_error(self, message: str) -> None:
        self.query_one("#manage_host_error", Label).update(message)

    def _initial_name(self) -> str:
        return "" if self.editing_host is None else self.editing_host.name

    def _initial_info_text(self) -> str:
        if self.editing_host is None or not self.editing_host.info:
            return ""
        return "\n".join(str(item) for item in self.editing_host.info)

    def _initial_param_value(self, param: str) -> str:
        if self.editing_host is None:
            return ""
        value = self.editing_host.params.get(param, "")
        if isinstance(value, list):
            return "" if not value else str(value[0])
        return str(value)

    def _initial_identity_value(self):
        identity_value = self._initial_param_value("identityfile")
        return Select.NULL if not identity_value else identity_value

    def _build_identity_options(self) -> list[tuple[str, str]]:
        options = list(discover_identity_files(self.sshconf.ssh_config_file))
        current_value = self._initial_param_value("identityfile")
        if current_value and current_value not in {value for _label, value in options}:
            options.append((current_value, current_value))
        return options

    def _initial_extra_parameters(self) -> list[tuple[str, str]]:
        if self.editing_host is None:
            return []

        extra_parameters: list[tuple[str, str]] = []
        for name, value in self.editing_host.params.items():
            if name in {"hostname", "port", "user"}:
                continue
            if name == "identityfile":
                if isinstance(value, list):
                    extra_parameters.extend((self._canonical_param_name(name), item) for item in value[1:])
                continue
            if isinstance(value, list):
                extra_parameters.extend((self._canonical_param_name(name), item) for item in value)
            else:
                extra_parameters.append((self._canonical_param_name(name), value))
        return extra_parameters

    def _canonical_param_name(self, param: str) -> str:
        for known_name in ALL_PARAM_SPECS:
            if known_name.lower() == param.lower():
                return known_name
        return param

    def _refresh_extra_parameter_list(self, highlight_index: int | None = None) -> None:
        """Refresh the extra-parameter preview list after add/remove actions."""

        option_list = self.query_one("#manage_host_extra_params", OptionList)
        empty_state = self.query_one("#manage_host_extra_params_empty", Static)

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
