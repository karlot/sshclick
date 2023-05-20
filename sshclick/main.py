from .version import VERSION
import click
import os.path
from .sshc import SSH_Config

# Setup click to use both short and long help option
USER_SSH_CONFIG   = "~/.ssh/config"
CONTEXT_SETTINGS  = dict(help_option_names=['-h', '--help'])

#------------------------------------------------------------------------------
# COMMAND: sshc
#------------------------------------------------------------------------------
MAIN_HELP = f"""
SSHClick - SSH Config manager. version {VERSION}

NOTE: As this will change your SSH config files, make backups before
using this software, as you might accidentally lose some configuration.
"""

# Parameters help:
SSHCONFIG_HELP = f"Config file (default: {USER_SSH_CONFIG})"
STDOUT_HELP    =  "Send changed SSH config to STDOUT instead to original file, can be enabled with setting ENV variable (export SSHC_STDOUT=1)"
#------------------------------------------------------------------------------

# In cases we want to have some execution without any sub-commands, instead of displaying help
# we can add "invoke_without_command=True" in a group decorator, to make function runnable directly
@click.group(context_settings=CONTEXT_SETTINGS, help=MAIN_HELP)
@click.option("--sshconfig", default=USER_SSH_CONFIG, envvar="SSHC_SSHCONFIG", help=SSHCONFIG_HELP)
@click.option("--stdout",    is_flag=True,            envvar="SSHC_STDOUT",    help=STDOUT_HELP)
@click.version_option(VERSION, message="SSHClick (sshc) - Version: %(version)s")
@click.pass_context
def cli(ctx: click.core.Context, sshconfig: str, stdout: bool):
    ctx.obj = SSH_Config(file=os.path.expanduser(sshconfig), stdout=stdout).read().parse()


# Add experimental TUI
from .main_tui import SSHTui
TUI_SHORT_HELP = "TUI Interface (experimental)"
TUI_HELP       = "Experimental TUI interface for interacting with SSH Configuration"
@click.command(name="tui", short_help=TUI_SHORT_HELP, help=TUI_HELP)
@click.pass_context
def tui_cmd(ctx: click.core.Context):
    SSHTui(ctx.obj).run()


# Link all commands to root command
#------------------------------------------------------------------------------
# Top commands
from .cmds import cmd_group, cmd_host, cmd_config
cli.add_command(cmd_host.ssh_host)
cli.add_command(cmd_group.ssh_group)
cli.add_command(cmd_config.ssh_config)
cli.add_command(tui_cmd)

# Top level aliases (groups --> group list, hosts --> host list, etc..)
from .cmds.cmd_group import group_list
cli.add_command(group_list.cmd, "groups")

from .cmds.cmd_host import host_list
cli.add_command(host_list.cmd, "hosts")
