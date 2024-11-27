# from sshclick.globals import USER_SSH_CONFIG
from sshclick.sshc import SSH_Config, SSH_Host

from textual.app import ComposeResult
from textual.widgets import Static, Tree

from sshclick.ssht.modal_action import ModalAction


class SSHTree(Static):
    """Widget for SSH Host tree"""

    def __init__(self, sshconf: SSH_Config):
        self.sshconf = sshconf
        super().__init__()


    def compose(self) -> ComposeResult:
        ssh_tree = Tree(f"SSH Configuration ({len(self.sshconf.groups)} groups)", id="sshtree", data=None)
        ssh_tree.root.expand()
        # ssh_tree.guide_depth = 3   # default:4  // currently not needed, as we dont have sub-groups

        # Add each group and its hosts in order as in SSH-config
        for group in self.sshconf.groups:
            g = ssh_tree.root.add(f":file_folder: {group.name}", data=group, expand=False)
            for host in group.hosts + group.patterns:
                g.add_leaf(host.name, data=host)
        
        yield ssh_tree


    def on_tree_node_selected(self, selected: Tree.NodeSelected):
        if isinstance(selected.node.data, SSH_Host):
            # self.notify(f"Selected host: {selected.node.data}")
            self.app.push_screen(ModalAction(selected.node.data))

