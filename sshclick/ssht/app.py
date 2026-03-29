import os.path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header

from sshclick.globals import USER_SSH_CONFIG
from sshclick.ops import delete_group, delete_host
from sshclick.core import SSH_Config, SSH_Group
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
        elif action_id in {"act_edit_host", "act_edit_group", "act_create_host", "act_create_group"}:
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

        item_type, deleted_name = self._delete_current_node()

        if self.state.sshconf.generate_ssh_config():
            self.notify(f"Deleted {item_type}: {deleted_name}", severity="information")
        self.current_node = None
        self.action_reload()


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


    def _restore_selection(self, preferred_name: str | None) -> None:
        if preferred_name is None:
            return
        self.current_node = self._find_node_by_name(preferred_name)
        self.state.current_node = self.current_node
