import click
from sshclick.sshc import SSH_Config
from rich.console import Console
from rich.table import Table
from rich import box

#------------------------------------------------------------------------------
# COMMAND: group list
#------------------------------------------------------------------------------
SHORT_HELP = "Lists all groups"
LONG_HELP  = SHORT_HELP

# Parameters help:
#------------------------------------------------------------------------------

@click.command(name="list", short_help=SHORT_HELP, help=LONG_HELP)
@click.pass_context
def cmd(ctx):
    config: SSH_Config = ctx.obj

    table = Table(box=box.SQUARE, style="grey35")
    table.add_column("Name", style="white")
    table.add_column("Num.Hosts", justify="right", style="bright_yellow")
    table.add_column("Desc", style="grey50")

    for group in config.groups:
        table.add_row(group.name, str(len(group.hosts)), group.desc)

    console = Console()
    console.print(table)
