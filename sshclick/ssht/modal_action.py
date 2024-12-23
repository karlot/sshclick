# from sshclick.globals import USER_SSH_CONFIG, SSH_CONNECT_TIMEOUT
from sshclick.sshc import SSH_Config, SSH_Group, SSH_Host, HostType

# from textual import on
from textual.app import ComposeResult
from textual.widgets import OptionList
from textual.widgets.option_list import Option, Separator
from textual.screen import ModalScreen

# SSHTui modules
from sshclick.ssht.modal_delete import ModalDelete

# Load linked utils
from sshclick.ssht.utils import run_connect
from sshclick.globals import *

class ModalAction(ModalScreen[None]):
    BINDINGS = [
        ("escape", "app.pop_screen"),
    ]

    DEFAULT_CSS = """
    OptionList {
        width: 40;
    }
    """

    def __init__(self, node: SSH_Host | SSH_Group) -> None:
        self.node = node
        super().__init__()

    def compose(self) -> ComposeResult:
        if self.node == None:
            # No object is selected in tree
            yield OptionList(
                Option("Create new host", id="opt_new_hst", disabled=ACTIONS_EDIT_DISABLED),
                Option("Create new group", id="opt_new_grp", disabled=ACTIONS_CREATE_GROUP_DISABLED),
                Separator(),
                Option("Cancel (ESC)", id="opt_cancel"),
            )
        elif isinstance(self.node, SSH_Group):
            # Group is selected
            yield OptionList(
                Option("Edit current group", id="opt_ed_cur", disabled=ACTIONS_EDIT_DISABLED),
                Option("Delete current group", id="opt_del_cur", disabled=ACTIONS_DELETE_DISABLED),
                Separator(),
                Option("Create new host", id="opt_new_hst", disabled=ACTIONS_CREATE_HOST_DISABLED),
                Option("Create new group", id="opt_new_grp", disabled=ACTIONS_CREATE_GROUP_DISABLED),
                Separator(),
                Option("Cancel (ESC)", id="opt_cancel"),
            )
        else:
            # Host is selected
            yield OptionList(
                Option("SSH to current host", id="opt_ssh_cur"),
                Option("SFTP to current host", id="opt_sftp_cur"),
                # Option("Upload file to current host", id="opt_up_file", disabled=True),
                # Option("Test host connectivity", id="opt_test", disabled=True),
                # Option("Clear host fingerprint", id="opt_clear_finger", disabled=True),
                # Option("Inject SSH Key", id="opt_inject_key", disabled=True),
                Separator(),
                Option("Edit current host", id="opt_ed_cur", disabled=ACTIONS_EDIT_DISABLED),
                Option("Delete current host", id="opt_del_cur", disabled=ACTIONS_DELETE_DISABLED),
                Separator(),
                Option("Create new host", id="opt_new_hst", disabled=ACTIONS_CREATE_HOST_DISABLED),
                Option("Create new group", id="opt_new_grp", disabled=ACTIONS_CREATE_GROUP_DISABLED),
                Separator(),
                Option("Cancel (ESC)", id="opt_cancel"),
            )


    def on_option_list_option_selected(self, selected: OptionList.OptionSelected) -> None:
        selected_id = selected.option_id
        if selected_id == None: return

        # Remove our screen overlay (Action modal) and start
        # whatever is linked to called "action option id"
        self.app.pop_screen()

        # If canceling, then just do nothing
        if selected_id == "opt_cancel":
            return

        # Host specific actions (connect, etc...)
        elif selected_id == "opt_ssh_cur":
            run_connect(self.app, "ssh", self.node)

        elif selected_id == "opt_sftp_cur":
            run_connect(self.app, "sftp", self.node)


        # Create host/group actions
        elif selected_id == "opt_new_hst":
            self.notify("New host?")

        elif selected_id == "opt_new_grp":
            self.notify("New group?")


        # Edit/Delete actions
        elif selected_id == "opt_ed_cur":
            self.notify(f"Editing '{self.node.name}'?")

        elif selected_id == "opt_del_cur":
            self.app.push_screen(ModalDelete(self.node))


        # Other, not implemented
        # ...

