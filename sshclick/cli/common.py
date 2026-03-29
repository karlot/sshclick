import os.path

from sshclick.globals import USER_SSH_CONFIG
from sshclick.core import SSH_Config

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}
SSHCONFIG_ENVVAR = "SSHC_CONFIG"
SSHCONFIG_HELP = f"Config file (default: {USER_SSH_CONFIG}). Can be set with SSHC_CONFIG."


def expand_config_path(config: str) -> str:
    """Expand `~` in the configured SSH config path."""

    return os.path.expanduser(config)


def load_ssh_config(config: str, *, stdout: bool = False, diff: bool = False) -> SSH_Config:
    """Load and parse the SSHClick config model for CLI/TUI entrypoints."""

    return SSH_Config(file=expand_config_path(config), stdout=stdout, diff=diff).read().parse()

