import click
from lib.sshutils import *


#------------------------------------------------------------------------------
# COMMAND: group-set
#------------------------------------------------------------------------------
@click.command(name="set", help="Change group parameters")
@click.option("-r", "--rename", default=None, help="Rename group")
@click.option("-d", "--desc", default=None, help="Set description")
@click.option("-i", "--info", default=None, multiple=True, help="Set info, can be set multiple times")
@click.argument("name")
@click.pass_context
def cmd(ctx, name, rename, desc, info):
    config = ctx.obj['CONFIG']

    # Nothing was provided
    if not rename and not desc and not info:
        error("Calling set without doing anything is not valid. Run with '-h' for help.")
        exit(1)

    # Find group by name
    gr = find_group_by_name(config, name)

    if rename:
        gr["name"] = rename
    
    if desc:
        gr["desc"] = desc

    if info:
        if len(info[0]) > 0:
            gr["info"] = info
        else:
            gr["info"] = []

    print(f"Modified group: {name}")
    
    lines = generate_ssh_config(config)
    write_ssh_config(ctx, lines)
