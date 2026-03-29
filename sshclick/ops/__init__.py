"""Shared config mutation helpers used by both CLI and TUI layers."""

from .config_ops import delete_host_style, set_host_style
from .errors import SSHClickOpsError
from .group_ops import create_group, delete_group, rename_group, update_group
from .host_ops import create_host, delete_host, rename_host, update_host

__all__ = [
    "SSHClickOpsError",
    "create_group",
    "create_host",
    "delete_group",
    "delete_host",
    "delete_host_style",
    "rename_group",
    "rename_host",
    "set_host_style",
    "update_group",
    "update_host",
]
