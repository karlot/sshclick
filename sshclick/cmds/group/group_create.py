import click
from sshclick.sshc import SSH_Config, SSH_Group

#------------------------------------------------------------------------------
# COMMAND: group create
#------------------------------------------------------------------------------
@click.command(name="create", help="Create new group")
@click.option("-d", "--desc", default=None, type=str, help="Short description of group")
@click.option("-i", "--info", default=[], multiple=True, type=str, help="Info line, can be set multiple times")
@click.argument("name")
@click.pass_context
def cmd(ctx, name, desc, info):
    config: SSH_Config = ctx.obj

    # Check if already group exists
    found_group = config.find_group_by_name(name, throw_on_fail=False)
    if found_group:
        print(f"Cannot create new group '{name}', as group already exists with this name")
        ctx.exit(1)

    new_group = SSH_Group(name, desc=desc, info=info)

    # Add new group to config and show newly created group
    config.groups.append(new_group)
    
    config.generate_ssh_config().write_out()
    if not config.stdout:
        print(f"Created group: {name}")
    