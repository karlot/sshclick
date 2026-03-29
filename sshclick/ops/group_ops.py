from collections.abc import Sequence

from sshclick.core import SSH_Config, SSH_Group

from .errors import SSHClickOpsError

# -----------------------------------------------------------------------------
# SSHClick group configuration operations
# -----------------------------------------------------------------------------

def create_group(config: SSH_Config, name: str, *, desc: str = "", info: Sequence[str] = ()) -> SSH_Group:
    """Create a new SSHClick group in the in-memory config model."""

    if config.check_group_by_name(name):
        raise SSHClickOpsError(f"Cannot create new group '{name}', as group already exists with this name")

    new_group = SSH_Group(name=name, desc=desc, info=list(info))
    config.groups.append(new_group)
    return new_group


def edit_group(config: SSH_Config, name: str, *, new_name: str, desc: str = "", info: Sequence[str] = ()) -> SSH_Group:
    """Edit a group in place, optionally renaming it and replacing its metadata."""

    if not config.check_group_by_name(name):
        raise SSHClickOpsError(f"Cannot modify group '{name}', it is not defined in configuration!")

    found_group = config.get_group_by_name(name)

    if new_name != name:
        if config.check_group_by_name(new_name):
            raise SSHClickOpsError(f"Cannot rename group '{name}' to '{new_name}' as new name is already used!")

        found_group.name = new_name
        for host in found_group.hosts + found_group.patterns:
            host.group = new_name

    found_group.desc = desc.strip()
    found_group.info = [line.strip() for line in info if line.strip()]
    return found_group


def delete_group(config: SSH_Config, name: str) -> SSH_Group:
    """Delete a group from the in-memory config model and return it."""

    if not config.check_group_by_name(name):
        raise SSHClickOpsError(f"Cannot delete group '{name}', it is not defined in configuration!")

    found_group = config.get_group_by_name(name)
    config.groups.remove(found_group)
    return found_group


def rename_group(config: SSH_Config, name: str, new_name: str) -> SSH_Group:
    """Rename a group and update the group reference on its hosts and patterns."""

    if not config.check_group_by_name(name):
        raise SSHClickOpsError(f"Cannot rename group '{name}', as it is not defined in configuration!")
    if config.check_group_by_name(new_name):
        raise SSHClickOpsError(f"Cannot rename group '{name}' to '{new_name}' as new name is already used!")

    found_group = config.get_group_by_name(name)
    found_group.name = new_name
    for host in found_group.hosts + found_group.patterns:
        host.group = new_name
    return found_group


def update_group(config: SSH_Config, name: str, *, desc: str | None = None, info: Sequence[str] | None = None) -> SSH_Group:
    """Update the editable metadata fields on a single group."""

    if desc is None and info is None:
        raise SSHClickOpsError("Calling set on group without specifying any option is not valid!\nRun 'sshc group set -h' for help.")
    if not config.check_group_by_name(name):
        raise SSHClickOpsError(f"Cannot modify group '{name}', it is not defined in configuration!")

    found_group = config.get_group_by_name(name)
    if desc is not None:
        found_group.desc = desc.strip()

    if info is not None:
        found_group.info = [line.strip() for line in info if line.strip()]

    return found_group
