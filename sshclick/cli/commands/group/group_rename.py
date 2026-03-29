import click
from sshclick.ops import SSHClickOpsError, rename_group
from sshclick.core import SSH_Config
from sshclick.core import complete_ssh_group_names

#------------------------------------------------------------------------------
# COMMAND: group rename
#------------------------------------------------------------------------------
SHORT_HELP = "Rename existing group"
LONG_HELP  = "Rename existing group in configuration"

#------------------------------------------------------------------------------

@click.command(name="rename", short_help=SHORT_HELP, help=LONG_HELP)
@click.argument("name", shell_complete=complete_ssh_group_names)
@click.argument("new_name")
@click.pass_context
def cmd(ctx, name, new_name):
    config: SSH_Config = ctx.obj

    try:
        rename_group(config, name, new_name)
    except SSHClickOpsError as exc:
        print(str(exc))
        ctx.exit(1)

    if config.generate_ssh_config():
        print(f"Renamed group: {name} -> {new_name}")
