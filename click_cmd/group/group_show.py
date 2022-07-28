import click
from lib.sshutils import SSH_Config
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

#------------------------------------------------------------------------------
# COMMAND: group show
#------------------------------------------------------------------------------
@click.command(name="show", help="Shows group details")
# @click.argument("name", shell_complete=complete_ssh_group_names)
@click.argument("name")
@click.pass_context
def cmd(ctx, name):
    config: SSH_Config = ctx.obj['CONFIG']

    found_group = config.find_group_by_name(name, throw_on_fail=False)
    if not found_group:
        print(f"Cannot show group '{name}', it is not defined in configuration!")
        ctx.exit(1)

    hostlist = []
    for host in found_group.hosts:
        if "hostname" in host.params:
            h_name = host.params["hostname"]
            h_port = (":" + host.params["port"]) if "port" in host.params else ""
            hostlist.append(f"{host.name} ({h_name}{h_port})")
        else:
            hostlist.append(host.name)

    patternlist = []
    for host in found_group.patterns:
        # hack to search via case insensitive info
        if "hostname" in host.params:
            h_name = host.params["hostname"]
            patternlist.append(f"{host.name} ({h_name})")
        else:
            patternlist.append(host.name)


    # New rich formating
    table = Table(box=box.SQUARE, style="grey39")
    table.add_column("Group Parameter", no_wrap=True)
    table.add_column("Value")

    table.add_row("name",        found_group.name,                   style="yellow")
    table.add_row("description", found_group.desc,                   style="yellow")
    table.add_row("info",        Panel("\n".join(found_group.info)), style="grey39")
    table.add_row("hosts",       Panel("\n".join(hostlist)),         style="white")
    table.add_row("patterns",    Panel("\n".join(patternlist)),      style="cyan")

    console = Console()
    console.print(table)

