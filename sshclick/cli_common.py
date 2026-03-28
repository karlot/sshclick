import os.path

from sshclick.globals import USER_SSH_CONFIG
from sshclick.sshc import SSH_Config

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}
SSHCONFIG_ENVVAR = "SSHC_CONFIG"
SSHCONFIG_HELP = f"Config file (default: {USER_SSH_CONFIG}). Can be set with SSHC_CONFIG."


def expand_config_path(config: str) -> str:
    return os.path.expanduser(config)


def load_ssh_config(config: str, *, stdout: bool = False, diff: bool = False) -> SSH_Config:
    return SSH_Config(file=expand_config_path(config), stdout=stdout, diff=diff).read().parse()
