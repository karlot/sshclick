import click
from lib.sshutils import SSH_Config

#------------------------------------------------------------------------------
# COMMAND: group delete
#------------------------------------------------------------------------------
@click.command(name="delete", help="Delete group")
# @click.argument("name", shell_complete=complete_ssh_group_names)
@click.argument("name")
@click.pass_context
def cmd(ctx, name):
    config: SSH_Config = ctx.obj['CONFIG']

    # Find group by name
    found_group = config.find_group_by_name(name, throw_on_fail=False)
    if not found_group:
        print(f"Cannot delete group '{name}', it is not defined in configuration!")
        ctx.exit(1)
    
    config.groups.remove(found_group)

    config.generate_ssh_config().write_out()
    if not config.stdout:
        print(f"Deleted group: {name}")
