import click
from sshclick.sshc import SSH_Config
from sshclick.sshc import complete_ssh_group_names

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

    if not config.check_group_by_name(name):
        print(f"Cannot rename group '{name}', as it is not defined in configuration!")
        ctx.exit(1)
    if config.check_group_by_name(new_name):
        print(f"Cannot rename group '{name}' to '{new_name}' as new name is already used!")
        ctx.exit(1)

    config.get_group_by_name(name).name = new_name
    config.generate_ssh_config().write_out()
    
    if not config.stdout:
        print(f"Renamed group: {name} -> {new_name}")
