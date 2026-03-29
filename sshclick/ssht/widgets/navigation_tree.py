from rich.text import Text
from textual.app import ComposeResult
from textual.message import Message
from textual.widgets import Static, Tree

from sshclick.core import SSH_Config, SSH_Group, SSH_Host, HostType


class NavigationTree(Static):
    """Left-hand SSH object tree used for group and host navigation."""

    class NodeHighlighted(Message):
        """Posted when the tree highlight changes."""

        def __init__(self, node_data: SSH_Group | SSH_Host | None) -> None:
            super().__init__()
            self.node_data = node_data

    class NodeSubmitted(Message):
        """Posted when the user confirms the current tree node."""

        def __init__(self, node_data: SSH_Group | SSH_Host | None) -> None:
            super().__init__()
            self.node_data = node_data


    def __init__(self, sshconf: SSH_Config, id: str | None = None) -> None:
        self.sshconf = sshconf
        super().__init__(id=id)


    def compose(self) -> ComposeResult:
        yield Tree("SSH Configuration", id="sshtree", data=None)


    def on_mount(self) -> None:
        self.rebuild(self.sshconf)


    def rebuild(self, sshconf: SSH_Config) -> None:
        """Recreate the visual tree from the parsed SSHClick config model."""

        self.sshconf = sshconf
        tree = self.query_one(Tree)
        pattern_color = getattr(self.app, "theme_variables", {}).get("sshclick-pattern", "bright_blue")
        tree.clear()
        tree.reset("SSH Configuration", data=None)
        tree.root.expand()

        for group in self.sshconf.groups:
            group_node = tree.root.add(group.name, data=group, expand=False)
            for host in group.hosts + group.patterns:
                label = host.name if host.type != HostType.PATTERN else Text(host.name, style=pattern_color)
                group_node.add_leaf(label, data=host)


    def focus_tree(self) -> None:
        self.query_one(Tree).focus()


    def select_node_by_name(self, name: str | None) -> bool:
        """Expand parents as needed and move the tree cursor to the named node."""

        if not name:
            return False

        tree = self.query_one(Tree)
        target_node = self._find_tree_node(tree.root, name)
        if target_node is None:
            return False

        parent = target_node.parent
        while parent is not None:
            parent.expand()
            parent = parent.parent

        tree.select_node(target_node)
        return True


    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        self.post_message(self.NodeHighlighted(event.node.data))


    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        # Enter on a group should behave like a folder toggle, while hosts keep
        # the regular "selected item" flow for the parent app.
        if isinstance(event.node.data, SSH_Group):
            event.node.toggle()
        self.post_message(self.NodeSubmitted(event.node.data))


    def _find_tree_node(self, node, name: str):
        """Return the first tree node whose SSHClick data object matches the given name."""

        node_data = getattr(node, "data", None)
        if getattr(node_data, "name", None) == name:
            return node

        for child in node.children:
            found = self._find_tree_node(child, name)
            if found is not None:
                return found
        return None
