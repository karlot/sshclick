from collections.abc import Sequence

from sshclick.globals import DEFAULT_GROUP_NAME
from sshclick.core import HostType, PARAMS_WITH_ALLOWED_MULTIPLE_VALUES, SSH_Config, SSH_Group, SSH_Host

from .errors import SSHClickOpsError

# -----------------------------------------------------------------------------
# SSHClick host configuration operations
# -----------------------------------------------------------------------------

def create_host(
    config: SSH_Config,
    name: str,
    *,
    host_type: HostType | None = None,
    address: str | None = None,
    user: str | None = None,
    info: Sequence[str] = (),
    parameters: Sequence[tuple[str, str]] = (),
    target_group_name: str | None = None,
    force_group: bool = False,
) -> SSH_Host:
    """Create a new host or pattern host in the in-memory config model."""

    target_group_name = target_group_name or DEFAULT_GROUP_NAME
    if config.check_host_by_name(name):
        raise SSHClickOpsError(f"Cannot create host '{name}' as it already exists in configuration!")

    target_group = _resolve_target_group(config, name, target_group_name, force_group)
    inferred_type = HostType.PATTERN if "*" in name else HostType.NORMAL
    target_type = host_type or inferred_type

    if target_type == HostType.NORMAL and "*" in name:
        raise SSHClickOpsError("Normal host names cannot contain '*' wildcards. Switch the entry type to Pattern instead.")
    if target_type == HostType.PATTERN and "*" not in name:
        raise SSHClickOpsError("Pattern entries must include '*' in their name so OpenSSH treats them as match patterns.")

    new_host = SSH_Host(name=name, group=target_group_name, type=target_type, info=list(info))

    if user:
        new_host.params["user"] = user
    if address:
        new_host.params["hostname"] = address

    for param, value in parameters:
        _store_host_parameter(new_host, param.lower(), value, address=address, user=user)

    if target_type == HostType.NORMAL:
        target_group.hosts.append(new_host)
    else:
        target_group.patterns.append(new_host)
    config.all_hosts.append(new_host)
    return new_host


def delete_host(config: SSH_Config, name: str) -> SSH_Host:
    """Delete a host or pattern host from the in-memory config model and return it."""

    if not config.check_host_by_name(name):
        raise SSHClickOpsError(f"Cannot delete host '{name}' as it is not defined in configuration!")

    found_host = config.get_host_by_name(name)
    host_group = config.get_group_by_name(found_host.group)

    if found_host.type == HostType.NORMAL:
        host_group.hosts.remove(found_host)
    else:
        host_group.patterns.remove(found_host)

    config.all_hosts.remove(found_host)
    return found_host


def rename_host(config: SSH_Config, name: str, new_name: str) -> SSH_Host:
    """Rename a host if the current and target names are valid."""

    if not config.check_host_by_name(name):
        raise SSHClickOpsError(f"Cannot rename host '{name}' as it is not defined in configuration!")
    if config.check_host_by_name(new_name):
        raise SSHClickOpsError(f"Cannot rename host '{name}' to '{new_name}' as new name is already used!")

    found_host = config.get_host_by_name(name)
    found_host.name = new_name
    return found_host


def update_host(
    config: SSH_Config,
    name: str,
    *,
    info: Sequence[str] | None = None,
    parameters: Sequence[tuple[str, str]] = (),
    target_group_name: str | None = None,
    force_group: bool = False,
) -> SSH_Host:
    """Update host metadata, parameters, and optionally move it to a different group."""

    if target_group_name is None and not parameters and info is None:
        raise SSHClickOpsError("Calling set without setting anything is not valid on host(s). Run with 'sshc host set -h' for help.")
    if not config.check_host_by_name(name):
        raise SSHClickOpsError(f"Unknown host '{name}'!")

    current_host = config.get_host_by_name(name)
    current_group = config.get_group_by_name(current_host.group)

    if target_group_name:
        if target_group_name == current_host.group:
            # Keep current CLI semantics: no hard failure if already in target group.
            pass
        else:
            target_group = _resolve_target_group(config, name, target_group_name, force_group)
            config.move_host_to_group(current_host, current_group, target_group)

    if info is not None:
        if info and len(info[0]) > 0:
            current_host.info = current_host.info + list(info)
        else:
            current_host.info = []

    for param, value in parameters:
        _update_host_parameter(current_host, name, param.lower(), value)

    return current_host


def _resolve_target_group(config: SSH_Config, host_name: str, target_group_name: str, force_group: bool) -> SSH_Group:
    """Return the destination group, creating it only when `force_group` allows it."""
    
    if config.check_group_by_name(target_group_name):
        return config.get_group_by_name(target_group_name)
    if force_group:
        new_group = SSH_Group(name=target_group_name)
        config.groups.append(new_group)
        return new_group
    raise SSHClickOpsError(
        f"Cannot create host '{host_name}' in group '{target_group_name}' since the group does not exist\n"
        "Create group first, or use '--force' option to create it automatically!"
    )


def _store_host_parameter(host: SSH_Host, param: str, value: str, *, address: str | None, user: str | None) -> None:
    """Store an initial parameter during host creation with basic validation."""

    if not value or value.isspace():
        raise SSHClickOpsError("Cannot define empty value for parameter during host creation!")
    if param == "user" and user:
        raise SSHClickOpsError("Trying to define user directly through argument and parameters, make no sense! Use only one")
    if param == "hostname" and address:
        raise SSHClickOpsError("Trying to define hostname directly through argument and parameters, make no sense! Use only one")

    if param in PARAMS_WITH_ALLOWED_MULTIPLE_VALUES:
        if param not in host.params:
            host.params[param] = [value]
        else:
            host.params[param].append(value)
        return

    host.params[param] = value


def _update_host_parameter(host: SSH_Host, host_name: str, param: str, value: str) -> None:
    """Apply a host parameter update, including unsets and multi-value merges."""

    if value:
        if param in PARAMS_WITH_ALLOWED_MULTIPLE_VALUES:
            if param not in host.params:
                host.params[param] = [value]
            elif value in host.params[param]:
                raise SSHClickOpsError(f"Cannot add existing value '{value}' to host parameter '{param}' multiple times!")
            else:
                host.params[param].append(value)
            return

        host.params[param] = value
        return

    if param in host.params:
        host.params.pop(param)
        return

    raise SSHClickOpsError(f"Cannot unset parameter '{param}' on host '{host_name}' because it is not defined!")
