from sshclick.globals import ENABLED_HOST_STYLES
from sshclick.core import SSH_Config

from .errors import SSHClickOpsError

# -----------------------------------------------------------------------------
# SSHClick metadata configuration operations
# -----------------------------------------------------------------------------

def set_host_style(config: SSH_Config, host_style: str) -> str:
    """Persist the configured host output style in SSHClick config metadata."""

    if not host_style:
        raise SSHClickOpsError("No option was provided to set into SSH config options!")
    if host_style not in ENABLED_HOST_STYLES:
        raise SSHClickOpsError(f"Cannot set style '{host_style}', as it is not one of available styles!")

    config.opts["host-style"] = host_style
    return host_style


def delete_host_style(config: SSH_Config) -> str:
    """Remove the stored host output style from SSHClick config metadata."""

    if "host-style" not in config.opts:
        raise SSHClickOpsError("Cannot remove host-style from configuration, as it is not defined!")

    del config.opts["host-style"]
    return "host-style"

