import click
from lib.sshutils import *

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box


#------------------------------------------------------------------------------
# COMMAND: group show
#------------------------------------------------------------------------------
@click.command(name="show", help="Shows group details")
@click.argument("name", shell_complete=complete_ssh_group_names)
@click.pass_context
def cmd(ctx, name):
    config = ctx.obj['CONFIG']

    found = find_group_by_name(config, name)

    hostlist = []
    for host in found["hosts"]:
        if "hostname" in host:
            if "port" in host:
                hostlist.append(f"{host['name']} ({host['hostname']}:{host['port']})")
            else:
                hostlist.append(f"{host['name']} ({host['hostname']})")
        else:
            hostlist.append(f"{host['name']}")

    patternlist = []
    for host in found["patterns"]:
        # hack to search via case insensitive info
        if "hostname" in host:
            patternlist.append(f"{host['name']} ({host['hostname']})")
        else:
            patternlist.append(f"{host['name']}")


    # New rich formating
    table = Table(box=box.SQUARE, style="grey39")
    table.add_column("Group Parameter", no_wrap=True)
    table.add_column("Value")

    table.add_row("name",        found["name"],                     style="yellow")
    table.add_row("description", found["desc"],                     style="yellow")
    table.add_row("info",        Panel("\n".join(found["info"])),   style="grey39")
    table.add_row("hosts",       Panel("\n".join(hostlist)),        style="white")
    table.add_row("patterns",    Panel("\n".join(patternlist)),     style="cyan")

    console = Console()
    console.print(table)

