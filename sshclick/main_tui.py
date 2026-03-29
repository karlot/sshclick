import click

from sshclick.cli.common import CONTEXT_SETTINGS, SSHCONFIG_ENVVAR, SSHCONFIG_HELP
from sshclick.globals import USER_SSH_CONFIG
from sshclick.tui.app import SSHTui
from sshclick.version import VERSION

MAIN_HELP = f"""
SSHClick - SSH Config browser TUI. version {VERSION}

NOTE: This opens the Textual interface for browsing your SSH configuration,
inspecting groups and hosts, and launching common host actions.
"""

## Entry for "ssht" command
@click.command(context_settings=CONTEXT_SETTINGS, help=MAIN_HELP)
@click.option("--config", default=USER_SSH_CONFIG, envvar=SSHCONFIG_ENVVAR, help=SSHCONFIG_HELP)
@click.version_option(VERSION, message="SSHClick (ssht) - Version: %(version)s")
def tui(config: str):
    SSHTui(config_file=config).run()
