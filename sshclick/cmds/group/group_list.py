import click
from sshclick.sshc import SSH_Config
from rich.console import Console
from rich.table import Table
from rich import box

#------------------------------------------------------------------------------
# COMMAND: group list
#------------------------------------------------------------------------------
@click.command(name="list", help="Lists all groups")
@click.pass_context
def cmd(ctx):
    config: SSH_Config = ctx.obj

    table = Table(box=box.SQUARE, style="grey35")
    table.add_column("Name", style="white")
    table.add_column("Num.Hosts", justify="right", style="bright_yellow")
    table.add_column("Desc", style="gray50")

    for group in config.groups:
        table.add_row(group.name, str(len(group.hosts)), group.desc)

    console = Console()
    console.print(table)
