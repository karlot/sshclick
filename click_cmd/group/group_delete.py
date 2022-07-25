import click
from lib.sshutils import *


#------------------------------------------------------------------------------
# COMMAND: group delete
#------------------------------------------------------------------------------
@click.command(name="delete", help="Delete group")
@click.argument("name")
@click.pass_context
def cmd(ctx, name):
    config = ctx.obj['CONFIG']

    # Find group by name
    find_group_by_name(config, name)
    
    new_conf = [gr for gr in config if gr["name"] != name]

    print(f"Deleted group: {name}")

    lines = generate_ssh_config(new_conf)
    write_ssh_config(ctx, lines)
