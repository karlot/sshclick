__version__ = "0.5.0"

import click
import os.path
from .sshc import SSH_Config

# Setup click to use both short and long help option
USER_SSH_CONFIG   = "~/.ssh/config"
CONTEXT_SETTINGS  = dict(help_option_names=['-h', '--help'])
DEFAULT_USER_CONF = os.path.expanduser(USER_SSH_CONFIG)

#------------------------------------------------------------------------------
# COMMAND: sshc
#------------------------------------------------------------------------------
MAIN_HELP = f"""
SSHClick - SSH Config manager. version {__version__}

NOTE: As this is early alpha, backup your SSH config files before
this software, as you might accidentally lose some configuration
"""

# Parameters help:
SSHCONFIG_HELP = f"Config file (default: {USER_SSH_CONFIG})"
STDOUT_HELP    =  "Send changed SSH config to STDOUT instead to original file, can be enabled with setting ENV variable (export SSHC_STDOUT=1)"
#------------------------------------------------------------------------------

@click.group(context_settings=CONTEXT_SETTINGS, help=MAIN_HELP)
@click.option("--sshconfig", default=DEFAULT_USER_CONF, envvar="SSHC_SSHCONFIG", help=SSHCONFIG_HELP)
@click.option("--stdout",    is_flag=True,              envvar="SSHC_STDOUT",    help=STDOUT_HELP)
@click.version_option(__version__, message="SSHClick (sshc) - Version: %(version)s")
@click.pass_context
def cli(ctx: click.core.Context, sshconfig: str, stdout: bool):
    ctx.obj = SSH_Config(file=sshconfig, stdout=stdout).read().parse()


# Top commands
from .cmds import cmd_group, cmd_host, cmd_config
cli.add_command(cmd_host.ssh_host)
cli.add_command(cmd_group.ssh_group)
cli.add_command(cmd_config.ssh_config)

# Top level aliases (groups --> group list, hosts --> host list, etc..)
from .cmds.cmd_group import group_list
cli.add_command(group_list.cmd, "groups")

from .cmds.cmd_host import host_list
cli.add_command(host_list.cmd, "hosts")
