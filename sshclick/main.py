import click
from .globals import *
from .sshc import SSH_Config

# Setup click to use both short and long help option
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

@click.group(context_settings=CONTEXT_SETTINGS)
@click.option("--sshconfig", default=DEFAULT_USER_CONF, help="Config file, default is ~/.ssh/config")
@click.option("--stdout",    default=DEFAULT_STDOUT, is_flag=True, help="Send changed SSH config to STDOUT instead to original file")
@click.version_option(VERSION, message="SSHClick (sshc) - Version: %(version)s")
@click.pass_context
def cli(ctx, sshconfig: str, stdout: bool):
    """
    SSHClick - SSH Config manager

    Note: As this is early alpha, backup your SSH config files before
    this software, as you might accidentally lose some configuration
    """
    # Prepare Click context object
    ctx.obj = SSH_Config(file=sshconfig, stdout=stdout).read().parse()


# Top full commands
from .cmds import cmd_group, cmd_host
cli.add_command(cmd_host.ssh_host)
cli.add_command(cmd_group.ssh_group)
