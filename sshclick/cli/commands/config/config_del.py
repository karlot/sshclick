import click
from sshclick.ops import SSHClickOpsError, delete_host_style
from sshclick.core import SSH_Config

#------------------------------------------------------------------------------
# COMMAND: config del
#------------------------------------------------------------------------------
SHORT_HELP = "Delete config option"

# Parameters help:
HOST_STYLE_HELP  = "Remove host-style from configuration"
#------------------------------------------------------------------------------
@click.command(name="del", short_help=SHORT_HELP, help=SHORT_HELP)
@click.option("--host-style", is_flag=True, help=HOST_STYLE_HELP)
@click.pass_context
def cmd(ctx, host_style):
    config: SSH_Config = ctx.obj

    if not host_style:
        print("No option was provided to delete from SSH config options!")
        return

    try:
        delete_host_style(config)
    except SSHClickOpsError as exc:
        print(str(exc))
        return

    config.generate_ssh_config()
