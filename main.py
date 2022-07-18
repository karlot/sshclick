import click
from ssh_globals import *
from lib.mylog import *
from lib.sshutils import parse_ssh_config

from commands import cmd_group, cmd_host



#-------------------[ CLI Functions below ]-------------------
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])

# Main CLI group
@click.group(context_settings=CONTEXT_SETTINGS)
@click.option("--debug/--no-debug", "_debug_", default=DEBUG, help="Enables debug, what did you expect?")
@click.option("--sshconfig", default=USER_CONF_FILE, type=click.Path(exists=True), help="Config file, default is ~/.ssh/config")
@click.option("--stdout",    default=STDOUT_CONF, is_flag=True, help="Original SSH config file will not be changed, instead modified SSH Config will be sent to STDOUT.")
@click.pass_context
def cli(ctx, _debug_, sshconfig, stdout):
    """
    SSH Config manager

    Basically glorified config file scraper & generator.
    It is for the people that do not want to manually handle veeeery 
    large SSH config files, and editing is just so darn pain in the ass!

    As this is early alpha, please backup your SSH config files before
    this software, as you might accidentally lose some configuration.
    """
    
    debug(f"! Debug mode is {'on' if _debug_ else 'off'}")

    ctx.ensure_object(dict)
    ctx.obj["DEBUG"] = _debug_
    ctx.obj["USER_CONF_FILE"] = sshconfig
    ctx.obj["STDOUT_CONF"] = stdout

    # Parse ssh config and store it for rest of the commands
    ctx.obj["CONFIG"] = parse_ssh_config(sshconfig)



cli.add_command(cmd_host.ssh_host)
cli.add_command(cmd_group.ssh_group)

if __name__ == '__main__':
    cli()


