import click
from typing import List

from sshclick.sshc import SSH_Config
from sshclick.sshc import complete_ssh_group_names

from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.console import Console

#------------------------------------------------------------------------------
# COMMAND: group show
#------------------------------------------------------------------------------
SHORT_HELP = "Shows group details"
LONG_HELP  = """
Display/Shows details from a group

Currently WIP - command will allow some styles in outputs...
"""

# Parameters help:
#------------------------------------------------------------------------------

@click.command(name="show", short_help=SHORT_HELP, help=LONG_HELP)
@click.argument("name", shell_complete=complete_ssh_group_names)
@click.pass_context
def cmd(ctx, name):
    config: SSH_Config = ctx.obj

    if not config.check_group_by_name(name):
        print(f"Cannot show group '{name}', it is not defined in configuration!")
        ctx.exit(1)

    found_group = config.get_group_by_name(name)
    host_list: List[str] = []

    for host in found_group.hosts:
        if "hostname" in host.params:
            h_name = host.params["hostname"]
            h_port = (":" + host.params["port"]) if "port" in host.params else ""
            host_list.append(f"{host.name} ({h_name}{h_port})")
        else:
            host_list.append(host.name)

    pattern_list: List[str] = []
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

