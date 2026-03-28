import os.path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header

from sshclick.globals import USER_SSH_CONFIG
from sshclick.sshc import HostType, SSH_Config, SSH_Group
from sshclick.ssht.screens import ActionMenuScreen, ConfirmDeleteScreen
from sshclick.ssht.state import SSHNode, TUIState
from sshclick.ssht.theme import SSHCLICK_DARK_THEME, register_sshclick_theme
from sshclick.ssht.utils import copy_ssh_keys, reset_fingerprint, run_connect
from sshclick.ssht.widgets import DetailsPane, NavigationTree, StatusBar, TreeStats


class SSHTui(App):
    """Main Textual application for browsing and acting on SSHClick config data."""

    CSS_PATH = "app.tcss"
    TITLE = "SSHClick"
    SUB_TITLE = "Browser"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("a", "toggle_actions", "Actions"),
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
        self._set_current_node(self._event_node(event))

    def on_navigation_tree_node_submitted(self, event: NavigationTree.NodeSubmitted) -> None:
        self._set_current_node(event.node_data)

    # Compatibility bridge for older tests / event paths used by the previous TUI layout
    def on_tree_node_highlighted(self, event) -> None:
        self._set_current_node(self._event_node(event))

    def _handle_action_menu_result(self, action_id: str | None) -> None:
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
        elif action_id in {"act_edit_host", "act_edit_group", "act_create_host", "act_create_group"}:
            self._handle_unimplemented_action()
        self._focus_tree()

    def action_quit(self) -> None:
        self.exit(0)

    def action_toggle_actions(self) -> None:
        """Open the centered action menu for the current selection."""

        self.push_screen(
            ActionMenuScreen(
                self.current_node,
                is_read_only=self.state.is_read_only,
                read_only_reason=self.state.read_only_reason,
            ),
            self._handle_action_menu_result,
        )

    def action_connect(self, prog: str) -> None:
        """Launch SSH or SFTP for the selected host."""

        run_connect(self, prog, self.current_node)

    def action_reload(self) -> None:
        """Reload the parsed config while trying to preserve selection by name."""

        selected_name = self._selected_name()
        self.state.sshconf = SSH_Config(file=self.state.config_file).read().parse()
        self._refresh_view(preferred_name=selected_name, rebuild_tree=True)
        self.notify("Configuration reloaded", severity="information")

    def action_delete(self) -> None:
        """Ask for confirmation before removing the selected host or group."""

        if not self._can_delete_current_node():
            return

        self.push_screen(ConfirmDeleteScreen(self.current_node), self._delete_confirmed)

    def _delete_confirmed(self, confirmed: bool | None) -> None:
        """Apply the destructive delete once the confirmation modal resolves."""

        if not confirmed or self.current_node is None:
            return

        item_type, deleted_name = self._delete_current_node()

        if self.state.sshconf.generate_ssh_config():
            self.notify(f"Deleted {item_type}: {deleted_name}", severity="information")
        self.current_node = None
        self.action_reload()

    def _set_current_node(self, node: SSHNode) -> None:
        """Store the active node and refresh the dependent widgets."""

        self.current_node = node
        self.state.current_node = node
        self._refresh_view()

    def _refresh_view(self, preferred_name: str | None = None, *, rebuild_tree: bool = False) -> None:
        self._restore_selection(preferred_name)

        nav_tree = self.query_one_optional(NavigationTree)
        if nav_tree is not None and rebuild_tree:
            # Rebuild the tree only on config reloads; doing it on every highlight
            # would collapse expanded groups and make navigation unusable.
            nav_tree.rebuild(self.state.sshconf)
            nav_tree.select_node_by_name(self._selected_name())

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
        """Best-effort lookup used to restore selection after config reload."""

        if self.state.sshconf.check_host_by_name(name):
            return self.state.sshconf.get_host_by_name(name)
        if self.state.sshconf.check_group_by_name(name):
            return self.state.sshconf.get_group_by_name(name)
        return None

    def _event_node(self, event) -> SSHNode:
        """Extract the selected SSHClick node from Tree or compatibility events."""

        return event.node.data if hasattr(event, "node") else getattr(event, "node_data", None)

    def _focus_tree(self) -> None:
        """Return keyboard focus to the navigation tree."""

        self.query_one(NavigationTree).focus_tree()

    def _selected_name(self) -> str | None:
        """Return the current node name so selection can survive a reload."""

        return self.current_node.name if self.current_node is not None else None

    def _handle_connection_action(self, action_id: str) -> None:
        """Dispatch interactive host actions from the action modal."""

        if action_id == "act_ssh":
            self.action_connect("ssh")
        elif action_id == "act_sftp":
            self.action_connect("sftp")
        elif action_id == "act_copy_key" and self.current_node is not None:
            copy_ssh_keys(self, self.current_node)
        elif action_id == "act_reset_fp" and self.current_node is not None:
            reset_fingerprint(self, self.current_node)

    def _handle_unimplemented_action(self) -> None:
        """Show the current placeholder message for create/edit flows."""

        if self.state.is_read_only:
            self.notify(self.state.read_only_reason, title="Read-only config", severity="warning")
            return
        self.notify("This flow will be implemented in the next TUI phase.", title="Not implemented", severity="information")

    def _can_delete_current_node(self) -> bool:
        """Validate whether the current selection may enter the delete flow."""

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
        """Remove the selected host or group from the in-memory config model."""

        if isinstance(self.current_node, SSH_Group):
            self.state.sshconf.groups.remove(self.current_node)
            return ("group", self.current_node.name)
        return self._delete_current_host()

    def _delete_current_host(self) -> tuple[str, str]:
        """Remove the selected host from its group and from the global host list."""

        found_host = self.current_node
        host_group = self.state.sshconf.get_group_by_name(found_host.group)
        if found_host.type == HostType.NORMAL:
            host_group.hosts.remove(found_host)
        else:
            host_group.patterns.remove(found_host)
        self.state.sshconf.all_hosts.remove(found_host)
        return ("host", found_host.name)

    def _restore_selection(self, preferred_name: str | None) -> None:
        """Restore selection by name after a config reload, if possible."""

        if preferred_name is None:
            return
        self.current_node = self._find_node_by_name(preferred_name)
        self.state.current_node = self.current_node
