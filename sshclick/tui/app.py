import os.path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header

from sshclick.globals import USER_SSH_CONFIG
from sshclick.core import SSH_Config, SSH_Group, SSH_Host
from sshclick.ops import SSHClickOpsError, create_group, create_host, delete_group, delete_host, delete_host_style, edit_group, edit_host, set_host_style
from sshclick.tui.screens import (
    ActionMenuScreen,
    ConfirmDeleteScreen,
    ManageConfigRequest,
    ManageConfigScreen,
    ManageGroupRequest,
    ManageGroupScreen,
    ManageHostRequest,
    ManageHostScreen,
)
from sshclick.tui.state import SSHNode, TUIState
from sshclick.tui.theme import SSHCLICK_DARK_THEME, register_sshclick_theme
from sshclick.tui.utils import copy_ssh_keys, reset_fingerprint, run_connect
from sshclick.tui.widgets import DetailsPane, NavigationTree, StatusBar, TreeStats
from sshclick.version import VERSION


DISPLAY_VERSION = VERSION.split("+", 1)[0]


class SSHTui(App):
    """Main Textual application for browsing and acting on SSHClick config data."""

    CSS_PATH = [
        "styles/base.tcss",
        "styles/layout.tcss",
        "styles/details.tcss",
        "styles/modals.tcss",
    ]
    TITLE = "SSHClick TUI"
    SUB_TITLE = f"SSH Config Browser · v{DISPLAY_VERSION}"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("a", "toggle_actions", "Actions"),
        ("e", "edit_selected", "Edit"),
        ("s", "connect('ssh')", "SSH"),
        ("f", "connect('sftp')", "SFTP"),
        ("d", "delete", "Delete"),
        ("r", "reload", "Reload"),
    ]


    def __init__(self, config_file: str = USER_SSH_CONFIG) -> None:
        super().__init__()
        config_path = os.path.expanduser(config_file)
        sshconf = SSH_Config(file=config_path).read().parse()
        self.state = TUIState(config_file=config_path, sshconf=sshconf)
        self.current_node: SSHNode = None
        self._tree_rebuilding = False


    def get_theme_variable_defaults(self) -> dict[str, str]:
        # Custom theme variables must exist before the stylesheet is parsed.
        return dict(SSHCLICK_DARK_THEME.variables)


    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="shell"):
            with Vertical(id="nav_column"):
                yield NavigationTree(self.state.sshconf, id="nav_tree")
                yield TreeStats(id="tree_stats")
            with Vertical(id="content_column"):
                yield StatusBar(id="status_bar")
                yield DetailsPane(self.state.sshconf, id="details_pane")
        yield Footer()


    def on_mount(self) -> None:
        register_sshclick_theme(self)
        self.theme = SSHCLICK_DARK_THEME.name
        self._refresh_view(rebuild_tree=True)
        self._focus_tree()


    def on_navigation_tree_node_highlighted(self, event) -> None:
        if self._tree_rebuilding:
            return
        self._set_current_node(self._event_node(event))


    def on_navigation_tree_node_submitted(self, event: NavigationTree.NodeSubmitted) -> None:
        if self._tree_rebuilding:
            return
        self._set_current_node(event.node_data)
        if isinstance(event.node_data, SSH_Host):
            self.action_toggle_actions()


    def on_navigation_tree_node_action_requested(self, event: NavigationTree.NodeActionRequested) -> None:
        """Open the action menu for the node requested by a right-click."""

        if self._tree_rebuilding:
            return
        self._set_current_node(event.node_data)
        self.action_toggle_actions()

    def on_navigation_tree_node_detail_tab_requested(self, event: NavigationTree.NodeDetailTabRequested) -> None:
        """Switch host detail tabs directly from left/right tree navigation."""

        if self._tree_rebuilding or not isinstance(self.current_node, SSH_Host):
            return

        details = self.query_one_optional(DetailsPane)
        if details is not None:
            details.show_host_tab(event.tab_id)


    # Compatibility bridge for older tests / event paths used by the previous TUI layout
    def on_tree_node_highlighted(self, event) -> None:
        if self._tree_rebuilding:
            return
        self._set_current_node(self._event_node(event))


    def _handle_action_menu_result(self, action_id: str | None) -> None:
        """
        Handle the action selected in the centered modal menu.

        The screen itself only returns an action id. This method keeps the real
        behavior mapping in one place so CLI-like actions, destructive flows,
        and future edit/create flows all go through the same app-level routing.
        """

        # Keep all action dispatching in one place so the modal stays dumb.
        if action_id is None:
            self._focus_tree()
            return
        if action_id == "act_reload":
            self.action_reload()
        elif action_id in {"act_ssh", "act_sftp", "act_copy_key", "act_reset_fp"}:
            self._handle_connection_action(action_id)
        elif action_id in {"act_delete_host", "act_delete_group"}:
            self.action_delete()
        elif action_id == "act_create_host":
            self.push_screen(ManageHostScreen(self.state.sshconf, self.current_node), self._handle_create_host_result)
            return
        elif action_id == "act_create_group":
            self.push_screen(ManageGroupScreen(self.state.sshconf, self.current_node), self._handle_create_group_result)
            return
        elif action_id == "act_edit_config":
            self.push_screen(ManageConfigScreen(self.state.sshconf.opts.get("host-style")), self._handle_edit_config_result)
            return
        elif action_id == "act_edit_host" and isinstance(self.current_node, SSH_Host):
            self.push_screen(
                ManageHostScreen(self.state.sshconf, self.current_node, editing_host=self.current_node),
                self._handle_edit_host_result,
            )
            return
        elif action_id == "act_edit_group" and isinstance(self.current_node, SSH_Group):
            self.push_screen(
                ManageGroupScreen(self.state.sshconf, self.current_node, editing_group=self.current_node),
                self._handle_edit_group_result,
            )
            return
        elif action_id in {"act_edit_host", "act_edit_group"}:
            self._handle_unimplemented_action()
        self._focus_tree()


    def action_quit(self) -> None:
        self.exit(0)


    def action_toggle_actions(self) -> None:
        self.push_screen(
            ActionMenuScreen(
                self.current_node,
                is_read_only=self.state.is_read_only,
                read_only_reason=self.state.read_only_reason,
            ),
            self._handle_action_menu_result,
        )


    def action_edit_selected(self) -> None:
        """Open the appropriate editor for the currently selected host or group."""

        if self.current_node is None:
            self.notify("Select host or group first", severity="warning")
            return
        if self.state.is_read_only:
            self.notify(self.state.read_only_reason, title="Read-only config", severity="warning")
            return

        if isinstance(self.current_node, SSH_Host):
            self.push_screen(
                ManageHostScreen(self.state.sshconf, self.current_node, editing_host=self.current_node),
                self._handle_edit_host_result,
            )
            return

        if isinstance(self.current_node, SSH_Group):
            self.push_screen(
                ManageGroupScreen(self.state.sshconf, self.current_node, editing_group=self.current_node),
                self._handle_edit_group_result,
            )
            return


    def action_connect(self, prog: str) -> None:
        run_connect(self, prog, self.current_node)


    def action_reload(self) -> None:
        """
        Reload the parsed config and restore the previous selection when possible.

        This is the main refresh path after external writes or destructive TUI
        actions. Selection is restored by node name so the UI lands roughly
        where the user was before the reload.
        """

        selected_name = self._selected_name()
        self.state.sshconf = SSH_Config(file=self.state.config_file).read().parse()
        self._refresh_view(preferred_name=selected_name, rebuild_tree=True)
        self.notify("Configuration reloaded", severity="information")


    def action_delete(self) -> None:
        if not self._can_delete_current_node():
            return

        self.push_screen(ConfirmDeleteScreen(self.current_node), self._delete_confirmed)


    def _delete_confirmed(self, confirmed: bool | None) -> None:
        if not confirmed or self.current_node is None:
            return

        preferred_name = self._preferred_name_after_delete()
        item_type, deleted_name = self._delete_current_node()

        if self.state.sshconf.generate_ssh_config():
            self.notify(f"Deleted {item_type}: {deleted_name}", severity="information")
        self.current_node = None
        self.state.current_node = None
        self._refresh_view(preferred_name=preferred_name, rebuild_tree=True)
        self._focus_tree()


    def _handle_create_host_result(self, request: ManageHostRequest | None) -> None:
        """
        Persist a new host from the create drawer and refresh the UI around it.

        The drawer only collects and validates user input. The real mutation is
        still routed through the shared ops layer so CLI and TUI keep using the
        same write semantics.
        """

        if request is None:
            self._focus_tree()
            return

        try:
            created_host = create_host(
                self.state.sshconf,
                request.name,
                address=request.hostname or None,
                user=request.user or None,
                info=self._request_info_lines(request),
                parameters=self._request_parameters(request),
                target_group_name=request.group_name,
                force_group=request.create_group,
            )
        except SSHClickOpsError as exc:
            self.notify(str(exc), title="Create host failed", severity="error")
            self._focus_tree()
            return

        if self.state.sshconf.generate_ssh_config():
            self.notify(f"Created host: {created_host.name}", severity="information")

        self._refresh_view(preferred_name=created_host.name, rebuild_tree=True)
        self._focus_tree()


    def _handle_create_group_result(self, request: ManageGroupRequest | None) -> None:
        """Persist a new group from the drawer and focus it in the tree."""

        if request is None:
            self._focus_tree()
            return

        try:
            created_group = create_group(
                self.state.sshconf,
                request.name,
                desc=request.desc,
                info=self._request_info_lines(request),
            )
        except SSHClickOpsError as exc:
            self.notify(str(exc), title="Create group failed", severity="error")
            self._focus_tree()
            return

        if self.state.sshconf.generate_ssh_config():
            self.notify(f"Created group: {created_group.name}", severity="information")

        self._refresh_view(preferred_name=created_group.name, rebuild_tree=True)
        self._focus_tree()


    def _handle_edit_config_result(self, request: ManageConfigRequest | None) -> None:
        """Persist SSHClick config metadata edited from the TUI drawer."""

        if request is None:
            self._focus_tree()
            return

        try:
            if request.host_style is None:
                if "host-style" in self.state.sshconf.opts:
                    delete_host_style(self.state.sshconf)
            else:
                set_host_style(self.state.sshconf, request.host_style)
        except SSHClickOpsError as exc:
            self.notify(str(exc), title="Update config failed", severity="error")
            self._focus_tree()
            return

        if self.state.sshconf.generate_ssh_config():
            self.notify("Updated SSHClick config", severity="information")

        self._refresh_view()
        self._focus_tree()


    def _handle_edit_host_result(self, request: ManageHostRequest | None) -> None:
        """Persist an edited host definition from the guided drawer and refresh the UI."""

        if request is None or request.original_name is None:
            self._focus_tree()
            return

        try:
            edited_host = edit_host(
                self.state.sshconf,
                request.original_name,
                new_name=request.name,
                address=request.hostname or None,
                user=request.user or None,
                info=self._request_info_lines(request),
                parameters=self._request_parameters(request),
                target_group_name=request.group_name,
                force_group=request.create_group,
            )
        except SSHClickOpsError as exc:
            self.notify(str(exc), title="Edit host failed", severity="error")
            self._focus_tree()
            return

        if self.state.sshconf.generate_ssh_config():
            self.notify(f"Updated host: {edited_host.name}", severity="information")

        self._refresh_view(preferred_name=edited_host.name, rebuild_tree=True)
        self._focus_tree()


    def _handle_edit_group_result(self, request: ManageGroupRequest | None) -> None:
        """Persist an edited group definition from the guided drawer and refresh the UI."""

        if request is None or request.original_name is None:
            self._focus_tree()
            return

        try:
            edited_group = edit_group(
                self.state.sshconf,
                request.original_name,
                new_name=request.name,
                desc=request.desc,
                info=self._request_info_lines(request),
            )
        except SSHClickOpsError as exc:
            self.notify(str(exc), title="Edit group failed", severity="error")
            self._focus_tree()
            return

        if self.state.sshconf.generate_ssh_config():
            self.notify(f"Updated group: {edited_group.name}", severity="information")

        self._refresh_view(preferred_name=edited_group.name, rebuild_tree=True)
        self._focus_tree()


    def _set_current_node(self, node: SSHNode) -> None:
        self.current_node = node
        self.state.current_node = node
        self._refresh_view()


    def _refresh_view(self, preferred_name: str | None = None, *, rebuild_tree: bool = False) -> None:
        """
        Refresh every widget that depends on config state or current selection.

        This is the central synchronization point for the TUI. It updates the
        tree, details pane, status bar, and left-hand statistics while avoiding
        unnecessary tree rebuilds that would collapse expanded groups.
        """
        selection_name = preferred_name or self._selected_name()

        nav_tree = self.query_one_optional(NavigationTree)
        if nav_tree is not None and rebuild_tree:
            expanded_group_names = nav_tree.get_expanded_group_names()
            if selection_name and self.state.sshconf.check_group_by_name(selection_name) and selection_name not in expanded_group_names:
                expanded_group_names.append(selection_name)
            # Rebuild the tree only on config reloads; doing it on every highlight
            # would collapse expanded groups and make navigation unusable.
            self._tree_rebuilding = True
            nav_tree.rebuild(self.state.sshconf)
            nav_tree.expand_groups(expanded_group_names)
            nav_tree.select_node_by_name(selection_name)
            self.call_after_refresh(self._finish_tree_rebuild, selection_name)

        if rebuild_tree or preferred_name is not None:
            self._restore_selection(selection_name)

        details = self.query_one_optional(DetailsPane)
        if details is not None:
            details.update_config(self.state.sshconf)
            details.update_node(self.current_node)

        status = self.query_one_optional(StatusBar)
        if status is not None:
            status.update_state(self.state)

        tree_stats = self.query_one_optional(TreeStats)
        if tree_stats is not None:
            tree_stats.update_state(self.state)


    def _find_node_by_name(self, name: str) -> SSHNode:
        if self.state.sshconf.check_host_by_name(name):
            return self.state.sshconf.get_host_by_name(name)
        if self.state.sshconf.check_group_by_name(name):
            return self.state.sshconf.get_group_by_name(name)
        return None


    def _event_node(self, event) -> SSHNode:
        return event.node.data if hasattr(event, "node") else getattr(event, "node_data", None)


    def _focus_tree(self) -> None:
        self.query_one(NavigationTree).focus_tree()


    def _selected_name(self) -> str | None:
        return self.current_node.name if self.current_node is not None else None


    def _request_parameters(self, request: ManageHostRequest) -> list[tuple[str, str]]:
        """Build the parameter list shared by create and edit host flows."""

        parameters: list[tuple[str, str]] = list(request.extra_parameters)
        if request.port:
            parameters.append(("port", request.port))
        if request.identity_file:
            parameters.append(("identityfile", request.identity_file))
        return parameters


    def _request_info_lines(self, request: ManageHostRequest | ManageGroupRequest) -> tuple[str, ...]:
        """Convert multiline textarea content into stored SSHClick info lines."""

        if not request.info_text:
            return ()

        return tuple(line.strip() for line in request.info_text.splitlines() if line.strip())


    def _handle_connection_action(self, action_id: str) -> None:
        if action_id == "act_ssh":
            self.action_connect("ssh")
        elif action_id == "act_sftp":
            self.action_connect("sftp")
        elif action_id == "act_copy_key" and self.current_node is not None:
            copy_ssh_keys(self, self.current_node)
        elif action_id == "act_reset_fp" and self.current_node is not None:
            reset_fingerprint(self, self.current_node)


    def _handle_unimplemented_action(self) -> None:
        if self.state.is_read_only:
            self.notify(self.state.read_only_reason, title="Read-only config", severity="warning")
            return
        self.notify("This flow will be implemented in the next TUI phase.", title="Not implemented", severity="information")


    def _can_delete_current_node(self) -> bool:
        if self.current_node is None:
            self.notify("Select host or group first", severity="warning")
            return False
        if self.state.is_read_only:
            self.notify(self.state.read_only_reason, title="Read-only config", severity="warning")
            return False
        if isinstance(self.current_node, SSH_Group) and self.current_node.name == "default":
            self.notify("You cannot delete the default group", severity="warning")
            return False
        return True


    def _delete_current_node(self) -> tuple[str, str]:
        if isinstance(self.current_node, SSH_Group):
            deleted_group = delete_group(self.state.sshconf, self.current_node.name)
            return ("group", deleted_group.name)
        return self._delete_current_host()


    def _delete_current_host(self) -> tuple[str, str]:
        deleted_host = delete_host(self.state.sshconf, self.current_node.name)
        return ("host", deleted_host.name)


    def _preferred_name_after_delete(self) -> str | None:
        """Choose a sensible selection target after deleting the current node."""

        if isinstance(self.current_node, SSH_Host):
            return self.current_node.group

        if self.state.sshconf.check_group_by_name("default") and self.current_node.name != "default":
            return "default"

        for group in self.state.sshconf.groups:
            if group.name != self.current_node.name:
                return group.name

        return None


    def _restore_selection(self, preferred_name: str | None) -> None:
        self.current_node = self._find_node_by_name(preferred_name) if preferred_name is not None else None
        self.state.current_node = self.current_node


    def _finish_tree_rebuild(self, preferred_name: str | None) -> None:
        """Release the rebuild guard after queued tree events and restore selection once more."""

        nav_tree = self.query_one_optional(NavigationTree)
        if nav_tree is not None:
            nav_tree.select_node_by_name(preferred_name)

        self._restore_selection(preferred_name)

        details = self.query_one_optional(DetailsPane)
        if details is not None:
            details.update_node(self.current_node)

        self._tree_rebuilding = False
