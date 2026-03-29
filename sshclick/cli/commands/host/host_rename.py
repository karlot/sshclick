import click
from sshclick.ops import SSHClickOpsError, rename_host
from sshclick.core import SSH_Config, complete_ssh_host_names

#------------------------------------------------------------------------------
# COMMAND: host rename
#------------------------------------------------------------------------------
SHORT_HELP = "Rename existing host"
LONG_HELP  = "Rename existing host in configuration"

#------------------------------------------------------------------------------

@click.command(name="rename", short_help=SHORT_HELP, help=LONG_HELP)
@click.argument("name", shell_complete=complete_ssh_host_names)
@click.argument("new_name")
@click.pass_context
def cmd(ctx, name, new_name):
    config: SSH_Config = ctx.obj

    try:
        rename_host(config, name, new_name)
    except SSHClickOpsError as exc:
        print(str(exc))
        ctx.exit(1)
    
    if config.generate_ssh_config():
        print(f"Renamed host: {name} -> {new_name}")
