import click
from ssh_globals import *
from lib.sshutils import SSH_Config

# Setup click to use both short and long help option
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

# Version printer callback function
def print_version(ctx, _, value):
    if not value or ctx.resilient_parsing:
        return
    print(f"SSHClick Version: {VERSION}")
    ctx.exit()

@click.group(context_settings=CONTEXT_SETTINGS)
@click.option("--sshconfig", default=DEFAULT_USER_CONF, type=click.Path(exists=True), help="Config file, default is ~/.ssh/config")
@click.option("--stdout",    default=DEFAULT_STDOUT, is_flag=True, help="Send changed SSH config to STDOUT instead to original file")
@click.option("--version",   is_flag=True, callback=print_version, expose_value=False, is_eager=True, help="Show current version")
@click.pass_context
def cli(ctx, sshconfig, stdout):
    """
    SSHClick - SSH Config manager

    Note: As this is early alpha, backup your SSH config files before
    this software, as you might accidentally lose some configuration
    """
    # Prepare Click context object
    ctx.ensure_object(dict)

    # Parse ssh config file and store config in the context
    config = SSH_Config(file=sshconfig, stdout=stdout).read().parse()
    ctx.obj["CONFIG"] = config


# Top full commands
from click_cmd import cmd_group, cmd_host
cli.add_command(cmd_host.ssh_host)
cli.add_command(cmd_group.ssh_group)

# Shortcuts/aliases
# from click_cmd.host import host_list
# cli.add_command(host_list.cmd, name="ls")


if __name__ == '__main__':
    cli()
