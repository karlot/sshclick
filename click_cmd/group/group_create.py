import click
from lib.sshutils import *
from click_cmd.group import group_show


#------------------------------------------------------------------------------
# COMMAND: group create
#------------------------------------------------------------------------------
@click.command(name="create", help="Create new group")
@click.option("-d", "--desc", default=None, type=str, help="Short description of group")
@click.option("-i", "--info", default=[], multiple=True, type=str, help="Info line, can be set multiple times")
@click.argument("name")
@click.pass_context
def cmd(ctx, name, desc, info):
    config = ctx.obj['CONFIG']

    # Check if already group exists
    found = find_group_by_name(config, name, exit_on_fail=False)
    if found:
        error(f"Cannot create new group '{name}', as group already exists with this name")
        exit(1)

    new_group = {
        "name": name,
        "desc": desc,
        "info": info,
        "hosts": [],
        "patterns": [],
    }
    debug(f"Created new group: {new_group}")

    # Add new group to config and show newly created group
    config.append(new_group)
    ctx.invoke(group_show.cmd, name=name)
    
    lines = generate_ssh_config(config)
    write_ssh_config(ctx, lines)
    