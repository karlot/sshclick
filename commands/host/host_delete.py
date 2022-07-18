import click
from lib.sshutils import *
from commands.host import host_show


#------------------------------------------------------------------------------
# COMMAND: host delete
#------------------------------------------------------------------------------
@click.command(name="delete", help="Delete host from configuration")
@click.argument("name")
@click.pass_context
def cmd(ctx, name):
    # global traced_hosts
    config = ctx.obj['CONFIG']

    found_host, found_group = find_host_by_name(config, name)
    print("Deleted host:")
    ctx.invoke(host_show.cmd, name=name, graph=False)
    
    if found_host in found_group["hosts"]:
        found_group["hosts"].remove(found_host)
    if found_host in found_group["patterns"]:
        found_group["patterns"].remove(found_host)

    lines = generate_ssh_config(config)
    write_ssh_config(ctx, lines)
