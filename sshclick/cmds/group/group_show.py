import click
from sshclick.sshc import SSH_Config, complete_ssh_group_names

from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.console import Console

#------------------------------------------------------------------------------
# COMMAND: group show
#------------------------------------------------------------------------------
@click.command(name="show", help="Shows group details")
@click.argument("name", shell_complete=complete_ssh_group_names)
@click.pass_context
def cmd(ctx, name):
    config: SSH_Config = ctx.obj

    found_group = config.find_group_by_name(name, throw_on_fail=False)
    if not found_group:
        print(f"Cannot show group '{name}', it is not defined in configuration!")
        ctx.exit(1)

    host_list = []
    for host in found_group.hosts:
        if "hostname" in host.params:
            h_name = host.params["hostname"]
            h_port = (":" + host.params["port"]) if "port" in host.params else ""
            host_list.append(f"{host.name} ({h_name}{h_port})")
        else:
            host_list.append(host.name)

    pattern_list = []
    for host in found_group.patterns:
        # hack to search via case insensitive info
        if "hostname" in host.params:
            h_name = host.params["hostname"]
            pattern_list.append(f"{host.name} ({h_name})")
        else:
            pattern_list.append(host.name)


    # New rich formatting
    table = Table(box=box.SQUARE, style="grey35")
    table.add_column("Group Parameter", no_wrap=True)
    table.add_column("Value")

    table.add_row("name",        found_group.name,                   style="white")
    table.add_row("description", found_group.desc,                   style="grey50")
    table.add_row("info",        Panel("\n".join(found_group.info)), style="grey50")
    table.add_row("hosts",       Panel("\n".join(host_list)),         style="white")
    table.add_row("patterns",    Panel("\n".join(pattern_list)),      style="cyan")

    console = Console()
    console.print(table)

