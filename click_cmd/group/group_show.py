import click
import yaml     #TODO: Cmooon...
from prettytable import PrettyTable
from lib.sshutils import *


#------------------------------------------------------------------------------
# COMMAND: group show
#------------------------------------------------------------------------------
@click.command(name="show", help="Shows group details")
@click.argument("name")
@click.pass_context
def cmd(ctx, name):
    config = ctx.obj['CONFIG']

    x = PrettyTable(field_names=["Group Parameter", "Value"])
    x.align = "l"

    found = find_group_by_name(config, name)

    x.add_row(["name", found["name"]])
    x.add_row(["description", found["desc"]])
    x.add_row(["info", yaml.dump(found["info"])])

    hostlist = []
    for host in found["hosts"]:
        if "hostname" in host:
            hostlist.append(f"{host['name']} ({host['hostname']})")
        else:
            hostlist.append(f"{host['name']}")

    x.add_row(["hosts", "\n".join(hostlist) + "\n"])

    patternlist = []
    for host in found["patterns"]:
        # hack to search via case insensitive info
        if "hostname" in host:
            patternlist.append(f"{host['name']} ({host['hostname']})")
        else:
            patternlist.append(f"{host['name']}")

    x.add_row(["patterns", "\n".join(patternlist)])

    # Print table
    print(x)
