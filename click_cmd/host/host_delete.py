import click
from lib.sshutils import *


#------------------------------------------------------------------------------
# COMMAND: host delete
#------------------------------------------------------------------------------
@click.command(name="delete", help="Delete host from configuration")
# @click.argument("name", shell_complete=complete_ssh_host_names)
@click.argument("name")
@click.pass_context
def cmd(ctx, name):
    config = ctx.obj['CONFIG']

    found_host, found_group = find_host_by_name(config, name)

    if found_host in found_group["hosts"]:
        found_group["hosts"].remove(found_host)
    if found_host in found_group["patterns"]:
        found_group["patterns"].remove(found_host)

    print(f"Deleted host: {name}")
    
    lines = generate_ssh_config(config)
    write_ssh_config(ctx, lines)
