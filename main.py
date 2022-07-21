import click
from ssh_globals import *
from lib.sshutils import parse_ssh_config

# Load top level commands
from commands import cmd_group, cmd_host

# Setup click to use both short and long help option
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

@click.group(context_settings=CONTEXT_SETTINGS)
@click.option("--debug/--no-debug", "_debug_", default=DEBUG)
@click.option("--sshconfig", default=USER_CONF_FILE, type=click.Path(exists=True), help="Config file, default is ~/.ssh/config")
@click.option("--stdout",    default=STDOUT_CONF, is_flag=True, help="Original SSH config file will not be changed, instead modified SSH Config will be sent to STDOUT.")
@click.pass_context
def cli(ctx, _debug_, sshconfig, stdout):
    """
    SSHClick - SSH Config manager

    Note: As this is early alpha, backup your SSH config files before
    this software, as you might accidentally lose some configuration.
    """
    
    ctx.ensure_object(dict)
    ctx.obj["DEBUG"] = _debug_
    ctx.obj["USER_CONF_FILE"] = sshconfig
    ctx.obj["STDOUT_CONF"] = stdout

    # Parse ssh config file and store config in the context
    ctx.obj["CONFIG"] = parse_ssh_config(sshconfig)

cli.add_command(cmd_host.ssh_host)
cli.add_command(cmd_group.ssh_group)


if __name__ == '__main__':
    cli()
